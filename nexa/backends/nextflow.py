# nexa/backends/nextflow.py
"""
Nextflow DSL2 backend.

Generates a correct Nextflow pipeline where:
- Each module becomes a `process` with `path` inputs (file staging) and
  `path ... emit:` outputs — this is what makes Nextflow's dataflow scheduler
  work: processes wait for the actual files, not strings.
- Independent modules (same topological level) run in parallel automatically
  because their input channels emit immediately.
- The script block includes --input port ${var} so module scripts receive
  their input files via NEXA's standard interface.
- publishDir copies outputs to workdir/outputs/<module_id>/ so the rest of
  ModelWave can find them in the usual place.
"""
import json
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import Dict, Any, List, Tuple
from .base import BaseBackend, ModuleResult, WorkflowResult
from ..core.workflow import Workflow


class NextflowBackend(BaseBackend):
    """Backend that generates a Nextflow DSL2 script and executes it."""

    def execute(self, workflow: Workflow, parameters: Dict[str, Any] = None) -> WorkflowResult:
        nf_script = self._generate_nextflow(workflow, parameters)
        nf_path = self.workdir / "main.nf"
        nf_path.write_text(nf_script)

        cmd = ["nextflow", "run", str(nf_path.name)]
        if parameters:
            param_file = self.workdir / "params.json"
            param_file.write_text(json.dumps(parameters, indent=2))
            cmd += ["-params-file", "params.json"]

        print(f"Running Nextflow: {' '.join(cmd)}")
        print("─" * 60)
        try:
            # stdout passes through to the terminal in real time (None = inherit).
            # stderr is captured so we can include it in WorkflowResult on failure.
            proc = subprocess.run(
                cmd, stdout=None, stderr=subprocess.PIPE, text=True, check=False,
                cwd=str(self.workdir),
            )
        except FileNotFoundError:
            raise RuntimeError("nextflow not found on PATH")
        print("─" * 60)

        ok = proc.returncode == 0
        if ok:
            print("Nextflow workflow completed successfully.")
        else:
            print(f"Nextflow workflow failed (rc={proc.returncode}).")
            if proc.stderr.strip():
                print(proc.stderr.strip())

        # Build WorkflowResult from publishDir outputs
        outputs_dir = self.workdir / "outputs"
        module_results: Dict[str, ModuleResult] = {}
        for mod in workflow.modules:
            out_dir = outputs_dir / mod.id
            outputs = {port: str(out_dir / f"{port}.json") for port in mod.output_ports}
            all_present = all(Path(p).exists() for p in outputs.values())
            module_results[mod.id] = ModuleResult(
                module_id=mod.id,
                status="success" if all_present else "failed",
                outputs=outputs,
                returncode=0 if all_present else proc.returncode,
                stderr=proc.stderr if not all_present else "",
            )

        stderr = (proc.stderr or "").strip()
        return WorkflowResult(
            workflow_id=workflow.workflow_id,
            status="success" if ok else "failed",
            modules=module_results,
            outputs_dir=outputs_dir,
            error="" if ok else (stderr.splitlines()[-1] if stderr else f"exit code {proc.returncode}"),
        )

    def _generate_nextflow(self, workflow: Workflow, parameters: Dict[str, Any] = None) -> str:
        # For each module, find which of its input ports come from connections
        # (keyed by input_port → (src_module, src_port))
        connected_inputs: Dict[str, Dict[str, Tuple[str, str]]] = {
            m.id: {} for m in workflow.modules
        }
        for conn in workflow.connections:
            dst_mod   = conn["to"]["module"]
            dst_port  = conn["to"]["input"]
            src_mod   = conn["from"]["module"]
            src_port  = conn["from"]["output"]
            connected_inputs[dst_mod][dst_port] = (src_mod, src_port)

        process_blocks: List[str] = []
        for mod in workflow.modules:
            in_ports = sorted(connected_inputs[mod.id].keys())

            # path inputs — Nextflow stages the file into the work directory
            if in_ports:
                input_block = "\n        ".join(f"path {port}" for port in in_ports)
            else:
                input_block = "/* no inputs */"

            # path outputs with emit names — Nextflow tracks these as channels
            output_lines = [
                f'path "{port}.json", emit: {port}' for port in mod.output_ports
            ]
            output_block = (
                "\n        ".join(output_lines) if output_lines else "/* no outputs */"
            )

            # publishDir copies outputs to workdir/outputs/<module_id>/
            # (path is relative to the Nextflow launch dir, which = workdir)
            publish_dir = f"outputs/{mod.id}"

            script_path = mod.get_script_path()
            if script_path is None:
                raise ValueError(f"Module '{mod.id}' has no script defined.")

            # Build --input args; ${port} refers to the staged filename
            input_args = " ".join(
                f"--input {port} ${{{port}}}" for port in in_ports
            )
            params_arg = "--params params.json" if parameters else ""

            script_cmd = (
                f"{mod.executable} {script_path} "
                f"{input_args} {params_arg} --output_dir ."
            ).strip()

            process_blocks.append(dedent(f"""\
process {mod.id} {{
    publishDir "{publish_dir}", mode: 'copy'
    input:
        {input_block}
    output:
        {output_block}
    script:
    \"\"\"
    {script_cmd}
    \"\"\"
}}
"""))

        # Workflow block — pass channel outputs as arguments to dependent processes.
        # Because inputs are `path` channels, Nextflow waits for upstream
        # processes to emit before scheduling downstream ones. Independent
        # processes (no common dependency) run in parallel automatically.
        workflow_lines: List[str] = []
        module_vars: Dict[str, str] = {}

        for mod_id in workflow.get_execution_order():
            mod = workflow.module_map[mod_id]
            args: List[str] = []
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    src_var  = module_vars[conn["from"]["module"]]
                    src_port = conn["from"]["output"]
                    args.append(f"{src_var}.{src_port}")
            call = f"{mod_id}({', '.join(args)})" if args else f"{mod_id}()"
            result_var = f"{mod_id}_out"
            module_vars[mod_id] = result_var
            workflow_lines.append(f"    {result_var} = {call}")

        workflow_block = "workflow {\n" + "\n".join(workflow_lines) + "\n}"

        return dedent(f"""\
nextflow.enable.dsl=2

{workflow_block}

""") + "\n".join(process_blocks)
