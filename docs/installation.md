# Installation

## Requirements

- Python >= 3.10
- Node.js >= 14 (for visualization, >= 18 recommended)
- Nextflow (optional, for Nextflow backend)
- SSH access with key-based authentication (for remote SLURM backend)

## Install from PyPI

```bash
pip install nexa
```

## Install from source

```bash
git clone https://github.com/daimoners/nexa.git
cd nexa
pip install -e .
```

This installs the `nexa` command-line tool.

## Install visualization (optional)

For web-based interactive workflow visualization:

```bash
npm install -g nexa-viz
```

Or use it via npx without installation:

```bash
npx nexa-viz workflow.json
```

## Verify installation

```bash
# Check NEXA version
nexa --help

# Check visualization tool (if installed)
nexa-viz --help
```

---

