# Workflow Visualization

NEXA includes an interactive web-based visualizer built with **React Flow** and **Vite**.

## Features

- **Interactive DAG** — drag-and-drop node positioning
- **Semantic edges** — type-labeled connections (e.g. `polymer_chain → polymer_chain`)
- **Module metadata** — click nodes to see input/output ports, parameters
- **Mini-map** — navigate large workflows
- **Zoom and pan** — explore workflow structure
- **Source/Sink highlighting** — visual indication of module roles

## Usage

```bash
nexa-viz demo/demo_workflow.json
```

Then open http://localhost:5173 in your browser.

### Custom port

```bash
nexa-viz workflow.json --port 8080
```

### Remote server

If NEXA is running on a remote machine, use SSH tunneling:

```bash
# On your local machine:
ssh -L 5173:localhost:5173 user@remote-host

# On the remote host:
nexa-viz workflow.json
```

Then open http://localhost:5173 locally.

## Requirements

- Node.js >= 14 (>= 18 recommended)
- npm >= 7

```bash
node --version
npm --version
```

**Upgrade Node.js — Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Upgrade Node.js — macOS:**
```bash
brew install node@18
```

## Troubleshooting

**"Unexpected reserved word"** — Node.js < 14. Upgrade to 14+.

**Port already in use:**
```bash
nexa-viz workflow.json --port 5174
```

**Visualization doesn't update** — the visualizer reads the workflow file at startup; restart `nexa-viz` to pick up changes.

The visualizer is **read-only** — it displays the workflow structure but does not modify the JSON file.
