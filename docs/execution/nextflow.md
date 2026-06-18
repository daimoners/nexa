# Nextflow Integration

NEXA automatically generates a valid **Nextflow DSL2** script from a workflow definition and executes it. Nextflow's own dataflow scheduler handles parallelism: independent modules run concurrently, dependent modules start only when their input files are ready.

## Usage

```bash
nexa workflow.json --backend nextflow --workdir runs/nf_run

# With simulation parameters
nexa workflow.json --simulation params.json --backend nextflow --workdir runs/nf_run
```

## How parallelism works

The generated script uses `path` inputs (not `val`) so Nextflow stages actual files between processes. When a process has no pending inputs, it starts immediately — which means independent modules (same topological level) run in parallel on separate Nextflow workers without any coordination from NEXA.

For the 5-module demo:

```
chain_builder()      ← starts immediately
ff_builder()         ← starts immediately (parallel with chain_builder)
nanoparticle_builder(chain_builder_out.polymer_chain, ff_builder_out.force_field)
                     ← waits for both files, then starts
solvation_module(nanoparticle_builder_out.nanoparticle)
leaching_evaluator(solvation_module_out.solvated_system)
```

Nextflow manages workers, retries, and resource allocation. With a cluster executor (e.g. `-profile slurm`) each process can run on a separate node.

## Generated Script

For each module NEXA generates a `process` block with:
- `path {port}` inputs — Nextflow stages upstream output files into the work directory
- `path "{port}.json", emit: {port}` outputs — tracked as named channels
- `publishDir "outputs/{module_id}", mode: 'copy'` — copies outputs to `workdir/outputs/` after each process completes
- Script block with `--input port ${port}` for each connected input (NEXA's standard interface)

Example for two connected modules:

```nextflow
nextflow.enable.dsl=2

workflow {
    chain_builder_out = chain_builder()
    ff_builder_out = ff_builder()
    nanoparticle_builder_out = nanoparticle_builder(
        chain_builder_out.polymer_chain,
        ff_builder_out.force_field
    )
}

process chain_builder {
    publishDir "outputs/chain_builder", mode: 'copy'
    input:
        /* no inputs */
    output:
        path "polymer_chain.json", emit: polymer_chain
    script:
    """
    python3 /abs/path/chain_builder.py --output_dir .
    """
}

process nanoparticle_builder {
    publishDir "outputs/nanoparticle_builder", mode: 'copy'
    input:
        path polymer_chain
        path force_field
    output:
        path "nanoparticle.json", emit: nanoparticle
    script:
    """
    python3 /abs/path/nanoparticle_builder.py \
        --input polymer_chain ${polymer_chain} \
        --input force_field ${force_field} \
        --output_dir .
    """
}
```

## WorkflowResult

After Nextflow completes, NEXA builds a `WorkflowResult` by checking whether the expected output files exist under `workdir/outputs/`:

```python
result = executor.run(backend="nextflow", workdir="runs/nf_run")
print(result.status)
for mod_id, mod in result.modules.items():
    print(f"  {mod_id}: {mod.status}")
```

## Cluster execution

Nextflow supports many cluster executors via profiles. Run from the Nextflow-generated directory:

```bash
# SLURM cluster
nextflow run main.nf -profile slurm

# AWS Batch
nextflow run main.nf -profile awsbatch

# Kubernetes
nextflow run main.nf -profile k8s
```

For cluster use, add per-process resource directives by extending `_generate_nextflow()` in `nexa/backends/nextflow.py` — for example reading from `module.resources`:

```nextflow
process md_simulation {
    cpus 8
    memory '32 GB'
    time '4h'
    ...
}
```

## Customization

To extend the generated script (container directives, custom labels, file staging), edit `nexa/backends/nextflow.py` — specifically `_generate_nextflow()`.

## Requirements

- [Nextflow](https://nextflow.io) installed and on `PATH`
- Java 11+
