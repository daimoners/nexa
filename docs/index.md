# Welcome to NEXA

**NEXA** is a semantic workflow engine for executing modular, multi-scale computational pipelines.  
It enables the composition of external modules (scripts, executables, containers) into validated, visualizable, and executable workflows using ontological reasoning and JSON-based definitions.

## ✨ Features

- **Semantic workflow definition** via JSON + ontologies
- **Modular execution**: run any external code as a "module"
- **Multiple backends**: local, Nextflow, and remote (SLURM)
- **Parallel execution**: independent modules run simultaneously
- **Interactive visualization** with React Flow (drag & drop, semantic edges)
- **Ontology-driven matching** of models and targets
- **Dependency-aware scheduling**: DAG-based execution order

## 🚀 Get Started

1. [Install NEXA](installation.md)
2. [Run your first workflow](quickstart.md)
3. [Visualize the workflow](visualization.md)

## 📚 Documentation

Explore the core concepts and advanced features:

- **[Workflows](concepts/workflows.md)**: How to define workflows with modules and connections
- **[Modules](concepts/modules.md)**: How to create reusable computational modules
- **[Semantic Matching](concepts/semantic-matching.md)**: How NEXA uses ontologies to validate connections
- **[Execution Backends](execution/backends.md)**: How to run workflows locally, with Nextflow, or on SLURM clusters
- **[Nextflow Integration](execution/nextflow.md)**: Advanced Nextflow configuration

## Quick Example

```bash
# Run demo workflow
nexa demo/demo_workflow.json --backend local

# Visualize it
nexa-viz demo/demo_workflow.json
```
