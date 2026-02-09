#!/usr/bin/env python
"""
Chain Builder Script
Generates a polymer chain from monomer species and unit ratios.
"""
import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser(description="Build a polymer chain from monomers")
    parser.add_argument("--input", nargs=2, action="append", help="port path")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--params", help="JSON parameter file")
    args = parser.parse_args()

    # Load parameters
    params = {}
    if args.params and os.path.exists(args.params):
        with open(args.params) as f:
            params.update(json.load(f))

    # Extract parameters (with defaults)
    species = params.get("species", ["C(C)C"])
    unit_ratio = params.get("unit_ratio", "1:0")
    mw = params.get("mw", 5000.0)

    # Generate polymer chain structure (simplified data)
    polymer_chain = {
        "id": "polymer_chain_001",
        "monomer_species": species if isinstance(species, list) else [species],
        "unit_ratio": unit_ratio,
        "target_molecular_weight": mw,
        "generated_mw": mw * 0.95,  # Simulated result slightly below target
        "num_units": int(mw / 100),
        "structure_format": "xyz",
        "coordinates": [
            {"atom": "C", "x": 0.0, "y": 0.0, "z": 0.0},
            {"atom": "C", "x": 1.5, "y": 0.0, "z": 0.0},
            {"atom": "C", "x": 3.0, "y": 0.0, "z": 0.0},
        ]
    }

    # Write output
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "polymer_chain.json")
    with open(out_path, "w") as f:
        json.dump(polymer_chain, f, indent=2)
    
    print(f"✓ Chain builder: Generated polymer chain with {polymer_chain['num_units']} units")
    print(f"  Species: {polymer_chain['monomer_species']}")
    print(f"  Target MW: {mw} Da, Generated MW: {polymer_chain['generated_mw']:.1f} Da")


if __name__ == "__main__":
    main()

