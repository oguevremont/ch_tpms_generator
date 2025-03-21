import os
import sys
import jinja2
import trimesh
import argparse

################### Files and directories parameters ###################
executables_path             = "./executables_and_scripts/"
templates_path               = "./parameters_templates/"
bitpit_executable            = "levelsetRBF_prototype"
bitpit_prm_template          = "levelsetRBF_prototype.param"

PATH = os.getcwd()

def discover_stl_files(base_dir,job_id = None):
    if not os.path.exists(base_dir):
        print(f"Directory '{base_dir}' does not exist.")
        return []

    stl_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".stl"):
                file_path = os.path.join(root, file)
                parent_folder = os.path.basename(root)  # Get direct parent folder name
                if job_id == None or job_id == parent_folder:
                    stl_files.append(file_path)

    return stl_files

def generate_rbf_from_stl(stl_file):
    absolute_executable_path = os.path.abspath(os.path.join(executables_path, bitpit_executable))
    absolute_prm_path        = os.path.abspath(os.path.join(templates_path, bitpit_prm_template))

    stl_dir = os.path.dirname(stl_file)
    stl_name = os.path.basename(stl_file)

    if stl_name.endswith(".stl"):
        stl_name = stl_name[:-4]  # Remove the last 4 characters (".stl")

    original_dir = os.getcwd()

    try:
        # Change to the directory of the .stl file
        os.chdir(stl_dir)

        # Prepare the command to execute using absolute paths
        command = f"{absolute_executable_path} {stl_name} ./ {absolute_prm_path} none"

        # Run the command
        print(f"Running command: {command}")
        os.system(command)

        print(f"RBF generation complete for: {stl_name}")
    except Exception as e:
        print(f"Error generating RBF for {stl_name}: {e}")
    finally:
        # Change back to the original directory
        os.chdir(original_dir)

def repair_stl(stl_path):
    """
    Automatically repairs an STL file by removing degenerate triangles and filling holes.
    
    Args:
        stl_path (str): Path to the input STL file.
    """
    try:
        # Load the STL file
        mesh = trimesh.load_mesh(stl_path)

        # Check if the mesh is watertight
        if not mesh.is_watertight:
            print(f"Mesh is not watertight. Attempting to repair...")

            # Remove duplicate faces
            mesh.remove_duplicate_faces()

            # Remove degenerate faces
            mesh.remove_degenerate_faces()

            # Fill holes in the mesh
            if not mesh.is_watertight:
                mesh.fill_holes()

        # Save the repaired mesh under the same filename
        mesh.export(stl_path)
        print(f"Repaired STL saved to {stl_path}")
    except Exception as e:
        print(f"Error repairing STL: {e}")

def run(job_id=None):
    """
    Discover all .stl files, repair them, and generate RBF files.
    """
    base_dir = "generated_media"
    stl_files = discover_stl_files(base_dir,job_id=job_id)

    if not stl_files:
        print(f"No .stl files found in '{base_dir}'.")
    else:
        print(f"Discovered {len(stl_files)} .stl files:")
        for stl_file in stl_files:
            print(f"Processing {stl_file}...")

            # Repair the STL file
            repair_stl(stl_file)

            # Generate the RBF file from the repaired STL
            generate_rbf_from_stl(stl_file)

    print("All files processed.")
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert STL mesh to RBF representation.")
    parser.add_argument("--job_id", type=str, required=True, help="Job ID to process.")

    args = parser.parse_args()
    run(job_id=args.job_id)