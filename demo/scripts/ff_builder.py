#!/usr/bin/env python
"""
Force Field Builder Script
Generates force field parameters from monomer species specifications.
"""
import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser(description="Build force field parameters from monomer species")
    parser.add_argument("--input", nargs=2, action="append", help="port path")
    parser.add_argument("--output_dir", required=True, help="Output directory")
    parser.add_argument("--params", help="JSON parameter file")
    args = parser.parse_args()

    # Load parameters
    params = {}
    if args.params and os.path.exists(args.params):
        with open(args.params) as f:
            params.update(json.load(f))

    # Load inputs (species from ff_builder input or from parameters)
    inputs = {}
    if args.input:
        for port, path in args.input:
            if os.path.exists(path):
                with open(path) as f:
                    inputs[port] = json.load(f)

    # Extract species from input or parameters
    species_data = inputs.get("species")
    if isinstance(species_data, dict):
        species = species_data.get("species") or species_data.get("monomer_species", ["C(C)C"])[0]
    else:
        species = params.get("species", "C(C)C")
    
    ff_type = params.get("ff_type", "OPLS-AA")

    # Generate force field parameters based on monomer species
    force_field = {
        "id": "force_field_001",
        "type": ff_type,
        "monomer_species": species if isinstance(species, list) else [species],
        "atom_types": ["C", "H", "O"],
        "bonds": [
            {"atom1": "C", "atom2": "C", "type": "single", "length": 0.153},
            {"atom1": "C", "atom2": "H", "type": "single", "length": 0.109},
        ],
        "angles": [
            {"atoms": ["C", "C", "C"], "angle": 109.5}
        ],
        "dihedrals": [
            {"atoms": ["C", "C", "C", "C"], "type": "improper"}
        ],
        "nonbonded": {
            "C": {"sigma": 0.355, "epsilon": 0.293},
            "H": {"sigma": 0.242, "epsilon": 0.063},
            "O": {"sigma": 0.296, "epsilon": 0.711}
        },
        "version": "1.0"
    }

    # Write output
    os.makedirs(args.output_dir, exist_ok=True)
    out_path = os.path.join(args.output_dir, "force_field.json")
    with open(out_path, "w") as f:
        json.dump(force_field, f, indent=2)
    
    print(f"✓ Force field builder: Generated {ff_type} force field")
    print(f"  Monomer species: {force_field['monomer_species']}")
    print(f"  Bond types: {len(force_field['bonds'])}")
    print(f"  Angle types: {len(force_field['angles'])}")


if __name__ == "__main__":
    main()


