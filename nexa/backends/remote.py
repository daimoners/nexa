# nexa/backends/remote.py
"""
Remote execution backend using SLURM for HPC clusters.

Each module in the workflow gets its own SLURM job, submitted to a remote host
via SSH. Resources (partition, cpus, memory, time) are read first from the
module's own `resources` field in module.json, then fall back to the global
SLURM configuration in nexa_config.json. This lets compute-heavy modules (e.g.
DFT, MD) request different allocations than lightweight pre/post-processing
modules within the same simulation.

Dependency tracking: modules are submitted only after all their dependencies
have completed (COMPLETED sacct state). SSH + squeue/sacct polling.
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional
from .base import BaseBackend, ModuleResult, WorkflowResult
from ..core.workflow import Workflow


class RemoteBackend(BaseBackend):
    """Remote execution via SSH + SLURM, one sbatch per module."""

    def __init__(self, workdir: Path = None, remotehost: str = None,
                 config_file: str = None, on_event=None):
        super().__init__(workdir, on_event)

        self.remotehost = remotehost
        self.config = self._load_config(config_file)

        slurm = self.config.get("slurm", {})
        self._default_partition = slurm.get("partition", "default")
        self._default_nodes = slurm.get("nodes", 1)
        self._default_ntasks = slurm.get("ntasks", 1)
        self._default_time = slurm.get("time", "01:00:00")
        self._default_mem = slurm.get("mem", "4G")
        self._slurm_modules = slurm.get("modules", [])   # env-modules to load

        remote_cfg = self.config.get("remote", {})
        self.remote_workdir = remote_cfg.get(
            "remote_workdir", f"/tmp/nexa_run_{int(time.time())}"
        )
        self.remote_username = remote_cfg.get("username", "")
        self.remote_private_key = remote_cfg.get("private_key", None)

        exec_cfg = self.config.get("execution", {})
        self._poll_interval = exec_cfg.get("poll_interval", 5)
        self._max_wait = exec_cfg.get("max_wait_time", 3600)

        print(f"[REMOTE] Backend initialized")
        print(f"  Remote host    : {self.remotehost}")
        print(f"  Remote workdir : {self.remote_workdir}")
        print(f"  Default partition: {self._default_partition}")

    # ── config ───────────────────────────────────────────────────────────────

    def _load_config(self, config_file: Optional[str]) -> dict:
        for path in ([Path(config_file).resolve()] if config_file else []) + [Path("nexa_config.json")]:
            if Path(path).exists():
                with open(path) as f:
                    return json.load(f)
        return {}

    # ── SSH helpers ───────────────────────────────────────────────────────────

    def _ssh(self, cmd: str) -> tuple:
        """Run cmd on remotehost via SSH. Returns (returncode, stdout, stderr)."""
        if not self.remotehost:
            raise ValueError("remotehost not specified for remote backend")
        result = subprocess.run(
            f"ssh {self.remotehost} '{cmd}'", shell=True,
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def _scp_to_remote(self, local: Path, remote_path: str) -> None:
        cmd = f"scp {local} {self.remotehost}:{remote_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"scp failed: {result.stderr}")

    def _rsync_from_remote(self, remote_dir: str, local_dir: Path) -> None:
        local_dir.mkdir(parents=True, exist_ok=True)
        cmd = f"rsync -avz {self.remotehost}:{remote_dir}/ {local_dir}/"
        subprocess.run(cmd, shell=True, capture_output=True, text=True)

    # ── per-module resource resolution ───────────────────────────────────────

    def _res(self, module, key: str, default):
        """Return module-level resource override, or global default."""
        return module.resources.get(key, default)

    # ── SLURM submission ─────────────────────────────────────────────────────

    def _slurm_script(self, module, script_path: str,
                      inputs: dict, params: dict,
                      params_remote_path: Optional[str]) -> str:
        """Build a self-contained bash/SBATCH script for one module."""
        partition = self._res(module, "partition", self._default_partition)
        nodes = self._res(module, "nodes", self._default_nodes)
        ntasks = self._res(module, "cpus", self._res(module, "ntasks", self._default_ntasks))
        time_limit = self._res(module, "time", self._default_time)
        mem = self._res(module, "mem", self._res(module, "memory", self._default_mem))

        output_dir = f"{self.remote_workdir}/outputs/{module.id}"

        input_args = "".join(
            f"--input {port} {path} " for port, path in inputs.items()
        )
        params_arg = f"--params {params_remote_path}" if params_remote_path else ""

        # Optional: load environment modules
        module_loads = "\n".join(f"module load {m}" for m in self._slurm_modules)

        return (
            f"#!/bin/bash\n"
            f"#SBATCH --job-name={module.id}\n"
            f"#SBATCH --partition={partition}\n"
            f"#SBATCH --nodes={nodes}\n"
            f"#SBATCH --ntasks={ntasks}\n"
            f"#SBATCH --time={time_limit}\n"
            f"#SBATCH --mem={mem}\n"
            f"#SBATCH --output={self.remote_workdir}/{module.id}_%j.out\n"
            f"#SBATCH --error={self.remote_workdir}/{module.id}_%j.err\n"
            f"\n"
            f"{module_loads}\n"
            f"\n"
            f"mkdir -p {output_dir}\n"
            f"\n"
            f"python3 {script_path} \\\n"
            f"    {input_args} \\\n"
            f"    {params_arg} \\\n"
            f"    --output_dir {output_dir}\n"
        )

    def _submit_module(self, module, script_path: str,
                       inputs: dict, params: dict) -> str:
        """Materialise SLURM script, scp + sbatch. Returns SLURM job id."""
        # Serialise params to remote if needed
        params_remote = None
        if params:
            local_pf = self.workdir / f"{module.id}_params.json"
            local_pf.write_text(json.dumps(params))
            remote_pf = f"{self.remote_workdir}/{module.id}_params.json"
            self._scp_to_remote(local_pf, remote_pf)
            params_remote = remote_pf

        script_content = self._slurm_script(module, script_path, inputs, params, params_remote)
        local_sh = self.workdir / f"submit_{module.id}.sh"
        local_sh.write_text(script_content)

        self._scp_to_remote(local_sh, f"{self.remote_workdir}/")

        returncode, stdout, stderr = self._ssh(
            f"cd {self.remote_workdir} && sbatch submit_{module.id}.sh"
        )
        if returncode != 0:
            raise RuntimeError(f"sbatch failed for {module.id}: {stderr}")

        job_id = stdout.strip().split()[-1]
        print(f"[REMOTE] {module.id}: submitted SLURM job {job_id} "
              f"(partition={self._res(module, 'partition', self._default_partition)}, "
              f"mem={self._res(module, 'mem', self._default_mem)})")
        return job_id

    def _wait_for_job(self, job_id: str, module_id: str) -> bool:
        start = time.time()
        while time.time() - start < self._max_wait:
            rc, stdout, _ = self._ssh(f"squeue -j {job_id} -h")
            if rc == 0 and not stdout.strip():
                # Job left the queue — check final state
                _, state_out, _ = self._ssh(
                    f"sacct -j {job_id} --format=State --noheader"
                )
                state = state_out.strip()
                if "COMPLETED" in state:
                    print(f"[REMOTE] {module_id}: job {job_id} COMPLETED")
                    return True
                print(f"[REMOTE] {module_id}: job {job_id} FAILED (state={state})")
                return False
            print(f"[REMOTE] {module_id}: job {job_id} still running …")
            time.sleep(self._poll_interval)
        print(f"[REMOTE] {module_id}: job {job_id} TIMEOUT")
        return False

    # ── execute ───────────────────────────────────────────────────────────────

    def execute(self, workflow: Workflow, parameters: dict = None) -> WorkflowResult:
        print(f"\n[REMOTE] Executing '{workflow.workflow_id}' on {self.remotehost}")

        # Create remote workdir
        rc, _, err = self._ssh(f"mkdir -p {self.remote_workdir}/outputs")
        if rc != 0:
            raise RuntimeError(f"Failed to create remote directory: {err}")

        order = workflow.get_execution_order()
        print(f"[REMOTE] Execution order: {order}")

        module_results: Dict[str, ModuleResult] = {}
        completed: set = set()

        for mod_id in order:
            module = workflow.module_map[mod_id]

            # Collect inputs (remote paths from already-completed modules)
            inputs = {}
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    inputs[conn["to"]["input"]] = (
                        f"{self.remote_workdir}/outputs/"
                        f"{conn['from']['module']}/{conn['from']['output']}.json"
                    )

            # Merge parameters
            mod_params = dict(module.parameters)
            if parameters:
                for k, v in parameters.items():
                    if k in mod_params:
                        mod_params[k] = v

            script_path = module.get_script_path()
            if script_path is None:
                module_results[mod_id] = ModuleResult(
                    module_id=mod_id, status="failed", error="No script defined"
                )
                # Skip remaining
                for remaining in order:
                    if remaining not in module_results:
                        module_results[remaining] = ModuleResult(
                            module_id=remaining, status="skipped",
                            error=f"Upstream {mod_id} has no script"
                        )
                return WorkflowResult(
                    workflow_id=workflow.workflow_id, status="failed",
                    modules=module_results, error=f"Module {mod_id} has no script"
                )

            self._emit("module_start", mod_id, {})
            try:
                job_id = self._submit_module(module, str(script_path), inputs, mod_params)
                succeeded = self._wait_for_job(job_id, mod_id)
            except Exception as exc:
                succeeded = False
                print(f"[REMOTE] Error for {mod_id}: {exc}")

            outputs = {port: f"{self.remote_workdir}/outputs/{mod_id}/{port}.json"
                       for port in module.output_ports}

            if succeeded:
                completed.add(mod_id)
                module_results[mod_id] = ModuleResult(
                    module_id=mod_id, status="success",
                    returncode=0, outputs=outputs,
                )
                self._emit("module_complete", mod_id, {"outputs": outputs})
            else:
                module_results[mod_id] = ModuleResult(
                    module_id=mod_id, status="failed",
                    returncode=1, error="SLURM job failed or timed out",
                )
                self._emit("module_failed", mod_id, {})
                # Skip remaining
                for remaining in order:
                    if remaining not in module_results:
                        module_results[remaining] = ModuleResult(
                            module_id=remaining, status="skipped",
                            error=f"Upstream {mod_id} failed"
                        )
                return WorkflowResult(
                    workflow_id=workflow.workflow_id, status="failed",
                    modules=module_results, error=f"Module {mod_id} failed"
                )

        # Copy all outputs back to local workdir
        print(f"[REMOTE] Syncing outputs from {self.remotehost} …")
        for mod_id in workflow.module_map:
            self._rsync_from_remote(
                f"{self.remote_workdir}/outputs/{mod_id}",
                self.workdir / "outputs" / mod_id,
            )
            # Update output paths to local
            if mod_id in module_results and module_results[mod_id].status == "success":
                local_out = self.workdir / "outputs" / mod_id
                module_results[mod_id].outputs = {
                    port: str(local_out / f"{port}.json")
                    for port in workflow.module_map[mod_id].output_ports
                }

        print(f"[REMOTE] Workflow execution completed")
        return WorkflowResult(
            workflow_id=workflow.workflow_id, status="success",
            modules=module_results, outputs_dir=self.workdir / "outputs",
        )
