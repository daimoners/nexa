# nexa/viz/workflow_to_cytoscape.py
"""
Convert a Nexus concrete workflow to Cytoscape.js JSON format.
"""
from typing import List, Dict, Any
from pathlib import Path


def workflow_to_cytoscape(workflow: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    Convert a concrete workflow (with modules and connections) to Cytoscape.js format.

    Returns
    -------
    dict
        {"elements": {"nodes": [...], "edges": [...]}}
    """
    nodes = []
    edges = []

    # Nodes: one per module
    for mod in workflow["modules"]:
        node = {
            "data": {
                "id": mod["id"],
                "label": mod["id"],
                "ref": mod.get("ref", ""),
            }
        }
        nodes.append(node)

    # Edges: from connections
    for i, conn in enumerate(workflow["connections"]):
        edge = {
            "data": {
                "id": f"e{i}",
                "source": conn["from"]["module"],
                "target": conn["to"]["module"],
                "source_port": conn["from"]["output"],
                "target_port": conn["to"]["input"],
            }
        }
        edges.append(edge)

    return {"elements": {"nodes": nodes, "edges": edges}}
