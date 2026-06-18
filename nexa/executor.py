# nexa/executor.py
"""
Unified workflow executor: routes to the appropriate backend and returns a
structured WorkflowResult. Callers can optionally register a per-module event
callback to receive real-time status updates without parsing stdout.
"""
import json
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from .core.workflow import Workflow
from .backends.local import LocalBackend
from .backends.nextflow import NextflowBackend
from .backends.remote import RemoteBackend
from .backends.base import WorkflowResult


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

    def run(
        self,
        backend: str = "local",
        workdir: str = None,
        remotehost: str = None,
        config_file: str = None,
        on_module_event: Optional[Callable[[str, str, Dict[str, Any]], None]] = None,
    ) -> WorkflowResult:
        """Execute the workflow and return a WorkflowResult.

        Parameters
        ----------
        backend : str
            Execution backend: "local" | "nextflow" | "remote".
        workdir : str, optional
            Working directory for outputs and temporary files.
        remotehost : str, optional
            SSH host for remote backend (e.g. "user@hpc.example.org").
        config_file : str, optional
            Path to nexa_config.json with SLURM / remote parameters.
        on_module_event : callable, optional
            Callback ``fn(event_type, module_id, data)`` fired at:
            - "module_start"    when a module begins execution
            - "module_complete" when a module finishes successfully
            - "module_failed"   when a module fails
        """
        if backend not in self.BACKENDS:
            raise ValueError(
                f"Unsupported backend '{backend}'. "
                f"Choose from: {list(self.BACKENDS)}"
            )

        backend_cls = self.BACKENDS[backend]
        workdir_path = Path(workdir) if workdir else None

        if backend == "remote":
            if not remotehost:
                raise ValueError("--remotehost is required for remote backend")
            runner = backend_cls(
                workdir=workdir_path,
                remotehost=remotehost,
                config_file=config_file,
                on_event=on_module_event,
            )
        elif backend == "local":
            runner = backend_cls(workdir=workdir_path, on_event=on_module_event)
        else:
            runner = backend_cls(workdir=workdir_path)

        result = runner.execute(self.workflow, self.parameters)

        if self.workflow_file:
            abs_workflow = Path(self.workflow_file).resolve()
            print("\n  Want to visualize this workflow?")
            print(f"   Run: nexa-viz {abs_workflow}")
            print("   Then open http://localhost:5173 in your browser"
                  " (use SSH tunnel if remote).")

        return result
