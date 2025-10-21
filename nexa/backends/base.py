# workflow_executor/backends/base.py
"""
Abstract base class for execution backends.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from ..core.workflow import Workflow


class BaseBackend(ABC):
    """Abstract base class for workflow execution backends."""

    def __init__(self, workdir: Path = None):
        self.workdir = workdir or Path("workdir")
        self.workdir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def execute(self, workflow: Workflow, parameters: dict = None):
        """
        Execute the given workflow with optional parameters.
        """
        pass
