# nexa/backends/local.py
"""
Local execution backend using subprocess.
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any
from .base import BaseBackend
from ..core.workflow import Workflow


class LocalBackend(BaseBackend):
    """Execute workflow modules locally via subprocess."""

    def __init__(self, workdir: Path = None):
        super().__init__(workdir)
        self.outputs_dir = self.workdir / "outputs"
        self.outputs_dir.mkdir(exist_ok=True)

    def _get_output_path(self, module_id: str, port: str) -> Path:
        return self.outputs_dir / module_id / f"{port}.json"

    def _run_module(self, module, inputs: Dict[str, Path], params: Dict[str, Any]):
        """Run a single module."""
        script_path = module.get_script_path()
        if script_path is None:
            raise ValueError(f"Module {module.id} has no script defined.")

        cmd = [module.executable, str(script_path)]

        # Pass input file paths as --input <port> <path>
        for port, path in inputs.items():
            cmd.extend(["--input", port, str(path)])

        # Pass parameters as JSON file
        if params:
            param_file = self.workdir / f"{module.id}_params.json"
            with open(param_file, "w") as f:
                json.dump(params, f)
            cmd.extend(["--params", str(param_file)])

        # Set output directory
        out_dir = self.outputs_dir / module.id
        out_dir.mkdir(exist_ok=True)
        cmd.extend(["--output_dir", str(out_dir)])

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Module {module.id} failed:\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        print(f"Module {module.id} completed.")

    def execute(self, workflow: Workflow, parameters: dict = None):
        order = workflow.get_execution_order()
        print(f"Execution order: {order}")

        for mod_id in order:
            module = workflow.module_map[mod_id]

            # Collect inputs from connections
            inputs = {}
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    src_mod = conn["from"]["module"]
                    src_port = conn["from"]["output"]
                    dst_port = conn["to"]["input"]
                    input_path = self._get_output_path(src_mod, src_port)
                    inputs[dst_port] = input_path

            # Merge module parameters with global simulation parameters
            mod_params = dict(module.parameters)
            if parameters:
                # Only override if key exists in module params (optional: make configurable)
                for k, v in parameters.items():
                    if k in mod_params:
                        mod_params[k] = v

            self._run_module(module, inputs, mod_params)
