# Quick Start

## Run a demo workflow

NEXA includes a demo workflow for polymer simulation.

```bash
cd nexa/demo
nexa demo_workflow.json --backend local
```

Output:

  Nextflow workflow completed successfully.

   Want to visualize this workflow?
   Run: nexa-viz /path/to/demo_workflow.json

## Visualize the workflow

nexa-viz demo_workflow.json

Then open http://localhost:5173 in your browser to see the interactive graph. 

    Remote server? Use SSH tunneling:

ssh -L 5173:localhost:5173 user@remote-host


