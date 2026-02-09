#!/usr/bin/env python
"""
Solvation Module Script
Adds solvent molecules around a nanoparticle structure.
"""
import argparse
import json
import os
import math


def main():
    parser = argparse.ArgumentParser(description="Solvate a nanoparticle structure")
    parser.add_argument("--input", nargs=2, action="append", help="port path")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--params", help="JSON parameter file")
    args = parser.parse_args()

    # Load parameters
    params = {}
    if args.params and os.path.exists(args.params):
        with open(args.params) as f:
            params.update(json.load(f))

    # Load inputs
    inputs = {}
    if args.input:
        for port, path in args.input:
            if os.path.exists(path):
                with open(path) as f:
                    inputs[port] = json.load(f)

    nanoparticle = inputs.get("nanoparticle", {})
    solvent_type = params.get("solvent_type", "water")
    box_margin = params.get("box_margin", 1.0)

    # Calculate box dimensions and solvent molecules
    np_size = nanoparticle.get("size_nm", 10.0)
    box_size = np_size + 2 * box_margin
    
    # Solvent properties
    solvent_data = {
        "water": {"density": 997, "molar_mass": 18.015, "molecules_per_nm3": 33.3},
        "ethanol": {"density": 789, "molar_mass": 46.07, "molecules_per_nm3": 15.6},
    }
    solvent_info = solvent_data.get(solvent_type, solvent_data["water"])
    
    # Calculate number of solvent molecules
    box_volume = box_size ** 3
    num_solvent_mols = int(box_volume * solvent_info["molecules_per_nm3"])

    # Generate solvated system
    solvated_system = {
        "id": "solvated_system_001",
        "nanoparticle_id": nanoparticle.get("id", "unknown"),
        "solvent_type": solvent_type,
        "solvent_density_kg_m3": solvent_info["density"],
        "num_solvent_molecules": num_solvent_mols,
        "box_dimensions": {
            "x": box_size,
            "y": box_size,
            "z": box_size
        },
        "total_atoms": nanoparticle.get("total_atoms", 0) + num_solvent_mols * (3 if solvent_type == "water" else 9),
        "structure_format": "gro",
        "box_margin_nm": box_margin,
        "coordinates": [
            {"atom": f"S{i}", "x": box_size/2 + 5*math.cos(2*math.pi*i/100), 
             "y": box_size/2 + 5*math.sin(2*math.pi*i/100), "z": box_size/2 + (i%10)*0.3}
            for i in range(min(100, num_solvent_mols))
        ]
    }

    # Write output
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "solvated_system.json")
    with open(out_path, "w") as f:
        json.dump(solvated_system, f, indent=2)
    
    print(f"✓ Solvation module: Generated solvated system")
    print(f"  Solvent: {solvent_type}")
    print(f"  Box size: {box_size:.2f} nm³")
    print(f"  Solvent molecules: {num_solvent_mols}")
    print(f"  Total atoms: {solvated_system['total_atoms']}")


if __name__ == "__main__":
    main()
