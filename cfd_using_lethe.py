import os
import sys
import jinja2
import shutil
import subprocess

################### Files and directories parameters ###################
executables_path = "./executables_and_scripts/"
templates_path = "./parameters_templates/"

lethe_executable = "lethe-fluid-sharp"  # Lethe executable
lethe_prm        = templates_path+"flow_around_rbf.prm"

PATH = os.getcwd()

def discover_rbf_files(base_dir):
    if not os.path.exists(base_dir):
        print(f"Directory '{base_dir}' does not exist.")
        return []

    rbf_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".input"):
                rbf_files.append(os.path.join(root, file))

    return rbf_files


def run_lethe(rbf_file):
    absolute_lethe_path = os.path.abspath(os.path.join(executables_path, lethe_executable))

    # Get the directory and filename of the RBF file
    rbf_dir = os.path.dirname(rbf_file)
    rbf_name = os.path.basename(rbf_file)

    # Save the current working directory
    original_dir = os.getcwd()

    # Get the absolute path for the Lethe parameter file
    abs_lethe_param = os.path.abspath(lethe_prm)

    # Get the absolute path for the templates folder
    abs_templates_path = os.path.abspath(templates_path)

    try:
        # Verify that the templates directory exists
        if not os.path.exists(abs_templates_path):
            raise FileNotFoundError(f"Templates directory not found: {abs_templates_path}")

        # Change to the directory of the RBF file
        os.chdir(rbf_dir)

        # Copy all files from the templates directory to the current directory
        for file_name in os.listdir(abs_templates_path):
            file_source = os.path.join(abs_templates_path, file_name)
            file_destination = os.path.join(rbf_dir, file_name)
            if os.path.isfile(file_source):  # Only copy files, not directories
                shutil.copy(file_source, file_destination)
                print(f"Copied '{file_name}' to {file_destination}")

        MASS_FLOW_RATE = 0.1 #g/s
        set_velocity   = MASS_FLOW_RATE/1/(1.2**2)   # =mass/density/surface_area
        replacement_dict = {
                            "RBF_NAME"      : rbf_name,
                            "SET_VELOCITY": set_velocity
                            }

        # Replace all keys in replacement_dict with their values in copied files
        for file_name in os.listdir(rbf_dir):
            file_path = os.path.join(rbf_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    content = file.read()
                
                # Replace each key in the file
                for key, value in replacement_dict.items():
                    content = content.replace(key, value)
                
                with open(file_path, "w") as file:
                    file.write(content)
                print(f"Updated placeholders in '{file_name}'.")

        # Prepare and execute the command
        command = f"mpirun -np 8 {absolute_lethe_path} {abs_lethe_param}"
        print(f"Running Lethe with command: {command}")
        os.system(command)

        print(f"Lethe simulation complete for RBF file: {rbf_file}")
    except Exception as e:
        print(f"Error running Lethe for RBF file {rbf_file}: {e}")
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def run():
    base_dir = "generated_media"
    rbf_files = discover_rbf_files(base_dir)

    if not rbf_files:
        print(f"No .input files found in '{base_dir}'.")
    else:
        print(f"Discovered {len(rbf_files)} .input files:")
        for rbf_file in rbf_files:
            print(f"Processing {rbf_file}...")
            # Run Lethe's fluid simulation
            run_lethe(rbf_file)

    print("All files processed.")
    return 1

if __name__ == "__main__":
    run()
