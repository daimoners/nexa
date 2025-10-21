# workflow_executor/executor.py
"""
Unified workflow executor supporting multiple backends.
"""
import json
from pathlib import Path
from typing import Dict, Any
from .core.workflow import Workflow
from .backends.local import LocalBackend
from .backends.nextflow import NextflowBackend
from .backends.remote import RemoteBackend


class UnifiedExecutor:
    """Unified interface to execute workflows with different backends."""

    BACKENDS = {
        "local": LocalBackend,
        "nextflow": NextflowBackend,
        "remote": RemoteBackend,
    }

    def __init__(self, workflow_file: str, simulation_file: str = None):
        self.workflow_file = Path(workflow_file)
        self.simulation_file = Path(simulation_file) if simulation_file else None

        self.workflow = Workflow.from_file(self.workflow_file)
        self.parameters = self._load_parameters()

    def _load_parameters(self) -> Dict[str, Any]:
        if not self.simulation_file or not self.simulation_file.exists():
            return {}
        with open(self.simulation_file) as f:
            sim = json.load(f)
        return sim.get("parameters", {})

    def run(self, backend: str = "local", workdir: str = None):
        if backend not in self.BACKENDS:
            raise ValueError(f"Unsupported backend: {backend}")

        backend_cls = self.BACKENDS[backend]
        runner = backend_cls(workdir=Path(workdir) if workdir else None)
        runner.execute(self.workflow, self.parameters)

        if self.workflow_file:
            abs_workflow = Path(self.workflow_file).resolve()
            print("\n  Want to visualize this workflow?")
            print(f"   Run: nexa-viz {abs_workflow}")
            print("   Then open http://localhost:5173 in your browser (use SSH tunnel if remote).")
