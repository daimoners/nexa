# Welcome to NEXA

**NEXA** is a semantic workflow engine for executing modular, multi-scale computational pipelines. It enables the composition of external modules (scripts, executables, containers) into validated, visualizable, and executable workflows using ontological annotations and JSON-based definitions.

## Features

- **Semantic workflow definition** — JSON + ontology annotations
- **Modular execution** — run any external script or executable as a module
- **Parallel execution** — independent modules run simultaneously (topological levels)
- **Per-module resources** — each module can declare its own SLURM allocation
- **Multiple backends** — local, Nextflow, and remote SLURM
- **Structured results** — `WorkflowResult` / `ModuleResult` for programmatic inspection
- **Event callbacks** — real-time per-module status via `on_module_event`
- **Interactive visualization** — React Flow DAG viewer with semantic edge labels

## Get Started

1. [Install NEXA](installation.md)
2. [Run your first workflow](quickstart.md)
3. [Visualize the workflow](visualization.md)

## Documentation

- **[Workflows](concepts/workflows.md)** — define workflows with modules and connections
- **[Modules](concepts/modules.md)** — create reusable computational modules
- **[Semantic Matching](concepts/semantic-matching.md)** — ontology annotations and type metadata
- **[Execution Backends](execution/backends.md)** — local, Nextflow, SLURM
- **[Nextflow Integration](execution/nextflow.md)** — DSL2 generation details

## Quick Example

```bash
# Run the 5-module demo workflow
nexa demo/demo_workflow.json --backend local

# Visualize it
nexa-viz demo/demo_workflow.json
```

```python
from nexa import UnifiedExecutor, WorkflowResult

result: WorkflowResult = UnifiedExecutor("workflow.json").run(backend="local")
print(result.status)
for mod_id, mod in result.modules.items():
    print(f"  {mod_id}: {mod.status}")
```
