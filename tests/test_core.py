# tests/test_core.py
"""
Unit tests for nexa core components: Module, Workflow, and result dataclasses.
"""
import json
import pytest
from pathlib import Path

from nexa.core.module import Module
from nexa.core.workflow import Workflow
from nexa.backends.base import ModuleResult, WorkflowResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_module_json(tmp_path: Path, data: dict) -> Path:
    """Write a module JSON file to tmp_path and return its path."""
    path = tmp_path / f"{data['id']}.json"
    path.write_text(json.dumps(data))
    return path


def _make_workflow_json(tmp_path: Path, data: dict) -> Path:
    """Write a workflow JSON file to tmp_path and return its path."""
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# Module tests
# ---------------------------------------------------------------------------

class TestModuleInit:
    def test_defaults(self):
        m = Module(id="mod1", executable="python")
        assert m.id == "mod1"
        assert m.executable == "python"
        assert m.input_ports == []
        assert m.output_ports == []
        assert m.parameters == {}
        assert m.resources == {}
        assert m.script is None
        assert m.container is None

    def test_custom_values(self):
        m = Module(
            id="mod2",
            executable="bash",
            script="run.sh",
            input_ports=["in1"],
            output_ports=["out1"],
            parameters={"k": "v"},
            resources={"cpus": 4},
        )
        assert m.script == "run.sh"
        assert m.input_ports == ["in1"]
        assert m.output_ports == ["out1"]
        assert m.parameters == {"k": "v"}
        assert m.resources == {"cpus": 4}


class TestModuleLoad:
    def test_load_minimal(self, tmp_path):
        data = {"id": "mod1", "executable": "python"}
        path = _make_module_json(tmp_path, data)
        m = Module.load(path)
        assert m.id == "mod1"
        assert m.executable == "python"
        assert m.base_path == tmp_path

    def test_load_full(self, tmp_path):
        data = {
            "id": "mod_full",
            "executable": "bash",
            "script": "run.sh",
            "input_ports": ["a", "b"],
            "output_ports": ["c"],
            "parameters": {"x": 1},
            "resources": {"cpus": 2},
        }
        path = _make_module_json(tmp_path, data)
        m = Module.load(path)
        assert m.script == "run.sh"
        assert m.input_ports == ["a", "b"]
        assert m.output_ports == ["c"]
        assert m.parameters == {"x": 1}
        assert m.resources == {"cpus": 2}

    def test_load_defaults_for_missing_fields(self, tmp_path):
        data = {"id": "mod_min", "executable": "python"}
        path = _make_module_json(tmp_path, data)
        m = Module.load(path)
        assert m.input_ports == []
        assert m.output_ports == []
        assert m.parameters == {}
        assert m.resources == {}


class TestModuleGetScriptPath:
    def test_no_script_returns_none(self):
        m = Module(id="m", executable="python")
        assert m.get_script_path() is None

    def test_existing_script(self, tmp_path):
        script = tmp_path / "run.py"
        script.write_text("print('hello')")
        m = Module(id="m", executable="python", script="run.py", base_path=tmp_path)
        assert m.get_script_path() == script.resolve()

    def test_missing_script_raises(self, tmp_path):
        m = Module(id="m", executable="python", script="missing.py", base_path=tmp_path)
        with pytest.raises(FileNotFoundError):
            m.get_script_path()


class TestModuleToDict:
    def test_to_dict_keys(self):
        m = Module(id="m1", executable="python", script="s.py")
        d = m.to_dict()
        assert set(d.keys()) == {
            "id", "executable", "script", "container",
            "input_ports", "output_ports", "parameters", "resources",
        }
        assert d["id"] == "m1"
        assert d["script"] == "s.py"


# ---------------------------------------------------------------------------
# Workflow tests
# ---------------------------------------------------------------------------

def _build_workflow_with_modules(tmp_path: Path, n_modules: int = 2):
    """Create n simple module JSON files and a workflow referencing them."""
    module_files = []
    module_refs = []
    for i in range(n_modules):
        data = {"id": f"mod{i}", "executable": "python"}
        path = _make_module_json(tmp_path, data)
        module_files.append(path)
        module_refs.append({"ref": path.name})
    return module_refs, module_files


class TestWorkflowInit:
    def test_basic(self, tmp_path):
        module_refs, _ = _build_workflow_with_modules(tmp_path, 2)
        wf_data = {
            "workflow_id": "wf1",
            "modules": module_refs,
            "connections": [],
        }
        wf = Workflow(wf_data, base_dir=tmp_path)
        assert wf.workflow_id == "wf1"
        assert len(wf.modules) == 2
        assert "mod0" in wf.module_map
        assert "mod1" in wf.module_map

    def test_from_file(self, tmp_path):
        module_refs, _ = _build_workflow_with_modules(tmp_path, 1)
        wf_data = {"workflow_id": "wf_file", "modules": module_refs, "connections": []}
        wf_path = _make_workflow_json(tmp_path, wf_data)
        wf = Workflow.from_file(wf_path)
        assert wf.workflow_id == "wf_file"
        assert len(wf.modules) == 1

    def test_default_workflow_id(self, tmp_path):
        wf = Workflow({}, base_dir=tmp_path)
        assert wf.workflow_id == "unnamed"


class TestWorkflowExecutionOrder:
    def test_no_connections_any_order(self, tmp_path):
        module_refs, _ = _build_workflow_with_modules(tmp_path, 3)
        wf_data = {"modules": module_refs, "connections": []}
        wf = Workflow(wf_data, base_dir=tmp_path)
        order = wf.get_execution_order()
        assert set(order) == {"mod0", "mod1", "mod2"}

    def test_linear_chain(self, tmp_path):
        module_refs, _ = _build_workflow_with_modules(tmp_path, 3)
        wf_data = {
            "modules": module_refs,
            "connections": [
                {"from": {"module": "mod0", "port": "out"}, "to": {"module": "mod1", "port": "in"}},
                {"from": {"module": "mod1", "port": "out"}, "to": {"module": "mod2", "port": "in"}},
            ],
        }
        wf = Workflow(wf_data, base_dir=tmp_path)
        order = wf.get_execution_order()
        assert order.index("mod0") < order.index("mod1")
        assert order.index("mod1") < order.index("mod2")

    def test_cycle_raises(self, tmp_path):
        module_refs, _ = _build_workflow_with_modules(tmp_path, 2)
        wf_data = {
            "modules": module_refs,
            "connections": [
                {"from": {"module": "mod0", "port": "out"}, "to": {"module": "mod1", "port": "in"}},
                {"from": {"module": "mod1", "port": "out"}, "to": {"module": "mod0", "port": "in"}},
            ],
        }
        wf = Workflow(wf_data, base_dir=tmp_path)
        with pytest.raises(ValueError, match="cycle"):
            wf.get_execution_order()


# ---------------------------------------------------------------------------
# ModuleResult and WorkflowResult tests
# ---------------------------------------------------------------------------

class TestModuleResult:
    def test_defaults(self):
        r = ModuleResult(module_id="m1", status="success")
        assert r.module_id == "m1"
        assert r.status == "success"
        assert r.outputs == {}
        assert r.returncode is None
        assert r.error == ""

    def test_to_dict(self):
        r = ModuleResult(module_id="m1", status="failed", returncode=1, error="oops")
        d = r.to_dict()
        assert d["module_id"] == "m1"
        assert d["status"] == "failed"
        assert d["returncode"] == 1
        assert d["error"] == "oops"


class TestWorkflowResult:
    def test_defaults(self):
        wr = WorkflowResult(workflow_id="wf1", status="success")
        assert wr.workflow_id == "wf1"
        assert wr.modules == {}
        assert wr.outputs_dir is None

    def test_to_dict_with_module(self):
        mr = ModuleResult(module_id="m1", status="success")
        wr = WorkflowResult(workflow_id="wf1", status="success", modules={"m1": mr})
        d = wr.to_dict()
        assert d["workflow_id"] == "wf1"
        assert "m1" in d["modules"]

    def test_to_dict_outputs_dir_none(self):
        wr = WorkflowResult(workflow_id="wf1", status="success")
        assert wr.to_dict()["outputs_dir"] is None

    def test_to_dict_outputs_dir_set(self, tmp_path):
        wr = WorkflowResult(workflow_id="wf1", status="success", outputs_dir=tmp_path)
        assert wr.to_dict()["outputs_dir"] == str(tmp_path)
