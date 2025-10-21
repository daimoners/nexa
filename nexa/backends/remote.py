# workflow_executor/backends/remote.py
"""
Remote execution backend (mocked).
In practice, this would submit to Slurm, SSH, etc.
"""
from .base import BaseBackend
from ..core.workflow import Workflow


class RemoteBackend(BaseBackend):
    """Mock remote backend."""

    def execute(self, workflow: Workflow, parameters: dict = None):
        print(f"[REMOTE] Would execute workflow '{workflow.workflow_id}' remotely.")
        print(f"[REMOTE] Parameters: {parameters}")
        print("[REMOTE] Execution completed (mock).")
