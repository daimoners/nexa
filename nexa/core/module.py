# nexa/core/module.py
"""
Module model: represents an external computational module defined by a JSON file.
Handles resolution of script paths relative to the module definition file.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class Module:
    """
    Represents an external module (script, executable, container).
    Loaded from a JSON definition file.
    """

    def __init__(
        self,
        id: str,
        executable: str,
        script: str = None,
        container: str = None,
        input_ports: List[str] = None,
        output_ports: List[str] = None,
        parameters: Dict[str, Any] = None,
        base_path: Path = None,
    ):
        """
        Initialize a module.

        Parameters
        ----------
        id : str
            Unique identifier of the module.
        executable : str
            Command to execute (e.g., 'python', 'bash', './run.sh').
        script : str, optional
            Path to the script, relative to base_path.
        container : str, optional
            Container image (future use).
        input_ports : list of str
            List of expected input port names.
        output_ports : list of str
            List of output port names (will become filenames: <port>.json).
        parameters : dict
            Default parameters for this module.
        base_path : Path
            Directory containing the module definition JSON file.
        """
        self.id = id
        self.executable = executable
        self.script = script
        self.container = container
        self.input_ports = input_ports or []
        self.output_ports = output_ports or []
        self.parameters = parameters or {}
        self.base_path = base_path or Path(".")

    @classmethod
    def load(cls, filepath: Path) -> "Module":
        """
        Load a module from a JSON file.

        The base_path is set to the directory of the JSON file,
        enabling correct resolution of relative script paths.
        """
        with open(filepath) as f:
            data = json.load(f)
        return cls(
            id=data["id"],
            executable=data.get("executable", "python"),
            script=data.get("script"),
            container=data.get("container"),
            input_ports=data.get("input_ports", []),
            output_ports=data.get("output_ports", []),
            parameters=data.get("parameters", {}),
            base_path=filepath.parent,
        )

    def get_script_path(self) -> Optional[Path]:
        """
        Return the absolute path to the script file.

        Raises
        ------
        FileNotFoundError
            If the script file does not exist.
        """
        if self.script is None:
            return None
        script_path = (self.base_path / self.script).resolve()
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        return script_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert module to dictionary (for debugging)."""
        return {
            "id": self.id,
            "executable": self.executable,
            "script": self.script,
            "container": self.container,
            "input_ports": self.input_ports,
            "output_ports": self.output_ports,
            "parameters": self.parameters,
        }
