# demo/scripts/ff_builder.py
import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs=2, action="append", help="port path")
    parser.add_argument("--output_dir", required=True)
    args = parser.parse_args()

    inputs = {}
    if args.input:
        for port, path in args.input:
            with open(path) as f:
                inputs[port] = json.load(f)

    output = {"force_field": {"type": "generic", "based_on": inputs.get("polymer_chain", {})}} 
    out_path = os.path.join(args.output_dir, "force_field.json")
    with open(out_path, "w") as f:
        json.dump(output, f)

if __name__ == "__main__":
    main()
