# NEXA Demo Workflow

This directory contains a complete demonstration of NEXA's capabilities with a 5-module polymer nanoparticle simulation workflow.

## Workflow Overview

The demo simulates the creation and analysis of polymer nanoparticles:

```
┌──────────────┐        ┌──────────────┐
│chain_builder │        │  ff_builder  │  (parallel execution)
└──────┬───────┘        └──────┬───────┘
       │                       │
       └───────────┬───────────┘
                   │
          ┌────────▼────────┐
          │nanoparticle_    │  (data fusion)
          │    builder      │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │solvation_module │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │leaching_evaluator│  (multi-output)
          └─────────────────┘
```

### Modules

1. **chain_builder**: Generates polymer chains from monomer SMILES
   - Input: species (MonomerSMILES)
   - Output: polymer_chain.json
   - Parameters: mw (molecular weight), unit_ratio

2. **ff_builder**: Creates force field parameters for monomers
   - Input: species (MonomerSMILES)
   - Output: force_field.json
   - Runs in parallel with chain_builder

3. **nanoparticle_builder**: Assembles nanoparticle from chain and force field
   - Inputs: polymer_chain, force_field
   - Output: nanoparticle.json
   - Parameters: nanoparticle_size

4. **solvation_module**: Adds solvent around nanoparticle
   - Input: nanoparticle
   - Output: solvated_system.json
   - Parameters: solvent_type (water/ethanol)

5. **leaching_evaluator**: Calculates leaching rate and annealing temperature
   - Input: solvated_system
   - Outputs: molecular_leaching_rate.json, t_anneal.json

## Running the Demo

### Basic Execution

```bash
# From repository root
nexa demo/demo_workflow.json --backend local
```

### With Custom Parameters

Create a simulation file:

```json
{
  "workflow": "demo/demo_workflow.json",
  "parameters": {
    "chain_builder": {
      "mw": 15000.0
    },
    "solvation_module": {
      "solvent_type": "ethanol"
    }
  }
}
```

Run with parameters:
```bash
nexa demo/demo_workflow.json --simulation my_params.json --backend local
```

### Remote Execution

For HPC cluster execution, copy `nexa_config.example.json` to `nexa_config.json`, edit with your cluster details, then:

```bash
nexa demo/demo_workflow.json --backend remote --remotehost your-cluster --config nexa_config.json
```

## Output Structure

After execution, results are in the work directory:

```
nexa_run/
├── outputs/
│   ├── chain_builder/
│   │   └── polymer_chain.json
│   ├── ff_builder/
│   │   └── force_field.json
│   ├── nanoparticle_builder/
│   │   └── nanoparticle.json
│   ├── solvation_module/
│   │   └── solvated_system.json
│   └── leaching_evaluator/
│       ├── molecular_leaching_rate.json
│       └── t_anneal.json
└── <module>_params.json (parameter files for each module)
```

## Workflow Features Demonstrated

- **Parallel Execution**: chain_builder and ff_builder run simultaneously (independent sources)
- **Data Fusion**: nanoparticle_builder waits for and merges outputs from both builders
- **Sequential Dependencies**: solvation → leaching follow strict ordering
- **Multi-Output Modules**: leaching_evaluator produces 2 separate output files
- **Parameter Passing**: Default and custom parameters support
- **Semantic Types**: All ports have ontological annotations (ModelWave namespace)

## Module Scripts

All module implementations are in `scripts/`:
- `chain_builder.py` - Polymer chain generation
- `ff_builder.py` - Force field parameter assignment
- `nanoparticle_builder.py` - Nanoparticle assembly
- `solvation_module.py` - Solvation box creation
- `leaching_evaluator.py` - Leaching kinetics calculation

Each script accepts:
- `--params <file>`: Module parameters (JSON)
- `--input <name> <file>`: Input data files
- `--output_dir <dir>`: Output directory

## Visualization

To see the workflow graph:

```bash
# Web-based interactive visualization (requires Node.js)
nexa-viz demo/demo_workflow.json

# Opens browser at http://localhost:5173
```

## Customization

To create your own workflow:

1. **Define modules**: Create JSON definitions in `modules/`
2. **Write scripts**: Implement module logic in `scripts/`
3. **Create workflow**: Define connections in workflow JSON
4. **Test locally**: Run with `--backend local`
5. **Scale up**: Use `--backend remote` for HPC execution

## Example Output Data

Sample `polymer_chain.json`:
```json
{
  "chain_id": "chain_001",
  "num_monomers": 42,
  "molecular_weight": 10000.0,
  "coordinates": [[0.0, 0.0, 0.0], ...],
  "topology": {"bonds": [[0, 1], ...]}
}
```

Sample `molecular_leaching_rate.json`:
```json
{
  "leaching_rate": 0.0234,
  "units": "mol/m^2/s",
  "temperature": 298.15,
  "solvent": "water"
}
```

## Troubleshooting

**Module execution fails:**
- Check that Python 3.10+ is available
- Verify all scripts have execute permissions
- Check module script paths in JSON definitions

**Missing output files:**
- Verify module completed without errors
- Check that script writes to `--output_dir`
- Look for error messages in console output

**Remote execution issues:**
- Verify SSH key-based authentication works
- Check SLURM is available on remote host
- Ensure remote_workdir exists and is writable

## Next Steps

- Modify parameters in `simulation_example.json`
- Create your own modules following the existing examples
- Explore different SLURM configurations in `nexa_config.example.json`
- Check the main [README](../README.md) for advanced usage

For more information, see the full documentation in [docs/](../docs/).
