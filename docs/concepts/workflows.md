# Workflows

A **workflow** in NEXA is a JSON file that defines a directed acyclic graph (DAG) of computational modules and their data dependencies.

## Workflow Structure

```json
{
  "name": "my_workflow",
  "modules": [
    {
      "id": "module_a",
      "definition": "path/to/module_a.json"
    },
    {
      "id": "module_b",
      "definition": "path/to/module_b.json"
    }
  ],
  "connections": [
    {
      "from": {"module": "module_a", "port": "output_data"},
      "to": {"module": "module_b", "port": "input_data"}
    }
  ]
}
```

### Fields

- **name**: Workflow identifier
- **modules**: List of module instances with unique IDs
  - **id**: Instance identifier (unique within workflow)
  - **definition**: Path to module JSON definition file
- **connections**: Data flow between modules
  - **from**: Source module ID and output port name
  - **to**: Target module ID and input port name

## Example: 5-Module Workflow

The demo workflow demonstrates common patterns:

```json
{
  "name": "advanced_demo_workflow",
  "modules": [
    {"id": "chain_builder", "definition": "modules/chain_builder/chain_builder.json"},
    {"id": "ff_builder", "definition": "modules/ff_builder/ff_builder.json"},
    {"id": "nanoparticle_builder", "definition": "modules/nanoparticle_builder/nanoparticle_builder.json"},
    {"id": "solvation_module", "definition": "modules/solvation_module/solvation_module.json"},
    {"id": "leaching_evaluator", "definition": "modules/leaching_evaluator/leaching_evaluator.json"}
  ],
  "connections": [
    {
      "from": {"module": "chain_builder", "port": "polymer_chain"},
      "to": {"module": "nanoparticle_builder", "port": "polymer_chain"}
    },
    {
      "from": {"module": "ff_builder", "port": "force_field"},
      "to": {"module": "nanoparticle_builder", "port": "force_field"}
    },
    {
      "from": {"module": "nanoparticle_builder", "port": "nanoparticle"},
      "to": {"module": "solvation_module", "port": "nanoparticle"}
    },
    {
      "from": {"module": "solvation_module", "port": "solvated_system"},
      "to": {"module": "leaching_evaluator", "port": "solvated_system"}
    }
  ]
}
```

## Workflow Patterns

### Parallel Execution

Modules without dependencies run in parallel:

```
module_a  ──┐
            ├──> module_c
module_b  ──┘
```

`module_a` and `module_b` execute simultaneously.

### Data Fusion

Multiple outputs merge into one module:

```
source_1 ─┐
          ├─> processor
source_2 ─┘
```

`processor` waits for both inputs before starting.

### Multi-Output

One module produces multiple outputs:

```
analyzer ──┬──> result_a
          └──> result_b
```

Different modules can consume different outputs.

## Execution Order

NEXA automatically determines execution order using **topological sorting** on the workflow DAG:

1. Identify modules without dependencies (sources)
2. Execute sources in parallel
3. Execute dependent modules once all inputs are ready
4. Repeat until all modules complete

Example execution order for the 5-module workflow:
```
['chain_builder', 'ff_builder', 'nanoparticle_builder', 'solvation_module', 'leaching_evaluator']
```

## Validation

NEXA validates workflows before execution:

- **No cycles**: Workflows must be acyclic (DAG)
- **Port matching**: Connections must link existing ports
- **Type compatibility**: Output/input types must match (via semantic types)
- **No orphans**: All modules must be reachable

## Best Practices

✓ Use descriptive module IDs  
✓ Document workflow purpose in the `name` field  
✓ Group related modules in subdirectories  
✓ Keep workflows focused (< 20 modules per workflow)  
✓ Use semantic types for all ports  
