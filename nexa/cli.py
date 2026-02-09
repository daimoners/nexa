# nexa/cli.py
import argparse
from pathlib import Path
from .executor import UnifiedExecutor
from .utils.banner import print_banner

def main():
    print_banner()
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", help="Path to workflow or simulation JSON")
    parser.add_argument("--simulation", help="Path to simulation JSON (optional)")
    parser.add_argument("--backend", choices=["local", "nextflow", "remote"], default="local")
    parser.add_argument("--workdir", default="nexa_run")
    parser.add_argument("--remotehost", help="Remote host for SLURM execution (e.g., ariadne)")
    parser.add_argument("--config", help="Path to nexa_config.json for remote/advanced settings")
    args = parser.parse_args()

    wf_path = Path(args.workflow).resolve()
    sim_path = Path(args.simulation).resolve() if args.simulation else None

    executor = UnifiedExecutor(str(wf_path), str(sim_path) if sim_path else None)
    executor.run(
        backend=args.backend,
        workdir=args.workdir,
        remotehost=args.remotehost,
        config_file=args.config
    )

if __name__ == "__main__":
    main()

