import create_xlsx_from_parameters_sets
import generation_from_xlsx
import postprocess_generated_media
import stl_to_rbf
import cfd_using_lethe
import postprocess_cfd_results
import pandas as pd
import os
import subprocess

parallel_workflow  = True  # Toggle between parallel and sequential execution
running_on_cluster = False

EXCEL_FILE = "to_generate.xlsx"
JOB_SCRIPT = "job.sh"
OUTPUT_DIR = "generated_media"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_job_script(job_id):
    """Generate a job script for the cluster."""
    job_script_path = os.path.join(OUTPUT_DIR, f"{job_id}/job.sh")
    os.makedirs(os.path.dirname(job_script_path), exist_ok=True)

    script_content = f"""#!/bin/bash
#SBATCH --account=rrg-fede1988
#SBATCH --ntasks-per-node=40 #number of parallel tasks (as in mpirun -np X)
#SBATCH --nodes=1 #number of whole nodes used (each with up to 40 tasks-per-node)
#SBATCH --time=4:00:00 #maximum time for the simulation (hh:mm:ss)
#SBATCH --job-name=case_{job_id}
#SBATCH --mail-type=END #email preferences
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=guevremont.o@gmail.com

module load python/3.11.5
virtualenv --no-download $SLURM_TMPDIR/env
source $SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip

pip install --no-index -r $HOME/requirements.txt
source $HOME/.dealii

python generation_from_xlsx.py        --job_id {job_id} --excel_file_name {EXCEL_FILE} --running_on_cluster true
python postprocess_generated_media.py --job_id {job_id} 
python stl_to_rbf.py                  --job_id {job_id} 
python cfd_using_lethe.py             --job_id {job_id} --running_on_cluster=True
python postprocess_cfd_results.py     --job_id {job_id} 

deactivate
"""
    
    with open(job_script_path, "w") as f:
        f.write(script_content)
    return job_script_path

def submit_jobs(running_on_cluster):
    """Submit a job for each row in the Excel file."""
    list_of_cases = generation_from_xlsx.read_excel_file(EXCEL_FILE)
    for index, list_of_params_for_case in enumerate(list_of_cases):
        id       = list_of_params_for_case[0]
        type_str = list_of_params_for_case[1]
        params   = list_of_params_for_case[2]
        print(f"Parallel processing of {type_str} ID={id}")
    
        if running_on_cluster:
            job_script = create_job_script(id)
            # I comment this line for now.
            subprocess.run(["sbatch", job_script])
        else:
            # 2. Generate media from the Excel file
            generation_from_xlsx.run(excel_file_name=EXCEL_FILE, job_id=id)
            # 3. Post-process generated media
            postprocess_generated_media.run(job_id=id)
            # 4. Convert STL files to RBF format
            stl_to_rbf.run(job_id=id)
            # 5. Run CFD simulations using Lethe
            cfd_using_lethe.run(job_id=id,running_on_cluster=running_on_cluster)
            # 6. Post-process CFD results
            postprocess_cfd_results.run(job_id=id)

        print(f"Submitted job {id}.")

def main():
    print("Generating Excel file with cases...")
    # 1. Generate the Excel file
    create_xlsx_from_parameters_sets.run(excel_file_name=EXCEL_FILE)
    print("Excel file generated.")

    if parallel_workflow:
        print("Submitting jobs for parallel execution...")
        submit_jobs(running_on_cluster=running_on_cluster)
        print("All jobs submitted.")
    else:
        # 2. Generate media from the Excel file
        generation_from_xlsx.run(excel_file_name=EXCEL_FILE)
        # 3. Post-process generated media
        #postprocess_generated_media.run()
        # 4. Convert STL files to RBF format
        stl_to_rbf.run()
        # 5. Run CFD simulations using Lethe
        #cfd_using_lethe.run()
        # 6. Post-process CFD results
        #postprocess_cfd_results.run()

if __name__ == "__main__":
    main()
