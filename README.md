# NEXA - Semantic Workflow Engine

<div align="center">
  <img src="nexa_logo_transp.png" alt="NEXA Logo" width="300"/>
</div>

NEXA is a Python-based semantic workflow orchestration engine that executes modular computational pipelines using JSON workflow definitions and ontological annotations.

## Features

- **Semantic Workflow Definitions**: JSON workflow descriptions with ontological metadata
- **Modular Architecture**: loosely-coupled modules communicating via JSON data files
- **Dependency-Aware Execution**: automatic DAG analysis and topological sorting (Kahn's algorithm)
- **Parallel Execution**: independent modules run concurrently in the same topological level
- **Per-Module Resources**: each module can declare its own SLURM resource requirements
- **Multiple Backends**: local subprocess, Nextflow, and remote SLURM cluster execution
- **Structured Results**: `WorkflowResult` / `ModuleResult` return types for programmatic inspection
- **Event Callbacks**: real-time per-module status updates via `on_module_event`
- **Interactive Visualization**: web-based workflow visualization with React Flow

## Installation

```bash
pip install -e .
```

## Quick Start

NEXA includes a complete 5-module demo workflow:

```bash
# Run the demo workflow locally
nexa demo/demo_workflow.json --backend local

# With simulation parameters
nexa demo/demo_workflow.json --simulation demo/simulation_example.json --backend local

# Visualize the workflow
nexa-viz demo/demo_workflow.json
```

The demo workflow demonstrates:
- **Parallel execution** — `chain_builder` and `ff_builder` have no dependency between them and run in the same level simultaneously
- **Data fusion** — `nanoparticle_builder` merges outputs from both builders
- **Sequential dependencies** — `solvation_module` → `leaching_evaluator`
- **Multi-output modules** — `leaching_evaluator` produces 2 output files

## Usage

### CLI

```bash
# Local execution
nexa workflow.json --backend local

# With simulation parameters
nexa workflow.json --simulation params.json --backend local

# Custom work directory
nexa workflow.json --backend local --workdir my_run

# Nextflow execution
nexa workflow.json --backend nextflow --workdir nf_run

# Remote SLURM execution
nexa workflow.json --backend remote --remotehost cluster.example.com \
    --config nexa_config.json
```

### Python API

```python
from nexa import UnifiedExecutor, WorkflowResult

executor = UnifiedExecutor("workflow.json", "simulation.json")

# Optional: per-module event callback
def on_event(event_type, module_id, data):
    print(f"[{event_type}] {module_id}")

result: WorkflowResult = executor.run(
    backend="local",
    workdir="my_run",
    on_module_event=on_event,
)

print(result.status)        # "success" | "failed"
for mod_id, mod in result.modules.items():
    print(f"  {mod_id}: {mod.status}  outputs={mod.outputs}")
```

## Workflow Definition

```json
{
  "workflow_id": "my_workflow",
  "scale": "molecular",
  "indicator": "leaching_rate",
  "description": "Example multi-module workflow",
  "modules": [
    { "id": "module_a", "ref": "modules/module_a/module_a.json" },
    { "id": "module_b", "ref": "modules/module_b/module_b.json" }
  ],
  "connections": [
    {
      "from": { "module": "module_a", "output": "result" },
      "to":   { "module": "module_b", "input":  "data"   }
    }
  ]
}
```

## Module Definition

```json
{
  "id": "chain_builder",
  "label": "Polymer Chain Builder",
  "executable": "python3",
  "script": "../../scripts/chain_builder.py",
  "input_ports":  [],
  "output_ports": ["polymer_chain"],
  "parameters": {
    "species": ["C(C)C"],
    "mw": 5000.0
  },
  "resources": {
    "partition": "cpu",
    "cpus": 4,
    "mem": "8G",
    "time": "00:30:00"
  }
}
```

`resources` is optional. When present it overrides the global SLURM settings in `nexa_config.json` for that specific module — useful when different modules need different allocations (e.g. a DFT module on `gpu` and a pre-processing module on `cpu`).

### Module Script Interface

All module scripts must follow this interface:

```bash
python3 script.py \
    [--input <port> <path.json>] ...  \
    [--params  <params.json>]          \
    --output_dir <dir>
```

Outputs are written as `<output_dir>/<port>.json`, one file per output port.

## Remote Execution (SLURM)

Create `nexa_config.json`:

```json
{
  "remote": {
    "hostname": "cluster.example.com",
    "username": "user",
    "remote_workdir": "/scratch/user/nexa_runs"
  },
  "slurm": {
    "partition": "default",
    "nodes": 1,
    "ntasks": 1,
    "time": "01:00:00",
    "mem": "4G",
    "modules": ["python/3.11", "rdkit"]
  },
  "execution": {
    "poll_interval": 5,
    "max_wait_time": 3600
  }
}
```

Global SLURM settings apply to every module; per-module `resources` in `module.json` take precedence.

```bash
nexa workflow.json --backend remote --remotehost cluster.example.com \
    --config nexa_config.json
```

## Backends

| Backend | Fan-out | Use case |
|---------|---------|----------|
| `local` | thread pool (parallel levels) | development, single machine |
| `nextflow` | Nextflow DSL2 | container-based, reproducible |
| `remote` | `sbatch --dependency` per module (parallel) | HPC clusters, per-module resource control |

## Parallel Execution (local backend)

The local backend groups modules into **topological levels**: all modules whose dependencies are already complete form a level and execute concurrently via `ThreadPoolExecutor`.

Example for the demo workflow:
```
level 0: [chain_builder, ff_builder]   ← parallel (no inter-dependency)
level 1: [nanoparticle_builder]
level 2: [solvation_module]
level 3: [leaching_evaluator]
```

## Architecture

NEXA workflows are directed acyclic graphs (DAGs) where:
- **Modules** are computational units (Python scripts, executables, containers)
- **Connections** define data flow between modules via typed ports
- **Ports** are named inputs/outputs; data travels as JSON files
- **Execution** respects topological order; independent modules run in parallel

```
┌─────────────┐    ┌──────────────────┐
│ chain_builder│──▶│                  │
└─────────────┘    │ nanoparticle_bld │──▶ solvation ──▶ leaching
┌─────────────┐    │                  │
│  ff_builder  │──▶│                  │
└─────────────┘    └──────────────────┘
      level 0              level 1           level 2      level 3
```

## Project Structure

```
nexa/
├── nexa/
│   ├── core/
│   │   ├── module.py       # Module class (loads module.json, resolves resources)
│   │   └── workflow.py     # Workflow class (loads workflow.json, topological sort)
│   ├── backends/
│   │   ├── base.py         # BaseBackend, WorkflowResult, ModuleResult, EventCallback
│   │   ├── local.py        # LocalBackend (parallel levels via ThreadPoolExecutor)
│   │   ├── remote.py       # RemoteBackend (SSH + sbatch, per-module resources)
│   │   └── nextflow.py     # NextflowBackend (DSL2 generation)
│   ├── viz/                # Web-based workflow visualization
│   └── cli.py              # CLI entry point
├── demo/                   # 5-module example workflow
│   ├── modules/            # Module definitions
│   └── scripts/            # Module scripts
└── docs/                   # Extended documentation
```

## Requirements

- Python 3.10+
- `networkx` (DAG operations)
- `rdflib` (ontology support)

Optional:
- Node.js 14+ (visualization)
- SSH access (remote backend)
- SLURM (HPC execution)
- Nextflow (Nextflow backend)

## License

See [LICENSE](LICENSE) for details.

## Citation

```bibtex
@software{nexa_2025,
  title  = {NEXA: Semantic Workflow Engine},
  author = {DAIMON Team},
  year   = {2025},
  url    = {https://github.com/daimoners/nexa}
}
```
