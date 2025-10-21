# workflow_executor/core/workflow.py
"""
Workflow model: loads and validates concrete workflow JSON.
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from .module import Module


class Workflow:
    """
    Represents a concrete workflow loaded from JSON.
    Contains modules and connections.
    """

    def __init__(self, data: Dict[str, Any], base_dir: Path = None):
        self.data = data
        self.base_dir = base_dir or Path(".")

        self.workflow_id: str = data.get("workflow_id", "unnamed")
        self.scale: str = data.get("scale", "")
        self.indicator: str = data.get("indicator", "")
        self.accuracy: str = data.get("accuracy", "")

        self.modules: List[Module] = []
        for mod in data.get("modules", []):
            mod_path = self.base_dir / mod["ref"]
            self.modules.append(Module.load(mod_path))

        self.connections: List[Dict] = data.get("connections", [])

        # Build module map for fast lookup
        self.module_map = {m.id: m for m in self.modules}

    @classmethod
    def from_file(cls, filepath: Path) -> "Workflow":
        """Load workflow from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return cls(data, base_dir=filepath.parent)

    def get_execution_order(self) -> List[str]:
        """
        Return module IDs in topological order using Kahn's algorithm.
        Assumes DAG.
        """
        from collections import defaultdict, deque

        in_degree = {m.id: 0 for m in self.modules}
        graph = defaultdict(list)

        for conn in self.connections:
            src = conn["from"]["module"]
            dst = conn["to"]["module"]
            graph[src].append(dst)
            in_degree[dst] += 1

        queue = deque([mod_id for mod_id, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.modules):
            raise ValueError("Workflow contains a cycle!")

        return order
