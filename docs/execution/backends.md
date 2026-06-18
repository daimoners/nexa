# Execution Backends

NEXA supports three backends for workflow execution. All backends respect DAG dependencies and return a structured `WorkflowResult` with per-module status.

## Choosing a Backend

| Backend | Fan-out | Use case | Requirements |
|---------|---------|----------|--------------|
| `local` | `ThreadPoolExecutor` (parallel levels) | development, single machine | none |
| `nextflow` | Nextflow DSL2 processes | containerized, reproducible | Nextflow installed |
| `remote` | one `sbatch` per module | HPC clusters, per-module resources | SSH + SLURM |

---

## local

Runs modules as subprocesses on the local machine. Independent modules (same topological level) execute concurrently via `ThreadPoolExecutor`.

```bash
nexa workflow.json --backend local --workdir runs/myrun
```

**Parallel execution** — modules are grouped into topological levels; all modules in the same level run simultaneously:

```
level 0: [chain_builder, ff_builder]   ← parallel
level 1: [nanoparticle_builder]
level 2: [solvation_module]
level 3: [leaching_evaluator]
```

**Python API:**

```python
result = executor.run(backend="local", workdir="runs/myrun")
print(result.status)           # "success" | "failed"
print(result.modules["chain_builder"].status)  # "success"
```

---

## nextflow

Generates a **Nextflow DSL2** script from the workflow and runs it. Each module becomes a Nextflow `process`; data flows through channels. See [Nextflow Integration](nextflow.md) for details.

```bash
nexa workflow.json --backend nextflow --workdir runs/myrun
```

---

## remote (SLURM)

Submits **all modules upfront** as independent `sbatch` jobs on a remote HPC cluster via SSH. Each module's submission includes a `--dependency=afterok:<dep_ids>` directive encoding its specific upstream dependencies — so SLURM manages the DAG natively. Independent modules (same topological level) run in parallel; dependent modules start automatically once their inputs are ready. After all submissions, a single polling loop checks job status via `squeue`/`sacct`.

Each module can declare its own SLURM resource requirements via the `resources` field in `module.json`, overriding the global config for that specific module.

```bash
nexa workflow.json \
  --backend remote \
  --remotehost cluster.example.com \
  --config nexa_config.json
```

### Configuration

Create `nexa_config.json`:

```json
{
  "remote": {
    "hostname": "cluster.example.com",
    "username": "your_username",
    "remote_workdir": "/scratch/username/nexa_runs",
    "private_key": "~/.ssh/id_rsa"
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

`slurm.modules` lists environment modules to load in each job script (`module load …`).

### Per-module resources

Override global SLURM settings for individual modules in `module.json`:

```json
"resources": {
  "partition": "gpu",
  "cpus": 8,
  "mem": "32G",
  "time": "04:00:00"
}
```

Example: in a workflow where `chain_builder` is lightweight and `md_simulation` is heavy:

| Module | partition | mem | time |
|--------|-----------|-----|------|
| `chain_builder` | *(global default)* | 4G | 01:00:00 |
| `md_simulation` | gpu | 64G | 12:00:00 |

### How it works

For the 5-module demo, all 5 jobs are submitted immediately:

```
sbatch chain_builder        (no deps)        → job #1001
sbatch ff_builder           (no deps)        → job #1002
sbatch nanoparticle_builder --dependency=afterok:1001:1002  → job #1003
sbatch solvation_module     --dependency=afterok:1003       → job #1004
sbatch leaching_evaluator   --dependency=afterok:1004       → job #1005
```

Jobs `#1001` and `#1002` start immediately and run in parallel. SLURM releases `#1003` only after both complete, and so on. NEXA then polls all pending jobs in a single loop until everything is done, then `rsync`s outputs back.

This is the most efficient use of SLURM: the scheduler can optimize placement for all jobs at once, and independent modules overlap without any coordination overhead from NEXA.

### Requirements

- SSH key-based authentication to the remote host
- SLURM installed on the cluster
- Python 3.10+ with NEXA dependencies on the remote system
- `rsync` available on both local and remote
