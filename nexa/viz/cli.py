# nexa/viz/cli.py
"""
CLI to visualize a Nexus concrete workflow in the browser using React Flow.

Designed for both local and remote execution.
When running on a remote server, use SSH tunneling to access the UI.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .workflow_to_cytoscape import workflow_to_cytoscape


def is_interactive() -> bool:
    """Check if running in an interactive terminal (likely local)."""
    return sys.stdout.isatty()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a Nexus concrete workflow in the browser."
    )
    parser.add_argument("workflow", help="Path to concrete workflow JSON file")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open browser automatically (recommended for remote servers)",
    )
    args = parser.parse_args()

    workflow_path = Path(args.workflow).resolve()
    if not workflow_path.exists():
        print(f" Error: Workflow file not found: {workflow_path}", file=sys.stderr)
        sys.exit(1)

    # Load workflow
    try:
        with open(workflow_path) as f:
            workflow = json.load(f)
    except Exception as e:
        print(f" Error loading workflow: {e}", file=sys.stderr)
        sys.exit(1)

    # Convert to React Flow-compatible format
    try:
        cy_data = workflow_to_cytoscape(workflow)
    except Exception as e:
        print(f" Error converting workflow: {e}", file=sys.stderr)
        sys.exit(1)

    # Create temporary directory for the frontend app
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Copy frontend templates
        template_dir = Path(__file__).parent / "templates"
        required_files = {
            "index.html",
            "app.jsx",
            "WorkflowVisualizer.jsx",
            "vite.config.js",
            "package.json",
        }
        for item in template_dir.iterdir():
            if item.is_file() and item.name in required_files:
                shutil.copy(item, tmp_path)

        # Write graph data
        data_js = f"export const graphData = {json.dumps(cy_data, indent=2)};"
        with open(tmp_path / "graphData.js", "w") as f:
            f.write(data_js)

        # Change to temp dir and install dependencies
        os.chdir(tmpdir)
        print(" Installing frontend dependencies...")
        try:
            subprocess.run(
                ["npm", "install"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            print(" Failed to install npm dependencies. Is Node.js installed?", file=sys.stderr)
            sys.exit(1)

        print("\n Nexus Workflow Visualizer is starting...\n")

        # Determine if we should try to open the browser
        should_open = not args.no_open and is_interactive()

        if should_open:
            print(" Opening browser at http://localhost:5173")
        else:
            print(" Server will be available at http://localhost:5173")
            print("\n To access from your local machine, set up an SSH tunnel:")
            print("   ssh -L 5173:localhost:5173 user@your-remote-server")
            print("   Then open http://localhost:5173 in your local browser.\n")

        # Start Vite dev server
        try:
            if should_open:
                import threading
                import webbrowser

                def open_browser():
                    webbrowser.open("http://localhost:5173")

                threading.Timer(1.5, open_browser).start()

            # Vite will read vite.config.js and bind to 0.0.0.0:5173
            subprocess.run(["npm", "run", "dev"], check=True)
        except KeyboardInterrupt:
            print("\n  Server stopped by user.")
        except subprocess.CalledProcessError as e:
            print(f" Vite server failed: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
