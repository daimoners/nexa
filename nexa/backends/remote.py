# nexa/backends/remote.py
"""
Remote execution backend using SLURM for HPC clusters.

All modules are submitted to SLURM upfront. Each module gets a
`--dependency=afterok:<dep_ids>` directive based on its specific upstream
modules, so SLURM itself manages the DAG — independent modules (same
topological level) run in parallel, dependent modules start automatically once
their dependencies complete.

Per-module resource overrides: each module can declare `resources` in its
module.json to request a different partition/memory/time than the global config.
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from .base import BaseBackend, ModuleResult, WorkflowResult
from ..core.workflow import Workflow


class RemoteBackend(BaseBackend):
    """Remote execution via SSH + SLURM, DAG-aware parallel submission."""

    def __init__(self, workdir: Path = None, remotehost: str = None,
                 config_file: str = None, on_event=None):
        super().__init__(workdir, on_event)

        self.remotehost = remotehost
        self.config = self._load_config(config_file)

        slurm = self.config.get("slurm", {})
        self._default_partition = slurm.get("partition", "default")
        self._default_nodes     = slurm.get("nodes", 1)
        self._default_ntasks    = slurm.get("ntasks", 1)
        self._default_time      = slurm.get("time", "01:00:00")
        self._default_mem       = slurm.get("mem", "4G")
        self._slurm_modules     = slurm.get("modules", [])

        remote_cfg = self.config.get("remote", {})
        self.remote_workdir      = remote_cfg.get(
            "remote_workdir", f"/tmp/nexa_run_{int(time.time())}"
        )
        self.remote_username     = remote_cfg.get("username", "")
        self.remote_private_key  = remote_cfg.get("private_key", None)

        exec_cfg = self.config.get("execution", {})
        self._poll_interval = exec_cfg.get("poll_interval", 5)
        self._max_wait      = exec_cfg.get("max_wait_time", 3600)

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

    # ── SSH / SCP helpers ────────────────────────────────────────────────────

    def _ssh(self, cmd: str) -> tuple:
        if not self.remotehost:
            raise ValueError("remotehost not specified for remote backend")
        result = subprocess.run(
            f"ssh {self.remotehost} '{cmd}'", shell=True,
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def _scp_to_remote(self, local: Path, remote_path: str) -> None:
        result = subprocess.run(
            f"scp {local} {self.remotehost}:{remote_path}",
            shell=True, capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"scp failed: {result.stderr}")

    def _rsync_from_remote(self, remote_dir: str, local_dir: Path) -> None:
        local_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            f"rsync -avz {self.remotehost}:{remote_dir}/ {local_dir}/",
            shell=True, capture_output=True, text=True,
        )

    # ── per-module resource resolution ───────────────────────────────────────

    def _res(self, module, key: str, default):
        return module.resources.get(key, default)

    # ── SLURM script + submission ─────────────────────────────────────────────

    def _slurm_script(self, module, script_path: str, inputs: dict,
                      params_remote: Optional[str],
                      dependency_ids: List[str]) -> str:
        partition  = self._res(module, "partition", self._default_partition)
        nodes      = self._res(module, "nodes",     self._default_nodes)
        ntasks     = self._res(module, "cpus", self._res(module, "ntasks", self._default_ntasks))
        time_limit = self._res(module, "time",      self._default_time)
        mem        = self._res(module, "mem", self._res(module, "memory", self._default_mem))

        dep_line = (
            f"#SBATCH --dependency=afterok:{':'.join(dependency_ids)}\n"
            if dependency_ids else ""
        )
        module_loads = "\n".join(f"module load {m}" for m in self._slurm_modules)
        output_dir   = f"{self.remote_workdir}/outputs/{module.id}"
        input_args   = "".join(f"--input {port} {path} " for port, path in inputs.items())
        params_arg   = f"--params {params_remote}" if params_remote else ""

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
            f"{dep_line}"
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

    def _submit_module(self, module, script_path: str, inputs: dict,
                       params: dict, dependency_ids: List[str]) -> str:
        """Materialise and submit one SLURM job. Returns SLURM job id."""
        params_remote = None
        if params:
            local_pf = self.workdir / f"{module.id}_params.json"
            local_pf.write_text(json.dumps(params))
            remote_pf = f"{self.remote_workdir}/{module.id}_params.json"
            self._scp_to_remote(local_pf, remote_pf)
            params_remote = remote_pf

        script_content = self._slurm_script(
            module, script_path, inputs, params_remote, dependency_ids
        )
        local_sh = self.workdir / f"submit_{module.id}.sh"
        local_sh.write_text(script_content)
        self._scp_to_remote(local_sh, f"{self.remote_workdir}/")

        rc, stdout, stderr = self._ssh(
            f"cd {self.remote_workdir} && sbatch submit_{module.id}.sh"
        )
        if rc != 0:
            raise RuntimeError(f"sbatch failed for {module.id}: {stderr}")

        job_id = stdout.strip().split()[-1]
        dep_str = f" after {dependency_ids}" if dependency_ids else " (no deps)"
        print(f"[REMOTE] {module.id}: submitted job {job_id}{dep_str} "
              f"(partition={self._res(module, 'partition', self._default_partition)}, "
              f"mem={self._res(module, 'mem', self._default_mem)})")
        return job_id

    # ── polling ───────────────────────────────────────────────────────────────

    def _poll_all(self, pending: Dict[str, str]) -> Dict[str, bool]:
        """Poll all jobs until done. Returns {mod_id: succeeded}."""
        results: Dict[str, bool] = {}
        start = time.time()

        while pending and time.time() - start < self._max_wait:
            for mod_id in list(pending):
                job_id = pending[mod_id]
                rc, stdout, _ = self._ssh(f"squeue -j {job_id} -h")
                if rc == 0 and not stdout.strip():
                    # Job left the queue — check final state
                    _, state_out, _ = self._ssh(
                        f"sacct -j {job_id} --format=State --noheader"
                    )
                    state = state_out.strip()
                    succeeded = "COMPLETED" in state
                    status_str = "COMPLETED" if succeeded else f"FAILED ({state})"
                    print(f"[REMOTE] {mod_id}: job {job_id} {status_str}")
                    results[mod_id] = succeeded
                    del pending[mod_id]

            if pending:
                print(f"[REMOTE] waiting for {list(pending)} …")
                time.sleep(self._poll_interval)

        # Anything still pending after timeout → failed
        for mod_id in pending:
            print(f"[REMOTE] {mod_id}: TIMEOUT")
            results[mod_id] = False

        return results

    # ── execute ───────────────────────────────────────────────────────────────

    def execute(self, workflow: Workflow, parameters: dict = None) -> WorkflowResult:
        print(f"\n[REMOTE] Executing '{workflow.workflow_id}' on {self.remotehost}")

        rc, _, err = self._ssh(f"mkdir -p {self.remote_workdir}/outputs")
        if rc != 0:
            raise RuntimeError(f"Failed to create remote directory: {err}")

        # Build dependency map: mod_id -> list of mod_ids it depends on
        dep_mods: Dict[str, List[str]] = {m.id: [] for m in workflow.modules}
        for conn in workflow.connections:
            dep_mods[conn["to"]["module"]].append(conn["from"]["module"])

        # Submit all modules upfront in topological order, using SLURM
        # --dependency=afterok to encode the DAG. Independent modules (same
        # topological level) are submitted without waiting and run in parallel.
        order = workflow.get_execution_order()
        submitted: Dict[str, str] = {}   # mod_id -> slurm_job_id
        submit_errors: Dict[str, str] = {}

        print(f"[REMOTE] Submitting {len(order)} jobs …")
        for mod_id in order:
            module = workflow.module_map[mod_id]

            inputs = {
                conn["to"]["input"]: (
                    f"{self.remote_workdir}/outputs/"
                    f"{conn['from']['module']}/{conn['from']['output']}"
                )
                for conn in workflow.connections
                if conn["to"]["module"] == mod_id
            }

            mod_params = dict(module.parameters)
            if parameters:
                for k, v in parameters.items():
                    if k in mod_params:
                        mod_params[k] = v

            script_path = module.get_script_path()
            if script_path is None:
                submit_errors[mod_id] = "No script defined"
                continue

            # Translate upstream mod_ids to SLURM job ids for the dependency flag
            dep_ids = [submitted[d] for d in dep_mods[mod_id] if d in submitted]

            self._emit("module_start", mod_id, {})
            try:
                job_id = self._submit_module(
                    module, str(script_path), inputs, mod_params, dep_ids
                )
                submitted[mod_id] = job_id
            except Exception as exc:
                submit_errors[mod_id] = str(exc)
                print(f"[REMOTE] Error submitting {mod_id}: {exc}")

        # Poll all submitted jobs concurrently (one SSH loop, not one per module)
        print(f"[REMOTE] All jobs submitted. Polling for completion …")
        job_outcomes = self._poll_all(dict(submitted))  # mod_id -> bool

        # Sync results + build WorkflowResult
        print(f"[REMOTE] Syncing outputs from {self.remotehost} …")
        module_results: Dict[str, ModuleResult] = {}

        for mod_id in order:
            if mod_id in submit_errors:
                module_results[mod_id] = ModuleResult(
                    module_id=mod_id, status="failed",
                    error=submit_errors[mod_id]
                )
                self._emit("module_failed", mod_id, {"error": submit_errors[mod_id]})
                continue

            succeeded = job_outcomes.get(mod_id, False)
            local_out = self.workdir / "outputs" / mod_id

            if succeeded:
                self._rsync_from_remote(
                    f"{self.remote_workdir}/outputs/{mod_id}", local_out
                )
                outputs = {
                    port: str(local_out / port)
                    for port in workflow.module_map[mod_id].output_ports
                }
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

        overall = "success" if all(r.status == "success" for r in module_results.values()) else "failed"
        failed  = [mid for mid, r in module_results.items() if r.status != "success"]

        print(f"[REMOTE] Done. Status: {overall}"
              + (f" (failed: {failed})" if failed else ""))

        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=overall,
            modules=module_results,
            outputs_dir=self.workdir / "outputs",
            error=f"Modules failed: {failed}" if failed else "",
        )
