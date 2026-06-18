# Workflows

A **workflow** in NEXA is a JSON file that defines a directed acyclic graph (DAG) of computational modules and their data dependencies.

## Workflow Structure

```json
{
  "workflow_id": "my_workflow",
  "scale": "molecular",
  "indicator": "leaching_rate",
  "accuracy": "estimated",
  "description": "Example multi-module workflow",
  "modules": [
    { "id": "module_a", "ref": "modules/module_a/module_a.json" },
    { "id": "module_b", "ref": "modules/module_b/module_b.json" }
  ],
  "connections": [
    {
      "from": { "module": "module_a", "output": "result"     },
      "to":   { "module": "module_b", "input":  "input_data" }
    }
  ]
}
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `workflow_id` | yes | Unique workflow identifier |
| `modules` | yes | List of module instances |
| `connections` | yes | Data-flow edges between modules |
| `scale` | no | Physical scale (e.g. `molecular`, `mesoscale`) |
| `indicator` | no | Target property (e.g. `leaching_rate`) |
| `accuracy` | no | Accuracy class (e.g. `estimated`, `high`) |
| `description` | no | Human-readable description |

Each entry in `modules`:
- `id` — instance identifier, unique within the workflow
- `ref` — path to the module JSON definition, **relative to the workflow file's directory**

Each entry in `connections`:
- `from.module` / `from.output` — source module id and output port name
- `to.module` / `to.input` — target module id and input port name

## Example: 5-Module Workflow

```json
{
  "workflow_id": "polymer_nanoparticle_leaching",
  "scale": "molecular",
  "indicator": "leaching_rate",
  "modules": [
    { "id": "chain_builder",        "ref": "modules/chain_builder/chain_builder.json" },
    { "id": "ff_builder",           "ref": "modules/ff_builder/ff_builder.json" },
    { "id": "nanoparticle_builder", "ref": "modules/nanoparticle_builder/nanoparticle_builder.json" },
    { "id": "solvation_module",     "ref": "modules/solvation_module/solvation_module.json" },
    { "id": "leaching_evaluator",   "ref": "modules/leaching_evaluator/leaching_evaluator.json" }
  ],
  "connections": [
    {
      "from": { "module": "chain_builder",        "output": "polymer_chain" },
      "to":   { "module": "nanoparticle_builder", "input":  "polymer_chain" }
    },
    {
      "from": { "module": "ff_builder",           "output": "force_field"  },
      "to":   { "module": "nanoparticle_builder", "input":  "force_field"  }
    },
    {
      "from": { "module": "nanoparticle_builder", "output": "nanoparticle"    },
      "to":   { "module": "solvation_module",     "input":  "nanoparticle"    }
    },
    {
      "from": { "module": "solvation_module",   "output": "solvated_system" },
      "to":   { "module": "leaching_evaluator", "input":  "solvated_system" }
    }
  ]
}
```

## Workflow Patterns

### Parallel Sources

Modules with no incoming connections start immediately and run in the same topological level:

```
chain_builder  ──┐
                 ├──▶ nanoparticle_builder
ff_builder     ──┘
```

`chain_builder` and `ff_builder` have no dependency between them → they execute simultaneously.

### Data Fusion

Multiple upstream outputs merge into one module's inputs:

```
source_1 ─┐
          ├─▶ processor
source_2 ─┘
```

`processor` waits for all inputs before starting.

### Multi-Output

One module produces multiple output ports consumed by different downstream modules:

```
analyzer ──┬──▶ consumer_a
           └──▶ consumer_b
```

## Execution Order

NEXA automatically determines execution order using **topological sorting** (Kahn's algorithm). Modules are grouped into **topological levels**: all modules in the same level have their dependencies satisfied and can execute concurrently.

For the 5-module demo workflow:

```
level 0: [chain_builder, ff_builder]   ← no dependencies, run in parallel
level 1: [nanoparticle_builder]        ← depends on level 0
level 2: [solvation_module]            ← depends on level 1
level 3: [leaching_evaluator]          ← depends on level 2
```

Both backends exploit this structure:
- **local** — runs each level concurrently via `ThreadPoolExecutor`
- **remote** — submits all modules upfront via `sbatch --dependency=afterok:<ids>`, letting SLURM run independent modules in parallel and release dependent ones automatically

## Validation

NEXA validates workflows before execution:

- **No cycles** — workflows must be acyclic (DAG); a `ValueError` is raised if a cycle is detected
- **Module refs** — all `ref` paths must resolve to existing module JSON files
- **Port existence** — connections must reference ports declared in `input_ports` / `output_ports`

## Best Practices

- Use descriptive `workflow_id` values that encode scale and indicator
- Keep `ref` paths relative to the workflow file so the workflow is portable
- Group module definitions in a `modules/` subdirectory alongside the workflow JSON
- Keep workflows focused (< 20 modules); split large pipelines into composable sub-workflows
