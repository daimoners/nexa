# Quick Start

## Run the demo workflow

NEXA includes a complete 5-module demo workflow simulating polymer nanoparticle creation and leaching analysis.

```bash
nexa demo/demo_workflow.json --backend local
```

Expected output:

```
Execution levels: [['chain_builder', 'ff_builder'], ['nanoparticle_builder'], ['solvation_module'], ['leaching_evaluator']]
Running: python3 .../chain_builder.py --output_dir .../outputs/chain_builder
Running: python3 .../ff_builder.py --output_dir .../outputs/ff_builder
Module chain_builder completed.
Module ff_builder completed.
Running: python3 .../nanoparticle_builder.py --input polymer_chain ... --input force_field ...
...
```

`chain_builder` and `ff_builder` are in the same topological level and run in parallel.

Results are saved in `nexa_run/outputs/<module_id>/`:

```
nexa_run/outputs/
  chain_builder/polymer_chain.json
  ff_builder/force_field.json
  nanoparticle_builder/nanoparticle.json
  solvation_module/solvated_system.json
  leaching_evaluator/molecular_leaching_rate.json
  leaching_evaluator/t_anneal.json
```

## Inspect results programmatically

```python
from nexa import UnifiedExecutor

result = UnifiedExecutor("demo/demo_workflow.json").run(
    backend="local",
    workdir="nexa_run",
)

print(result.status)   # "success"
for mod_id, mod in result.modules.items():
    print(f"  {mod_id}: {mod.status}  outputs={list(mod.outputs)}")
```

## Run with simulation parameters

Create a simulation file:

```json
{
  "simulation_id": "my_sim_001",
  "parameters": {
    "mw": 15000.0,
    "species": ["C(C)C"]
  }
}
```

Parameters are merged into each module's defaults: a parameter is applied to a module only if it exists in that module's `parameters` block.

```bash
nexa demo/demo_workflow.json --simulation params.json --backend local
```

## Run with event callback

```python
def on_event(event_type, module_id, data):
    if event_type == "module_start":
        print(f"  → starting {module_id}")
    elif event_type == "module_complete":
        print(f"  ✓ {module_id}")
    elif event_type == "module_failed":
        print(f"  ✗ {module_id}: {data.get('error')}")

result = UnifiedExecutor("demo/demo_workflow.json").run(
    backend="local",
    workdir="nexa_run",
    on_module_event=on_event,
)
```

## Visualize the workflow

```bash
nexa-viz demo/demo_workflow.json
```

Then open http://localhost:5173 in your browser. See [Visualization](visualization.md) for details.

## Next Steps

- Define your own [modules](concepts/modules.md)
- Compose a [workflow](concepts/workflows.md)
- Run on HPC with the [remote backend](execution/backends.md)
