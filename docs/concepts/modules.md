# Modules

A **module** is a reusable computational unit defined by a JSON file. Modules can be Python scripts, executables, or any program that follows NEXA's interface conventions.

## Module Definition

```json
{
  "name": "chain_builder",
  "version": "1.0.0",
  "executable": "python3",
  "script": "scripts/chain_builder.py",
  "inputs": {
    "species": {
      "semantic_type": "http://modelwave.org/ns/MonomerSMILES"
    }
  },
  "outputs": {
    "polymer_chain": {
      "semantic_type": "http://modelwave.org/ns/PolymerStructure"
    }
  },
  "parameters": {
    "mw": 10000.0,
    "unit_ratio": 1.0
  }
}
```

### Fields

- **name**: Module identifier
- **version**: Semantic version (for tracking)
- **executable**: Command to run (e.g., `python3`, `bash`, `/usr/bin/myapp`)
- **script**: Path to the script file (relative to module definition)
- **inputs**: Dictionary of input ports with semantic types
- **outputs**: Dictionary of output ports with semantic types
- **parameters**: Default parameter values

## Script Interface

Modules must accept these command-line arguments:

### Required Arguments

```bash
--output_dir <directory>    # Where to write output files
```

### Optional Arguments

```bash
--params <file.json>        # JSON file with module parameters
--input <name> <file.json>  # Input data files (one per input port)
```

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
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load parameters
    params = {}
    if args.params:
        with open(args.params) as f:
            params = json.load(f)
    
    # Load inputs
    inputs = {}
    for name, path in args.input:
        with open(path) as f:
            inputs[name] = json.load(f)
    
    # Process data
    result = {"value": 42, **params}
    
    # Write output
    with open(output_dir / "output_data.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
```

## Module Types

### Source Modules

No input ports, only outputs:

```json
{
  "name": "data_generator",
  "inputs": {},
  "outputs": {
    "data": {"semantic_type": "http://example.org/Data"}
  }
}
```

### Processor Modules

Both inputs and outputs:

```json
{
  "name": "transformer",
  "inputs": {
    "raw_data": {"semantic_type": "http://example.org/RawData"}
  },
  "outputs": {
    "processed_data": {"semantic_type": "http://example.org/ProcessedData"}
  }
}
```

### Sink Modules

Inputs only, no outputs:

```json
{
  "name": "report_generator",
  "inputs": {
    "results": {"semantic_type": "http://example.org/Results"}
  },
  "outputs": {}
}
```

## Semantic Types

Semantic types enable:
- **Type checking**: Validate compatible connections
- **Automatic workflow discovery**: Match modules by data types
- **Documentation**: Self-describing interfaces

Use URIs from domain ontologies:
```
http://modelwave.org/ns/PolymerStructure
http://modelwave.org/ns/ForceFieldParameters
http://purl.obolibrary.org/obo/CHEBI_24431
```

## Multi-Input Modules

Modules can have multiple inputs:

```json
{
  "name": "nanoparticle_builder",
  "inputs": {
    "polymer_chain": {"semantic_type": "http://modelwave.org/ns/PolymerStructure"},
    "force_field": {"semantic_type": "http://modelwave.org/ns/ForceFieldParameters"}
  },
  "outputs": {
    "nanoparticle": {"semantic_type": "http://modelwave.org/ns/NanoparticleStructure"}
  }
}
```

Usage:
```bash
python3 script.py \
  --input polymer_chain chain.json \
  --input force_field ff.json \
  --output_dir outputs/
```

## Multi-Output Modules

Modules can produce multiple outputs:

```json
{
  "name": "analyzer",
  "outputs": {
    "leaching_rate": {"semantic_type": "http://example.org/LeachingRate"},
    "t_anneal": {"semantic_type": "http://example.org/Temperature"}
  }
}
```

Write each output to a separate file:
```python
output_dir / "leaching_rate.json"
output_dir / "t_anneal.json"
```

## Best Practices

✓ Use semantic versioning for modules  
✓ Document semantic types with URIs  
✓ Validate input data in scripts  
✓ Write structured output (JSON preferred)  
✓ Handle errors gracefully with exit codes  
✓ Log progress to stdout/stderr  
✓ Keep modules focused (single responsibility)  
