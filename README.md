# NEXA - Semantic Workflow Engine

<div align="center">
  <img src="nexa_logo_transp.png" alt="NEXA Logo" width="300"/>
</div>

NEXA is a Python-based semantic workflow orchestration engine that executes modular computational pipelines using JSON workflow definitions and ontological annotations.

## Features

- **Semantic Workflow Definitions**: JSON-based workflow descriptions with ontological metadata
- **Modular Architecture**: Loosely-coupled modules communicating via JSON data files
- **Dependency-Aware Execution**: Automatic DAG analysis and topological sorting
- **Multiple Backends**: Local subprocess, Nextflow, and remote SLURM cluster execution
- **Parallel Execution**: Independent modules run in parallel automatically
- **Interactive Visualization**: Web-based workflow visualization with React Flow

## Installation

```bash
pip install -e .
```

Or install from PyPI (when published):
```bash
pip install nexa
```

### Visualization (Optional)

For web-based workflow visualization:
```bash
npm install -g nexa-viz
```

## Quick Start

NEXA includes a complete 5-module demo workflow:

```bash
# Run the demo workflow locally
nexa demo/demo_workflow.json --backend local

# Visualize the workflow (requires Node.js)
nexa-viz demo/demo_workflow.json
```

The demo workflow demonstrates:
- **Parallel execution**: chain_builder and ff_builder run simultaneously
- **Data fusion**: nanoparticle_builder merges outputs from both builders
- **Sequential dependencies**: solvation_module → leaching_evaluator
- **Multi-output modules**: leaching_evaluator produces 2 output files

See [demo/README.md](demo/README.md) for details.

## Usage

### Basic Workflow Execution

```bash
# Local execution
nexa workflow.json --backend local

# With simulation parameters
nexa workflow.json --simulation params.json --backend local

# Custom work directory
nexa workflow.json --backend local --workdir my_run
```

### Remote Execution (SLURM)

Execute workflows on HPC clusters:

```bash
# Create nexa_config.json with SLURM parameters
cat > nexa_config.json << EOF
{
  "remote": {
    "hostname": "cluster.example.com",
    "username": "user",
    "remote_workdir": "/scratch/user/nexa_runs"
  },
  "slurm": {
    "partition": "gpu",
    "time": "01:00:00",
    "mem_per_cpu": "4G"
  }
}
EOF

# Run on remote cluster
nexa workflow.json --backend remote --remotehost cluster.example.com --config nexa_config.json
```

## Workflow Structure

### Workflow Definition (JSON)

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

### Module Definition (JSON)

```json
{
  "name": "example_module",
  "version": "1.0.0",
  "executable": "python3",
  "script": "scripts/example.py",
  "inputs": {
    "input_data": {
      "semantic_type": "http://example.org/DataFormat"
    }
  },
  "outputs": {
    "output_data": {
      "semantic_type": "http://example.org/ResultFormat"
    }
  }
}
```

## Supported Backends

| Backend | Description | Use Case |
|---------|-------------|----------|
| **local** | Subprocess execution | Development, testing, small workflows |
| **nextflow** | Nextflow pipeline | Container-based, reproducible workflows |
| **remote** | SLURM cluster | HPC execution, large-scale computations |

## Architecture

NEXA workflows are directed acyclic graphs (DAGs) where:
- **Modules** are computational units (Python scripts, executables)
- **Connections** define data flow between modules
- **Ports** are typed inputs/outputs with semantic annotations
- **Execution** follows topological order respecting dependencies

```
┌─────────┐     ┌─────────┐
│ Module A│────▶│ Module C│
└─────────┘  ┌─▶└─────────┘
             │
┌─────────┐  │
│ Module B│──┘
└─────────┘
```

## Development

### Project Structure

```
nexa/
├── nexa/              # Core engine
│   ├── core/          # Workflow and module classes
│   ├── backends/      # Execution backends
│   ├── viz/           # Visualization tools
│   └── cli.py         # Command-line interface
├── demo/              # Example workflow
│   ├── modules/       # Module definitions
│   └── scripts/       # Module scripts
└── docs/              # Documentation
```

### Running Tests

```bash
# Test local backend
nexa demo/demo_workflow.json --backend local

# Validate workflow structure
python -m nexa.core.workflow demo/demo_workflow.json
```

## Documentation

Full documentation available in the [docs/](docs/) directory:
- [Installation Guide](docs/installation.md)
- [Quick Start Tutorial](docs/quickstart.md)
- [Workflow Concepts](docs/concepts/workflows.md)
- [Module Development](docs/concepts/modules.md)
- [Semantic Matching](docs/concepts/semantic-matching.md)
- [Backend Configuration](docs/execution/backends.md)
- [Nextflow Integration](docs/execution/nextflow.md)
- [Visualization Guide](docs/visualization.md)

## Requirements

- Python 3.10+
- NetworkX (for DAG operations)
- RDFlib (for ontology support)

Optional:
- Node.js 14+ (for visualization)
- Vite (for web UI)
- SSH access (for remote backend)
- SLURM (for HPC execution)

## License

See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8 style
- New features include tests
- Documentation is updated

## Citation

If you use NEXA in your research, please cite:

```bibtex
@software{nexa_2025,
  title = {NEXA: Semantic Workflow Engine},
  author = {NEXA Contributors},
  year = {2025},
  url = {https://github.com/daimoners/nexa}
}
```

## Contact

For questions, issues, or feature requests, please open an issue on GitHub.
