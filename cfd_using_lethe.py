import os
import sys
import jinja2
import shutil
import subprocess
import argparse

################### Files and directories parameters ###################
executables_path = "./executables_and_scripts/"
templates_path = "./parameters_templates/"

lethe_executable = "lethe-fluid-sharp"  # Lethe executable
lethe_prm = "flow_around_rbf.prm"  

PATH = os.getcwd()

def str2bool(v):
    return str(v).lower() in ('yes', 'true', 't', '1')

def discover_rbf_files(base_dir, job_id=None):
    if not os.path.exists(base_dir):
        print(f"Directory '{base_dir}' does not exist.")
        return []

    rbf_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".input"):
                file_path = os.path.abspath(os.path.join(root, file))  # Ensure absolute path
                parent_folder = os.path.basename(root)  # Get direct parent folder name
                if job_id is None or job_id == parent_folder:
                    rbf_files.append(file_path)

    return rbf_files

def copy_template_files(source_dir, destination_dir):
    """
    Copies all files from source_dir to destination_dir.
    """
    if not os.path.exists(source_dir):
        print(f"Error: Templates directory '{source_dir}' not found.")
        return False

    os.makedirs(destination_dir, exist_ok=True)  # Ensure destination exists

    for file_name in os.listdir(source_dir):
        file_source = os.path.join(source_dir, file_name)
        file_destination = os.path.join(destination_dir, file_name)
        if os.path.isfile(file_source):  # Only copy files, not directories
            shutil.copy2(file_source, file_destination)
            print(f"Copied '{file_name}' to {file_destination}")

    return True

def run_lethe(rbf_file,running_on_cluster):
    absolute_lethe_path = os.path.abspath(os.path.join(executables_path, lethe_executable))

    # Get the absolute directory and filename of the RBF file
    rbf_dir = os.path.abspath(os.path.dirname(rbf_file))  # Ensure absolute path
    rbf_name = os.path.basename(rbf_file)

    # Save the current working directory
    original_dir = os.getcwd()

    # Get the absolute path for the templates folder
    abs_templates_path = os.path.abspath(templates_path)

    try:
        # Change to the directory of the RBF file
        os.chdir(rbf_dir)
        print(f"We are now here: {rbf_dir}")

        # Copy all files from the templates directory to the current directory
        if not copy_template_files(abs_templates_path, rbf_dir):
            print(f"Skipping Lethe run because template files could not be copied.")
            return

        MASS_FLOW_RATE = 0.1  # g/s
        set_velocity = MASS_FLOW_RATE / 1 / (1.2**2)  # =mass/density/surface_area
        replacement_dict = {
            "RBF_NAME": rbf_name,
            "SET_VELOCITY": str(set_velocity)  # Ensure value is a string
        }

        # Replace all keys in replacement_dict with their values in copied files
        for file_name in os.listdir(rbf_dir):
            file_path = os.path.join(rbf_dir, file_name)
            
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:  # Explicitly set encoding
                        content = file.read()\
                    # Replace each key in the file
                    for key, value in replacement_dict.items():
                        content = content.replace(str(key), str(value))  # Ensure string replacement\
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(content)
                    print(f"Updated placeholders in '{file_name}'.")
                
                except Exception as e:
                    print(f"Skipping file '{file_name}' (not a text file or unreadable): {e}")


        # Prepare and execute the command
        if running_on_cluster:
            command = f"srun {absolute_lethe_path} {lethe_prm}"
        else:
            command = f"mpirun -np 4 {absolute_lethe_path} {lethe_prm}"
        print(f"Running Lethe with command: {command}")
        os.system(command)

        print(f"Lethe simulation complete for RBF file: {rbf_file}")
    except Exception as e:
        print(f"Error running Lethe for RBF file {rbf_file}: {e}")
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def run(job_id=None,running_on_cluster=False):
    base_dir = "generated_media"
    rbf_files = discover_rbf_files(base_dir, job_id)

    if not rbf_files:
        print(f"No .input files found in '{base_dir}'.")
    else:
        print(f"Discovered {len(rbf_files)} .input files:")
        for rbf_file in rbf_files:
            print(f"Processing {rbf_file}...")
            # Run Lethe's fluid simulation
            run_lethe(rbf_file,running_on_cluster)

    print("All files processed.")
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CFD simulation using Lethe.")
    parser.add_argument("--job_id", type=int, required=True, help="Job ID to process.")
    parser.add_argument("--running_on_cluster", type=str2bool, default=False,
                    help="Whether to run on a cluster (true/false).")

    args = parser.parse_args()
    run(job_id=args.job_id, running_on_cluster=args.running_on_cluster)

