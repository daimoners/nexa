# Installation

## Requirements

- Python >= 3.10
- `networkx` — DAG operations
- `rdflib` — ontology support

Optional:
- Node.js >= 14 (>= 18 recommended) — for workflow visualization
- Nextflow — for the `nextflow` backend
- SSH key-based authentication + SLURM — for the `remote` backend

## Install from source

```bash
git clone https://github.com/daimoners/nexa.git
cd nexa
pip install -e .
```

This registers the `nexa` and `nexa-viz` CLI commands.

## Install from PyPI

```bash
pip install nexa
```

## Verify installation

```bash
nexa --help
nexa-viz --help   # if Node.js is available
```

## Install visualization (optional)

```bash
# Install globally
npm install -g nexa-viz

# Or use without installing
npx nexa-viz workflow.json
```

## Remote backend setup

For HPC execution via the `remote` backend:

1. Configure SSH key-based authentication to the cluster
2. Ensure Python 3.10+ with NEXA dependencies is available on the remote system
3. Ensure `sbatch`, `squeue`, `sacct`, and `rsync` are on PATH on both machines
4. Create `nexa_config.json` with your cluster settings (see [Execution Backends](execution/backends.md))
