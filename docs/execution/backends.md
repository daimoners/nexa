# Execution Backends

NEXA supports multiple backends for workflow execution. All backends respect workflow DAG dependencies and enable parallel execution of independent modules.

## Local backend

Runs modules using Python `subprocess` on the local machine. Best for development and testing.

```bash
nexa workflow.json --backend local --workdir runs/myrun
```

**Features:**
- Sequential execution with automatic parallelization of independent modules
- Fast startup (< 1 second)
- Suitable for small to medium workflows
- No external dependencies

## Nextflow backend 

Generates and runs a Nextflow pipeline with containerization support.

```bash
nexa workflow.json --backend nextflow --workdir runs/myrun
```

**Features:**
- Container-based execution (Docker/Singularity)
- Reproducible environments
- Checkpoint and resume capability
- Workflow provenance tracking

## Remote backend (SLURM)

Executes workflows on HPC clusters using SLURM job scheduler via SSH.

```bash
nexa workflow.json \
  --backend remote \
  --remotehost cluster.example.com \
  --config nexa_config.json
```

**Features:**
- Dependency-aware SLURM job submission
- Automatic parallel scheduling of independent modules
- Job status monitoring via `squeue` and `sacct`
- Result synchronization with `rsync`
- Configurable SLURM parameters (partition, nodes, memory, time)

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
    "partition": "gpu",
    "nodes": 1,
    "ntasks_per_node": 4,
    "cpus_per_task": 2,
    "time": "01:00:00",
    "mem_per_cpu": "4G",
    "modules": ["python/3.10", "rdkit"]
  },
  "execution": {
    "poll_interval": 5,
    "max_wait_time": 3600
  }
}
```

### Example Execution

For a workflow with parallel modules:

```
chain_builder  ──┐
                 ├──> nanoparticle_builder ──> solvation_module
ff_builder  ─────┘
```

Timeline:
1. `chain_builder` and `ff_builder` submitted simultaneously (SLURM jobs #1001, #1002)
2. `nanoparticle_builder` submitted with `--dependency=afterok:1001:1002`
3. `solvation_module` submitted after `nanoparticle_builder` completes
4. Results automatically copied back to local machine

### Requirements

- SSH key-based authentication configured
- SLURM installed on remote cluster
- Python 3.10+ and dependencies on remote system
- `rsync` available on both local and remote

For detailed setup instructions, see `demo/README.md`.

## Choosing a Backend

| Backend | Use Case | Execution Speed | Setup Complexity |
|---------|----------|----------------|------------------|
| **local** | Development, testing, small workflows | Fast | None |
| **nextflow** | Reproducible, containerized workflows | Medium | Medium (Docker/Singularity) |
| **remote** | Large-scale HPC computations | Depends on queue | Medium (SSH + SLURM) |
