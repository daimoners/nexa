# nexa/backends/base.py
"""
Abstract base class for execution backends.
Defines WorkflowResult and ModuleResult — the structured return types that all
backends must produce. Callers (ModelWave runner, tests) can inspect per-module
status without parsing stdout.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional, Any
from ..core.workflow import Workflow


@dataclass
class ModuleResult:
    """Outcome of executing one module."""
    module_id: str
    status: str             # "success" | "failed" | "skipped"
    outputs: Dict[str, str] = field(default_factory=dict)  # port -> output file path
    returncode: Optional[int] = None
    error: str = ""
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict:
        return {
            "module_id": self.module_id,
            "status": self.status,
            "outputs": self.outputs,
            "returncode": self.returncode,
            "error": self.error,
        }


@dataclass
class WorkflowResult:
    """Outcome of executing a complete workflow."""
    workflow_id: str
    status: str             # "success" | "failed"
    modules: Dict[str, ModuleResult] = field(default_factory=dict)
    outputs_dir: Optional[Path] = None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "error": self.error,
            "outputs_dir": str(self.outputs_dir) if self.outputs_dir else None,
            "modules": {mid: r.to_dict() for mid, r in self.modules.items()},
        }


# Callback signature: on_event(event_type, module_id, data)
# event_type in {"module_start", "module_complete", "module_failed"}
EventCallback = Callable[[str, str, Dict[str, Any]], None]


class BaseBackend(ABC):
    """Abstract base class for workflow execution backends."""

    def __init__(self, workdir: Path = None, on_event: EventCallback = None):
        self.workdir = workdir or Path("workdir")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._on_event: EventCallback = on_event or (lambda *_: None)

    def _emit(self, event: str, module_id: str, data: Dict[str, Any] = None) -> None:
        self._on_event(event, module_id, data or {})

    @abstractmethod
    def execute(self, workflow: Workflow, parameters: dict = None) -> WorkflowResult:
        """Execute the workflow and return a structured WorkflowResult."""
        pass
