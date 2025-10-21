# nexa/demo/run_demo.py
"""
Demo script to run a workflow locally using the nexa executor.
Must be run from the parent directory of nexa (i.e., ModelWave/).
But we make it work even if run from inside nexa.
"""
import sys
import os
from pathlib import Path
from nexa.utils.banner import print_banner

# Ensure 'nexa' is in sys.path when running from inside nexa/
if Path(__file__).parent.parent.name == "nexa":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nexa import UnifiedExecutor

if __name__ == "__main__":
    print_banner()
    # Resolve paths relative to this script
    demo_dir = Path(__file__).parent.resolve()
    workflow_file = demo_dir / "demo_workflow.json"

    executor = UnifiedExecutor(str(workflow_file))
    print ("Executing workflow: ", workflow_file)
    executor.run(backend="nextflow", workdir=str(demo_dir / "demo_local"))
