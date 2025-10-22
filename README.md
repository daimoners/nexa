# NEXA

**NEXA** is a semantic workflow engine for executing modular, multi-scale computational pipelines.  
It enables the composition of external modules (scripts, executables, containers) into validated, visualizable, and executable workflows using ontological reasoning and JSON-based definitions.

## Features

- **Semantic workflow definition** via JSON + ontologies
- **Modular execution**: run any external code as a "module"
- **Multiple backends**: local, Nextflow, remote
- **Interactive visualization** with React Flow (drag & drop, semantic edges)
- **Ontology-driven matching** of models and targets

## Quick Start

```bash
git clone https://github.com/daimoners/nexa.git
cd nexa
pip install -e .
nexa demo/demo_workflow.json --backend local
nexa-viz demo/demo_workflow.json
```

Then open http://localhost:5173 to see the workflow graph. 

## Requirements 

- Python ≥ 3.9
- Node.js ≥ 18 (for visualization)
- Nextflow (optional)
     
## License 

MIT License — see LICENSE 
