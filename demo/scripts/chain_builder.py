# demo/scripts/chain_builder.py
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--params", help="JSON parameter file")
    args = parser.parse_args()

    params = {}
    if args.params and os.path.exists(args.params):
        with open(args.params) as f:
            params.update(json.load(f))

    output = {"polymer_chain": {"monomer": params.get("monomer", "default")}}
    out_path = os.path.join(args.output_dir, "polymer_chain.json")
    with open(out_path, "w") as f:
        json.dump(output, f)

if __name__ == "__main__":
    main()
