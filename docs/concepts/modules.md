# Modules

A **module** is a reusable computational unit defined by a JSON file. Modules can be Python scripts, executables, or any program that follows NEXA's interface conventions.

## Module Definition

```json
{
  "id": "chain_builder",
  "label": "Polymer Chain Builder",
  "description": "Generates a polymer chain from monomer SMILES",
  "executable": "python3",
  "script": "../../scripts/chain_builder.py",
  "input_ports":  [],
  "output_ports": ["polymer_chain"],
  "parameters": {
    "species": ["C(C)C"],
    "unit_ratio": "1:0",
    "mw": 5000.0
  },
  "resources": {
    "partition": "cpu",
    "cpus": 4,
    "mem": "8G",
    "time": "00:30:00"
  },
  "ontology_links": {
    "class": "ModelWave:PolymerModelConstruction",
    "outputs": {"polymer_chain": "ModelWave:PolymerStructure"}
  },
  "metadata": {
    "version": "1.0",
    "author": "CNR",
    "license": "MIT"
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique module identifier |
| `executable` | string | Command to run (`python3`, `bash`, …) |
| `script` | string | Path to script, relative to the module JSON file |
| `input_ports` | list | Names of expected input ports |
| `output_ports` | list | Names of output ports (each becomes `<port>.json`) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `label` | string | Human-readable name |
| `description` | string | What the module does |
| `parameters` | dict | Default parameter values |
| `resources` | dict | Per-module SLURM resource requirements (see below) |
| `container` | string | Docker/Singularity image (future use) |
| `ontology_links` | dict | Semantic type annotations |
| `metadata` | dict | Version, author, license |

### `resources` field

When using the `remote` backend, each module can declare its own SLURM resource requirements:

```json
"resources": {
  "partition": "gpu",
  "cpus": 8,
  "mem": "32G",
  "time": "04:00:00",
  "nodes": 1
}
```

These override the global SLURM settings in `nexa_config.json` for that specific module. This allows compute-heavy modules (e.g. DFT, MD) to request different allocations than lightweight pre/post-processing modules within the same simulation.

## Script Interface

All module scripts must follow this interface:

```bash
python3 script.py \
    [--input <port> <path.json>] ...  \
    [--params <params.json>]           \
    --output_dir <dir>
```

- `--input port path` — one flag per input connection; `port` matches a name in `input_ports`
- `--params path` — JSON file with merged module + simulation parameters
- `--output_dir dir` — directory where output files are written

Each output port is written as `<output_dir>/<port>.json`.

### Example Module Script

```python
#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--params", default=None)
    parser.add_argument("--input", action="append", nargs=2, default=[])
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    params = {}
    if args.params:
        with open(args.params) as f:
            params = json.load(f)

    inputs = {}
    for name, path in args.input:
        with open(path) as f:
            inputs[name] = json.load(f)

    # ... computation ...
    result = {"value": 42, **params}

    with open(output_dir / "output_data.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
```

## Module Types

### Source Modules

No input ports, only outputs (e.g. data generators, initial structure builders):

```json
{
  "id": "chain_builder",
  "input_ports":  [],
  "output_ports": ["polymer_chain"]
}
```

### Processor Modules

Both inputs and outputs:

```json
{
  "id": "nanoparticle_builder",
  "input_ports":  ["polymer_chain", "force_field"],
  "output_ports": ["nanoparticle"]
}
```

### Sink Modules

Inputs only, no outputs (e.g. analysis, reporting):

```json
{
  "id": "report_generator",
  "input_ports":  ["results"],
  "output_ports": []
}
```

## Multi-Input Modules

Modules can receive outputs from multiple upstream modules:

```bash
python3 script.py \
  --input polymer_chain chain.json \
  --input force_field   ff.json    \
  --output_dir outputs/
```

## Multi-Output Modules

Modules can write multiple output ports:

```python
# leaching_evaluator writes two ports
output_dir / "molecular_leaching_rate.json"
output_dir / "t_anneal.json"
```

These can be consumed independently by different downstream modules.

## Best Practices

- Keep modules focused (single responsibility)
- Use descriptive port names that match the data they carry
- Always handle missing or empty inputs gracefully
- Exit with a non-zero code on failure — NEXA uses the exit code to detect errors
- Log progress to stdout/stderr for debugging
