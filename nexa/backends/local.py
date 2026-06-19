# nexa/backends/local.py
"""
Local execution backend using subprocess.

Independent modules (no dependency between them) are run in parallel via a
thread pool — each topological level executes concurrently. This maps to the
natural parallelism of the module DAG without requiring a cluster.
"""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseBackend, ModuleResult, WorkflowResult
from ..core.workflow import Workflow


class LocalBackend(BaseBackend):
    """Execute workflow modules locally via subprocess, in parallel where possible."""

    def __init__(self, workdir: Path = None, on_event=None, parallel: bool = True):
        super().__init__(workdir, on_event)
        self.outputs_dir = self.workdir / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)
        self.parallel = parallel

    def _get_output_path(self, module_id: str, port: str) -> Path:
        return self.outputs_dir / module_id / port

    def _run_module(self, module, inputs: Dict[str, Path], params: Dict[str, Any]) -> ModuleResult:
        """Run a single module as a subprocess; return a ModuleResult."""
        script_path = module.get_script_path()
        if script_path is None:
            return ModuleResult(module_id=module.id, status="failed", error="No script defined")

        cmd: List[str] = [module.executable, str(script_path)]

        for port, path in inputs.items():
            cmd.extend(["--input", port, str(path)])

        if params:
            param_file = self.workdir / f"{module.id}_params.json"
            with open(param_file, "w") as f:
                json.dump(params, f)
            cmd.extend(["--params", str(param_file)])

        out_dir = self.outputs_dir / module.id
        out_dir.mkdir(exist_ok=True)
        cmd.extend(["--output_dir", str(out_dir)])

        self._emit("module_start", module.id, {"cmd": " ".join(str(c) for c in cmd)})
        print(f"Running: {' '.join(str(c) for c in cmd)}")

        proc = subprocess.run(cmd, capture_output=True, text=True)
        outputs = {port: str(out_dir / port) for port in module.output_ports}

        if proc.returncode != 0:
            err = proc.stderr.strip()
            self._emit("module_failed", module.id, {"error": err, "returncode": proc.returncode})
            return ModuleResult(
                module_id=module.id, status="failed",
                returncode=proc.returncode, error=err,
                stdout=proc.stdout, stderr=proc.stderr,
                outputs=outputs,
            )

        print(f"Module {module.id} completed.")
        self._emit("module_complete", module.id, {"outputs": outputs})
        return ModuleResult(
            module_id=module.id, status="success",
            returncode=0, outputs=outputs,
            stdout=proc.stdout, stderr=proc.stderr,
        )

    def _parallel_levels(self, workflow: Workflow) -> List[List[str]]:
        """Group module IDs into topological levels respecting DAG dependencies.

        All modules in the same level have no inter-dependency and can run
        concurrently. Levels are ordered so each level's modules depend only on
        modules in earlier levels.
        """
        deps: Dict[str, set] = {m.id: set() for m in workflow.modules}
        for conn in workflow.connections:
            deps[conn["to"]["module"]].add(conn["from"]["module"])

        remaining = set(deps)
        done: set = set()
        levels: List[List[str]] = []

        while remaining:
            level = [m for m in remaining if deps[m].issubset(done)]
            if not level:
                break
            levels.append(level)
            done.update(level)
            remaining -= set(level)

        return levels

    def _collect_inputs(self, workflow: Workflow, mod_id: str) -> Dict[str, Path]:
        inputs: Dict[str, Path] = {}
        for conn in workflow.connections:
            if conn["to"]["module"] == mod_id:
                inputs[conn["to"]["input"]] = self._get_output_path(
                    conn["from"]["module"], conn["from"]["output"]
                )
        return inputs

    def _merge_params(self, module, parameters: Optional[dict]) -> dict:
        mod_params = dict(module.parameters)
        if parameters:
            for k, v in parameters.items():
                if k in mod_params:
                    mod_params[k] = v
        return mod_params

    def _skip_remaining(self, workflow: Workflow, done: Dict[str, ModuleResult], reason: str):
        for mid in workflow.module_map:
            if mid not in done:
                done[mid] = ModuleResult(module_id=mid, status="skipped", error=reason)

    def execute(self, workflow: Workflow, parameters: dict = None) -> WorkflowResult:
        module_results: Dict[str, ModuleResult] = {}

        if self.parallel:
            levels = self._parallel_levels(workflow)
        else:
            levels = [[mid] for mid in workflow.get_execution_order()]

        print(f"Execution levels: {levels}")

        for level in levels:
            if len(level) == 1:
                # Single module — run directly, no thread overhead
                mod_id = level[0]
                module = workflow.module_map[mod_id]
                result = self._run_module(
                    module,
                    self._collect_inputs(workflow, mod_id),
                    self._merge_params(module, parameters),
                )
                module_results[mod_id] = result
                if result.status == "failed":
                    self._skip_remaining(workflow, module_results,
                                         f"Upstream module {mod_id} failed")
                    return WorkflowResult(
                        workflow_id=workflow.workflow_id, status="failed",
                        modules=module_results, outputs_dir=self.outputs_dir,
                        error=f"Module {mod_id} failed: {result.error}",
                    )
            else:
                # Parallel level — run all modules concurrently
                with ThreadPoolExecutor(max_workers=len(level)) as pool:
                    futures = {
                        pool.submit(
                            self._run_module,
                            workflow.module_map[mid],
                            self._collect_inputs(workflow, mid),
                            self._merge_params(workflow.module_map[mid], parameters),
                        ): mid
                        for mid in level
                    }
                    level_failed = False
                    for fut in as_completed(futures):
                        mid = futures[fut]
                        result = fut.result()
                        module_results[mid] = result
                        if result.status == "failed":
                            level_failed = True

                if level_failed:
                    failed = [mid for mid, r in module_results.items() if r.status == "failed"]
                    self._skip_remaining(workflow, module_results,
                                         f"Modules in level failed: {failed}")
                    return WorkflowResult(
                        workflow_id=workflow.workflow_id, status="failed",
                        modules=module_results, outputs_dir=self.outputs_dir,
                        error=f"Modules failed: {failed}",
                    )

        return WorkflowResult(
            workflow_id=workflow.workflow_id, status="success",
            modules=module_results, outputs_dir=self.outputs_dir,
        )
