# Workflow Visualization

NEXA includes an interactive web-based visualizer built with **React Flow** and **Vite**.

## Features

- **Interactive DAG**: Drag-and-drop node positioning
- **Semantic edges**: Type-labeled connections (e.g., `polymer_chain → polymer_chain`)
- **Module metadata**: Click nodes to see inputs, outputs, parameters
- **Mini-map**: Navigate large workflows easily
- **Zoom and pan**: Explore workflow structure
- **Source/Sink highlighting**: Visual indication of module roles

## Installation

```bash
# Install globally
npm install -g nexa-viz

# Or use without installation
npx nexa-viz workflow.json
```

## Usage

```bash
nexa-viz demo/demo_workflow.json
```

Then open http://localhost:5173 in your browser.

### Custom port

```bash
nexa-viz workflow.json --port 8080
```

### Remote visualization

If NEXA is running on a remote server, use SSH tunneling:

```bash
# On your local machine
ssh -L 5173:localhost:5173 user@remote-host

# Then in another terminal on remote-host
nexa-viz workflow.json
```

Now access http://localhost:5173 from your local browser.

## Requirements

- Node.js >= 14 (recommended: >= 18)
- npm >= 7

To check your versions:

```bash
node --version
npm --version
```

### Upgrade Node.js (if needed)

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**macOS:**
```bash
brew install node@18
```

## Troubleshooting

**Error: "Unexpected reserved word"**
- Your Node.js version is too old (< 14)
- Solution: Upgrade to Node.js 14+ or use npx with the latest version

**Port already in use:**
```bash
nexa-viz workflow.json --port 5174
```

**Visualization doesn't update:**
- The visualizer reads the workflow file on startup
- Restart `nexa-viz` to see changes
     
## Note

The visualization is **read-only** – it displays the workflow structure but does not modify the workflow JSON file.

