# Quick Start

## Run the demo workflow

NEXA includes a complete 5-module demo workflow simulating polymer nanoparticle creation and analysis.

```bash
# Run locally
nexa demo/demo_workflow.json --backend local
```

This executes the workflow with the following modules:
- **chain_builder**: Generate polymer chains
- **ff_builder**: Create force field parameters (runs in parallel with chain_builder)
- **nanoparticle_builder**: Assemble nanoparticle from chain + force field
- **solvation_module**: Add solvent around nanoparticle
- **leaching_evaluator**: Calculate leaching rate and annealing temperature

Output:

```
Execution order: ['chain_builder', 'ff_builder', 'nanoparticle_builder', 
'solvation_module', 'leaching_evaluator']
Running: python3 .../chain_builder.py ...
Module chain_builder completed.
...
```

Results are saved in `nexa_run/outputs/<module_name>/`.

## Visualize the workflow

```bash
nexa-viz demo/demo_workflow.json
```

Then open http://localhost:5173 in your browser to see the interactive graph with:
- Draggable nodes
- Semantic edge labels
- Mini-map navigation
- Module metadata

**Remote server?** Use SSH tunneling:

```bash
ssh -L 5173:localhost:5173 user@remote-host
```

## Run with custom parameters

Create a simulation file:

```json
{
  "workflow": "demo/demo_workflow.json",
  "parameters": {
    "chain_builder": {
      "mw": 15000.0
    },
    "solvation_module": {
      "solvent_type": "ethanol"
    }
  }
}
```

Run with parameters:

```bash
nexa demo/demo_workflow.json --simulation params.json --backend local
```

## Next Steps

- Explore [workflow concepts](concepts/workflows.md)
- Learn about [execution backends](execution/backends.md)
- Create your own [modules](concepts/modules.md)


