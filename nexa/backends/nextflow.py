# nexa/backends/nextflow.py
"""
Nextflow backend for the Nexus workflow executor.
Generates and runs a valid Nextflow DSL2 pipeline from a concrete workflow.
"""
import subprocess
import json
from pathlib import Path
from textwrap import dedent
from typing import Dict, Any
from .base import BaseBackend
from ..core.workflow import Workflow


class NextflowBackend(BaseBackend):
    """
    Backend that generates a Nextflow DSL2 script and executes it.
    """

    def execute(self, workflow: Workflow, parameters: Dict[str, Any] = None):
        """
        Generate and run a Nextflow pipeline.

        Parameters
        ----------
        workflow : Workflow
            The concrete workflow to execute.
        parameters : dict, optional
            Global parameters to pass to all modules via params.json.
        """
        nf_script = self._generate_nextflow(workflow, parameters)
        nf_path = self.workdir / "main.nf"
        with open(nf_path, "w") as f:
            f.write(nf_script)

        if parameters:
            param_file = self.workdir / "params.json"
            with open(param_file, "w") as f:
                json.dump(parameters, f, indent=2)
            cmd = ["nextflow", "run", str(nf_path), "-params-file", str(param_file)]
        else:
            cmd = ["nextflow", "run", str(nf_path)]

        print(f"Running Nextflow: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("Nextflow workflow completed successfully.")

    def _generate_nextflow(self, workflow: Workflow, parameters: Dict[str, Any] = None) -> str:
        """
        Generate a valid Nextflow DSL2 script.

        Key rules for DSL2:
        - Each process emits named outputs.
        - Workflow block assigns process results to variables.
        - Inputs are passed as `result.output_name`.
        """
        # Step 1: Generate process definitions
        process_blocks = []
        for mod in workflow.modules:
            # Input block: list of val(port_name)
            input_ports = set()
            for conn in workflow.connections:
                if conn["to"]["module"] == mod.id:
                    input_ports.add(conn["to"]["input"])
            input_block = "\n        ".join(f"val({port})" for port in sorted(input_ports)) or "/* no inputs */"

            # Output block: emit one channel per output port
            output_lines = [f'path "{port}.json", emit: {port}' for port in mod.output_ports]
            output_block = "\n        ".join(output_lines) if output_lines else '/* no outputs */'

            # Script command with absolute path
            script_path = mod.get_script_path()
            if script_path is None:
                raise ValueError(f"Module '{mod.id}' has no script defined.")
            script_cmd = f"{mod.executable} {script_path} --output_dir ."
            if parameters:
                script_cmd += " --params params.json"

            process_def = f"""
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
"""
            process_blocks.append(process_def)

        # Step 2: Build workflow block with explicit variable assignment
        workflow_lines = []
        module_vars = {}  # module_id → result variable name
        execution_order = workflow.get_execution_order()

        for mod_id in execution_order:
            mod = workflow.module_map[mod_id]

            # Collect inputs from connections
            input_args = []
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    src_mod = conn["from"]["module"]
                    src_port = conn["from"]["output"]
                    src_var = module_vars[src_mod]
                    input_args.append(f"{src_var}.{src_port}")

            # Sort to ensure consistent order (matches input block)
            input_args.sort()

            if input_args:
                call = f"{mod.id}({', '.join(input_args)})"
            else:
                call = f"{mod.id}()"

            result_var = f"{mod_id}_out"
            module_vars[mod_id] = result_var
            workflow_lines.append(f"    {result_var} = {call}")

        workflow_block = "workflow {\n" + "\n".join(workflow_lines) + "\n}"

        # Combine all parts
        return dedent(f"""\
nextflow.enable.dsl=2

{workflow_block}

{chr(10).join(process_blocks)}
""")
