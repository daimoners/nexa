#!/usr/bin/env python
"""
Leaching Evaluator Script
Calculates molecular leaching rate and annealing temperature.
"""
import argparse
import json
import os
import math


def main():
    parser = argparse.ArgumentParser(description="Evaluate leaching rate from solvated system")
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

    solvated_system = inputs.get("solvated_system", {})
    temperature = params.get("temperature", 298.15)  # K
    pressure = params.get("pressure", 1.0)  # atm

    # Calculate leaching rate based on system properties
    # This is a simplified model for demonstration
    num_atoms = solvated_system.get("total_atoms", 1000)
    num_solvent = solvated_system.get("num_solvent_molecules", 100)
    
    # Simplified leaching rate calculation
    # Base rate depends on solvent type and conditions
    base_rate = 1e-10  # s^-1
    
    # Arrhenius-like temperature dependence
    activation_energy = 50000  # J/mol
    R = 8.314  # J/(mol*K)
    temp_factor = math.exp(-activation_energy / (R * temperature))
    
    # Solvent effect
    solvent_type = solvated_system.get("solvent_type", "water")
    solvent_factors = {
        "water": 1.0,
        "ethanol": 0.8,
        "acetone": 0.6,
    }
    solvent_factor = solvent_factors.get(solvent_type, 1.0)
    
    # Combined leaching rate
    molecular_leaching_rate = base_rate * temp_factor * solvent_factor * (1 + num_solvent/1000)
    
    # Optimal annealing temperature (simplified model)
    # Typically around 0.4-0.5 of melting temperature
    # For polymers, estimate around 50-70% of Tg
    base_tg = 350  # K (typical polymer glass transition)
    t_anneal = base_tg * 0.6 + temperature * 0.2
    
    # Create output files
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Molecular leaching rate output
    rate_out_path = os.path.join(args.output_dir, "molecular_leaching_rate.json")
    molecular_leaching_rate_data = {
        "value": molecular_leaching_rate,
        "unit": "1/s",
        "scientific_notation": f"{molecular_leaching_rate:.3e}",
        "calculation_method": "Arrhenius with solvent correction",
        "temperature_K": temperature,
        "pressure_atm": pressure,
        "solvent_type": solvent_type,
        "confidence": "estimated"
    }
    with open(rate_out_path, "w") as f:
        json.dump(molecular_leaching_rate_data, f, indent=2)
    
    # Annealing temperature output
    anneal_out_path = os.path.join(args.output_dir, "t_anneal.json")
    t_anneal_data = {
        "value": t_anneal,
        "unit": "K",
        "celsius": t_anneal - 273.15,
        "calculation_basis": "Glass transition temperature based model",
        "recommended_procedure": "Heat at this temperature for optimal polymer relaxation"
    }
    with open(anneal_out_path, "w") as f:
        json.dump(t_anneal_data, f, indent=2)
    
    print(f"✓ Leaching evaluator: Analysis complete")
    print(f"  Molecular leaching rate: {molecular_leaching_rate:.3e} s⁻¹")
    print(f"  Temperature: {temperature} K ({temperature - 273.15:.1f}°C)")
    print(f"  Annealing temperature: {t_anneal:.1f} K ({t_anneal - 273.15:.1f}°C)")
    print(f"  Solvent type: {solvent_type}")


if __name__ == "__main__":
    main()
