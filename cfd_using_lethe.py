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

    # Get the absolute path for the monolith.composite
    composite_file_source = os.path.join(templates_path, "monolith.composite")
    abs_composite_file_source = os.path.abspath(composite_file_source)

    try:
        # Verify that the source monolith.composite file exists
        if not os.path.exists(abs_composite_file_source):
            raise FileNotFoundError(f"'monolith.composite' not found at {abs_composite_file_source}")

        # Change to the directory of the RBF file
        os.chdir(rbf_dir)

        # Copy the monolith.composite file to the current directory
        current_dir = os.getcwd()
        composite_file_destination = os.path.join(current_dir, "monolith.composite")
        shutil.copy(abs_composite_file_source, ".")
        print(f"Copied 'monolith.composite' to {composite_file_destination}")

        # Replace the string "RBF_NAME" with the actual RBF name in the monolith.composite file
        with open(composite_file_destination, "r") as file:
            composite_content = file.read()
        composite_content = composite_content.replace("RBF_NAME", rbf_name)
        with open(composite_file_destination, "w") as file:
            file.write(composite_content)
        print(f"Replaced 'RBF_NAME' with '{rbf_name}' in monolith.composite.")

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
