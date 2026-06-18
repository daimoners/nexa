# Nextflow Integration

NEXA automatically generates a valid **Nextflow DSL2** script from a workflow definition and runs it.

## Usage

```bash
nexa workflow.json --backend nextflow --workdir runs/nf_run
```

With simulation parameters:

```bash
nexa workflow.json --simulation params.json --backend nextflow --workdir runs/nf_run
```

## Generated Script

For each module NEXA generates a Nextflow `process` block with:
- `input:` — one `val()` channel per incoming connection
- `output:` — one `path` emit per output port
- `script:` — the module's executable + script path + `--output_dir .`

The `workflow` block chains processes in topological order, passing outputs as channels.

Example output for two connected modules:

```nextflow
nextflow.enable.dsl=2

workflow {
    chain_builder_out = chain_builder()
    nanoparticle_builder_out = nanoparticle_builder(chain_builder_out.polymer_chain)
}

process chain_builder {
    input:
        /* no inputs */
    output:
        path "polymer_chain.json", emit: polymer_chain
    script:
    """
    python3 /abs/path/to/chain_builder.py --output_dir .
    """
}

process nanoparticle_builder {
    input:
        val(polymer_chain)
    output:
        path "nanoparticle.json", emit: nanoparticle
    script:
    """
    python3 /abs/path/to/nanoparticle_builder.py --output_dir .
    """
}
```

The generated `main.nf` and optional `params.json` are written to `workdir/`.

## WorkflowResult

After Nextflow completes, NEXA returns a `WorkflowResult`. Per-module status is inferred from whether the expected output files (`<port>.json`) are present:

```python
result = executor.run(backend="nextflow", workdir="runs/nf_run")
print(result.status)   # "success" | "failed"
for mod_id, mod in result.modules.items():
    print(f"{mod_id}: {mod.status}")
```

## Customization

To extend the generated script (container directives, custom resource labels, file staging), edit `nexa/backends/nextflow.py` — specifically `_generate_nextflow()`.

## Requirements

- [Nextflow](https://nextflow.io) installed and on `PATH`
- Java 11+ (Nextflow dependency)
