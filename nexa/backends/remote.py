# nexa/backends/remote.py
"""
Remote execution backend using SLURM for HPC clusters.
Submits jobs to a remote host via SSH and SLURM.
Respects workflow dependencies and executes in correct order.
"""
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict, deque
from .base import BaseBackend
from ..core.workflow import Workflow


class RemoteBackend(BaseBackend):
    """
    Remote execution backend using SLURM.
    Submits workflow jobs to a remote HPC cluster.
    """

    def __init__(self, workdir: Path = None, remotehost: str = None, config_file: str = None):
        """
        Initialize remote backend.
        
        Parameters
        ----------
        workdir : Path
            Local work directory
        remotehost : str
            Remote host for SLURM submission (e.g., 'ariadne')
        config_file : str
            Path to nexa_config.json with SLURM parameters
        """
        super().__init__(workdir)
        
        self.remotehost = remotehost
        self.config = self._load_config(config_file)
        
        # SLURM parameters from config or defaults
        self.slurm_params = self.config.get("slurm", {})
        self.slurm_partition = self.slurm_params.get("partition", "default")
        self.slurm_nodes = self.slurm_params.get("nodes", 1)
        self.slurm_ntasks = self.slurm_params.get("ntasks", 1)
        self.slurm_time = self.slurm_params.get("time", "01:00:00")
        self.slurm_mem = self.slurm_params.get("mem", "4G")
        
        # Remote paths - extract from "remote" section or use defaults
        remote_config = self.config.get("remote", {})
        self.remote_workdir = remote_config.get("remote_workdir", f"/tmp/nexa_run_{int(time.time())}")
        self.remote_username = remote_config.get("username", "")
        self.remote_private_key = remote_config.get("private_key", None)
        
        # Job tracking
        self.job_ids = {}  # module_id -> slurm_job_id
        self.job_status = {}  # module_id -> status
        
        print(f"[REMOTE] Backend initialized")
        print(f"  Remote host: {self.remotehost}")
        print(f"  Remote workdir: {self.remote_workdir}")
        print(f"  SLURM partition: {self.slurm_partition}")
        print(f"  SLURM time limit: {self.slurm_time}")

    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load NEXA configuration from JSON file."""
        if config_file:
            config_path = Path(config_file).resolve()
            if config_path.exists():
                with open(config_path) as f:
                    return json.load(f)
        
        # Try default nexa_config.json
        default_path = Path("nexa_config.json")
        if default_path.exists():
            with open(default_path) as f:
                return json.load(f)
        
        # Return empty config if not found
        return {}

    def _run_ssh_command(self, cmd: str) -> tuple:
        """
        Execute command on remote host via SSH.
        
        Returns
        -------
        tuple
            (returncode, stdout, stderr)
        """
        if not self.remotehost:
            raise ValueError("remotehost not specified for remote backend")
        
        ssh_cmd = f"ssh {self.remotehost} '{cmd}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr

    def _submit_slurm_job(self, module_id: str, script_path: str, 
                          inputs: Dict[str, Path], params: Dict) -> str:
        """
        Submit a module job to SLURM.
        
        Returns
        -------
        str
            SLURM job ID
        """
        # Create SLURM submission script
        script_content = self._create_slurm_script(module_id, script_path, inputs, params)
        
        # Write script to local file
        script_file = self.workdir / f"submit_{module_id}.sh"
        with open(script_file, "w") as f:
            f.write(script_content)
        
        # Copy script to remote
        scp_cmd = f"scp {script_file} {self.remotehost}:{self.remote_workdir}/"
        result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to copy script to remote: {result.stderr}")
        
        # Submit to SLURM
        submit_cmd = f"cd {self.remote_workdir} && sbatch submit_{module_id}.sh"
        returncode, stdout, stderr = self._run_ssh_command(submit_cmd)
        
        if returncode != 0:
            raise RuntimeError(f"SLURM submission failed: {stderr}")
        
        # Extract job ID from sbatch output
        # Output format: "Submitted batch job 12345"
        job_id = stdout.strip().split()[-1]
        print(f"[REMOTE] {module_id}: Submitted SLURM job {job_id}")
        
        return job_id

    def _create_slurm_script(self, module_id: str, script_path: str,
                             inputs: Dict[str, Path], params: Dict) -> str:
        """Create a SLURM submission script."""
        
        # Build input arguments
        input_args = ""
        for port, path in inputs.items():
            input_args += f"--input {port} {path} "
        
        # Build output directory
        output_dir = f"{self.remote_workdir}/outputs/{module_id}"
        
        # Create SLURM script
        script = f"""#!/bin/bash
#SBATCH --job-name={module_id}
#SBATCH --partition={self.slurm_partition}
#SBATCH --nodes={self.slurm_nodes}
#SBATCH --ntasks={self.slurm_ntasks}
#SBATCH --time={self.slurm_time}
#SBATCH --mem={self.slurm_mem}
#SBATCH --output={self.remote_workdir}/{module_id}_%j.out
#SBATCH --error={self.remote_workdir}/{module_id}_%j.err

# Create output directory
mkdir -p {output_dir}

# Run module
python3 {script_path} \\
    {input_args} \\
    --output_dir {output_dir}

if [ $? -eq 0 ]; then
    echo "SUCCESS"
    exit 0
else
    echo "FAILED"
    exit 1
fi
"""
        
        if params:
            # Save params to file
            params_file = f"{self.remote_workdir}/{module_id}_params.json"
            script += f"\n# Add params to command\n"
            # Params would be serialized and passed in actual implementation
        
        return script

    def _wait_for_job(self, job_id: str, module_id: str, timeout: int = 3600) -> bool:
        """
        Wait for SLURM job to complete.
        
        Parameters
        ----------
        job_id : str
            SLURM job ID
        module_id : str
            Module identifier
        timeout : int
            Maximum time to wait in seconds
            
        Returns
        -------
        bool
            True if job succeeded, False otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check job status
            check_cmd = f"squeue -j {job_id} -h"
            returncode, stdout, stderr = self._run_ssh_command(check_cmd)
            
            if returncode == 0 and not stdout.strip():
                # Job not in queue anymore - check if it succeeded
                check_exit_cmd = f"sacct -j {job_id} --format=State --noheader"
                returncode, stdout, stderr = self._run_ssh_command(check_exit_cmd)
                
                state = stdout.strip()
                if "COMPLETED" in state:
                    print(f"[REMOTE] {module_id}: Job {job_id} COMPLETED")
                    return True
                else:
                    print(f"[REMOTE] {module_id}: Job {job_id} FAILED (state: {state})")
                    return False
            
            # Job still running
            print(f"[REMOTE] {module_id}: Job {job_id} still running...")
            time.sleep(5)
        
        print(f"[REMOTE] {module_id}: Job {job_id} TIMEOUT")
        return False

    def execute(self, workflow: Workflow, parameters: dict = None):
        """
        Execute workflow on remote SLURM cluster.
        Respects dependencies and submits jobs accordingly.
        """
        print(f"\n[REMOTE] Executing workflow '{workflow.workflow_id}' on {self.remotehost}")
        
        # Create remote work directory
        mkdir_cmd = f"mkdir -p {self.remote_workdir}/outputs"
        returncode, _, stderr = self._run_ssh_command(mkdir_cmd)
        if returncode != 0:
            raise RuntimeError(f"Failed to create remote directory: {stderr}")
        
        # Get execution order
        order = workflow.get_execution_order()
        print(f"[REMOTE] Execution order: {order}")
        
        # Build dependency graph for job submission
        submitted_jobs = {}  # module_id -> job_id
        completed_modules = set()
        
        for mod_id in order:
            module = workflow.module_map[mod_id]
            
            # Wait for dependencies before submitting
            deps_satisfied = False
            while not deps_satisfied:
                deps = []
                for conn in workflow.connections:
                    if conn["to"]["module"] == mod_id:
                        deps.append(conn["from"]["module"])
                
                deps_satisfied = all(d in completed_modules for d in deps)
                
                if not deps_satisfied:
                    print(f"[REMOTE] {mod_id}: Waiting for dependencies: {set(deps) - completed_modules}")
                    # Check on submitted jobs
                    for check_mod, job_id in submitted_jobs.items():
                        if check_mod not in completed_modules:
                            if self._wait_for_job(job_id, check_mod):
                                completed_modules.add(check_mod)
                    time.sleep(1)
            
            # All dependencies satisfied - collect module inputs
            inputs = {}
            for conn in workflow.connections:
                if conn["to"]["module"] == mod_id:
                    src_mod = conn["from"]["module"]
                    src_port = conn["from"]["output"]
                    dst_port = conn["to"]["input"]
                    input_path = f"{self.remote_workdir}/outputs/{src_mod}/{src_port}.json"
                    inputs[dst_port] = Path(input_path)
            
            # Gather parameters
            mod_params = dict(module.parameters)
            if parameters:
                for k, v in parameters.items():
                    if k in mod_params:
                        mod_params[k] = v
            
            # Get script path
            script_path = module.get_script_path()
            if script_path is None:
                raise ValueError(f"Module {module.id} has no script defined.")
            
            # Submit job to SLURM
            try:
                job_id = self._submit_slurm_job(mod_id, str(script_path), inputs, mod_params)
                submitted_jobs[mod_id] = job_id
                
                # Wait for job completion
                if self._wait_for_job(job_id, mod_id):
                    completed_modules.add(mod_id)
                else:
                    raise RuntimeError(f"Module {mod_id} failed on remote host")
                    
            except Exception as e:
                print(f"[REMOTE] Error submitting {mod_id}: {e}")
                raise
        
        # Copy results back
        print(f"[REMOTE] Copying results back from {self.remotehost}")
        for mod_id in workflow.module_map:
            remote_dir = f"{self.remotehost}:{self.remote_workdir}/outputs/{mod_id}"
            local_dir = self.workdir / "outputs" / mod_id
            local_dir.mkdir(parents=True, exist_ok=True)
            
            rsync_cmd = f"rsync -avz {remote_dir}/ {local_dir}/"
            result = subprocess.run(rsync_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[REMOTE] Copied outputs for {mod_id}")
        
        print(f"[REMOTE] Workflow execution completed")
