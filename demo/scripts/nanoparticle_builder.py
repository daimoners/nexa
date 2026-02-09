#!/usr/bin/env python
"""
Nanoparticle Builder Script
Assembles a nanoparticle from a polymer chain and force field.
"""
import argparse
import json
import os
import math


def main():
    parser = argparse.ArgumentParser(description="Build a nanoparticle from polymer chain and force field")
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

    polymer_chain = inputs.get("polymer_chain", {})
    force_field = inputs.get("force_field", {})
    np_size = params.get("np_size", 10.0)
    np_type = params.get("np_type", "spherical")

    # Calculate nanoparticle properties
    num_chains = max(1, int(np_size / 2))
    total_atoms = num_chains * len(polymer_chain.get("coordinates", []))
    density = total_atoms / (4/3 * math.pi * (np_size/2)**3)

    # Generate nanoparticle structure
    nanoparticle = {
        "id": "nanoparticle_001",
        "type": np_type,
        "size_nm": np_size,
        "num_polymer_chains": num_chains,
        "total_atoms": total_atoms,
        "density_atoms_per_nm3": round(density, 2),
        "force_field_used": force_field.get("type", "unknown"),
        "monomer_composition": polymer_chain.get("monomer_species", ["unknown"]),
        "structure_format": "gro",
        "coordinates": [
            {"atom": f"P{i % num_chains}", "x": np_size/2 * math.cos(2*math.pi*i/num_chains), 
             "y": np_size/2 * math.sin(2*math.pi*i/num_chains), "z": i*0.5}
            for i in range(min(10, total_atoms))
        ]
    }

    # Write output
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "nanoparticle.json")
    with open(out_path, "w") as f:
        json.dump(nanoparticle, f, indent=2)
    
    print(f"✓ Nanoparticle builder: Generated {np_type} nanoparticle")
    print(f"  Size: {np_size} nm")
    print(f"  Polymer chains: {num_chains}")
    print(f"  Total atoms: {total_atoms}")
    print(f"  Density: {nanoparticle['density_atoms_per_nm3']} atoms/nm³")


if __name__ == "__main__":
    main()
