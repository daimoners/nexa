# nexa/backends/nextflow.py
"""
Nextflow backend: generates a Nextflow DSL2 script from the concrete workflow
and executes it. Returns a WorkflowResult after execution.
"""
import subprocess
import json
from pathlib import Path
from textwrap import dedent
from typing import Dict, Any
from .base import BaseBackend, ModuleResult, WorkflowResult
from ..core.workflow import Workflow


class NextflowBackend(BaseBackend):
    """Backend that generates a Nextflow DSL2 script and executes it."""

    def execute(self, workflow: Workflow, parameters: Dict[str, Any] = None) -> WorkflowResult:
        nf_script = self._generate_nextflow(workflow, parameters)
        nf_path = self.workdir / "main.nf"
        nf_path.write_text(nf_script)

        cmd = ["nextflow", "run", str(nf_path)]
        if parameters:
            param_file = self.workdir / "params.json"
            param_file.write_text(json.dumps(parameters, indent=2))
            cmd += ["-params-file", str(param_file)]

        print(f"Running Nextflow: {' '.join(cmd)}")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            raise RuntimeError("nextflow not found on PATH")

        ok = proc.returncode == 0
        if ok:
            print("Nextflow workflow completed successfully.")
        else:
            print(f"Nextflow workflow failed (rc={proc.returncode}).")

        # Build per-module results from the outputs/ tree (best effort)
        module_results: Dict[str, ModuleResult] = {}
        outputs_dir = self.workdir / "outputs"
        for mod in workflow.modules:
            out_dir = outputs_dir / mod.id
            outputs = {port: str(out_dir / f"{port}.json") for port in mod.output_ports}
            all_present = all(Path(p).exists() for p in outputs.values())
            module_results[mod.id] = ModuleResult(
                module_id=mod.id,
                status="success" if all_present else ("failed" if not ok else "unknown"),
                outputs=outputs,
                returncode=proc.returncode if not all_present else 0,
            )

        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            status="success" if ok else "failed",
            modules=module_results,
            outputs_dir=outputs_dir,
            error="" if ok else proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "",
        )

    def _generate_nextflow(self, workflow: Workflow, parameters: Dict[str, Any] = None) -> str:
        process_blocks = []
        for mod in workflow.modules:
            input_ports = set()
            for conn in workflow.connections:
                if conn["to"]["module"] == mod.id:
                    input_ports.add(conn["to"]["input"])
            input_block = "\n        ".join(
                f"val({port})" for port in sorted(input_ports)
            ) or "/* no inputs */"

            output_lines = [f'path "{port}.json", emit: {port}' for port in mod.output_ports]
            output_block = "\n        ".join(output_lines) if output_lines else "/* no outputs */"

            script_path = mod.get_script_path()
            if script_path is None:
                raise ValueError(f"Module '{mod.id}' has no script defined.")
            script_cmd = f"{mod.executable} {script_path} --output_dir ."
            if parameters:
                script_cmd += " --params params.json"

            process_blocks.append(f"""
process {mod.id} {{
    input:
        {input_block}
    output:
        {output_block}
    script:
    \"\"\"
    {script_cmd}
    \"\"\"
}}
""")

        workflow_lines = []
        module_vars: Dict[str, str] = {}
        for mod_id in workflow.get_execution_order():
            mod = workflow.module_map[mod_id]
            input_args = []
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    src_var = module_vars[conn["from"]["module"]]
                    input_args.append(f"{src_var}.{conn['from']['output']}")
            input_args.sort()
            call = f"{mod_id}({', '.join(input_args)})" if input_args else f"{mod_id}()"
            result_var = f"{mod_id}_out"
            module_vars[mod_id] = result_var
            workflow_lines.append(f"    {result_var} = {call}")

        workflow_block = "workflow {\n" + "\n".join(workflow_lines) + "\n}"

        return dedent(f"""\
nextflow.enable.dsl=2

{workflow_block}

{chr(10).join(process_blocks)}
""")
