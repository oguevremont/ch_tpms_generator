import os
import shutil
import sys
import jinja2
import create_xlsx_from_parameters_sets

run_lethe                    = True
run_paraview                 = True
keep_working_dir_contents    = True
remove_working_directory     = False
n_cores                      = 4


############## File parameters ###################
executables_path             = "./executables_and_scripts/"
templates_path               = "./parameters_templates/"
working_directory            = "working_directory_ch"

executable_lethe                     = "lethe-fluid"
executable_script_lethe_to_stl       = "ch_to_stl.py"

template_cahn_hilliard_prm           = "spinodal_3d.prm"
template_cahn_hilliard_prm_restart   = "spinodal_3d_restart.prm"


def copy_all_files(src_directory, dest_directory):
    """
    Copy all files from src_directory to dest_directory.
    """
    os.makedirs(dest_directory, exist_ok=True)
    for item in os.listdir(src_directory):
        src_item = os.path.join(src_directory, item)
        if os.path.isfile(src_item):
            shutil.copy(src_item, dest_directory)
            print(f"Copied {src_item} to {dest_directory}")

def substitute_parameters_in_files(directory, param_replacements):
    """
    Loop through all files in the given directory and replace each
    occurrence of the parameter keys with their corresponding values.
    """
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                # Replace each placeholder with its value.
                for key, value in param_replacements.items():
                    content = content.replace(key, str(value))
                with open(filepath, "w") as f:
                    f.write(content)
                print(f"Updated parameters in file: {filepath}")
            except Exception as e:
                print(f"Error processing file {filepath}: {e}")

def merge_parameters(original, appended):
    """
    Merge two dictionaries by concatenating values for common keys.
    For keys present only in one dictionary, the value is taken as is.
    """
    merged = {}
    # Add all keys from the original dictionary.
    for key, value in original.items():
        merged[key] = str(value)
    
    # For each key in appended, concatenate if already present; else, add it.
    for key, value in appended.items():
        if key in merged:
            merged[key] = merged[key] + str(value)
        else:
            merged[key] = str(value)
    return merged

def run_lethe_func(executables_abs_path):
    if run_lethe:
        # Run Lethe Cahn-Hilliard simulation
        first_line  = 'mpirun -np ' +str(n_cores)+' '+executables_abs_path+'/'+executable_lethe+' '+ template_cahn_hilliard_prm
        second_line = 'mpirun -np ' +str(n_cores)+' '+executables_abs_path+'/'+executable_lethe+' '+ template_cahn_hilliard_prm_restart
        print(first_line)
        print(second_line)

        ## Run Lethe simulation
        os.system(first_line)

        ## We restart to impose Dirichlet BC to obtain a closed STL
        os.system(second_line)

    
def run_paraview_func(executables_abs_path,param_original):
    if run_paraview:
        param_names = list(param_original.keys())
        param_values = list(param_original.values())
        case_name =  create_xlsx_from_parameters_sets.generate_id("cahnhilliard",param_names,param_values)
        
        command_line = "pvbatch " + executables_abs_path+'/'+executable_script_lethe_to_stl + " " + "spinodal.pvd"
        print(command_line)
        os.system(command_line)
     
def run(param_original):
    print("Generate Cahn-Hilliard")
    original_dir = os.getcwd()
    new_parameters = {
            "FINAL_TIME"                : float(param_original["TIME_END"])+1e-9,
            "TIME_STEP_R"               : str(1e-9),
            "BOUNDARY_CONDITION_R"      : "dirichlet",
            "CHECKPOINT_R"              : "false",
            "RESTART_R"                 : "true",
            
            #"TIME_END"                  : str(2e-5),
            "TIME_STEP"                 : str(float(param_original["TIME_END"])/5),
            "OUTPUT_FOLDER"             : "output",
            "CHECKPOINT"                : "true",
            "RESTART"                   : "false",
            "BOUNDARY_CONDITION"        : "noflux",
        }
    param_appended = merge_parameters(param_original, new_parameters)
    executable_absolute_path = os.path.abspath(os.path.join(os.getcwd(), "executables_and_scripts"))
    generated_absolute_path  = os.path.abspath(os.path.join(os.getcwd(), "generated_media"))

    # 1. We create a working directory, copy all template files then replace 
    # parameters in this working directory
    os.makedirs(working_directory, exist_ok=True)
    
    copy_all_files(templates_path  , working_directory)
    substitute_parameters_in_files(working_directory, param_appended)
    os.chdir(working_directory)
    working_directory_absolute_path = os.getcwd()


    # 2. We run Lethe CH simulations
    run_lethe_func(executable_absolute_path)


    # 3. We run Paraview
    run_paraview_func(executable_absolute_path,param_original)


    # 4. We copy generated.stl back to the case specify directory, and maybe the whole 
    # working directory as well
    param_names = list(param_original.keys())
    param_values = list(param_original.values())
    case_specific_directory = create_xlsx_from_parameters_sets.generate_id("cahnhilliard",
                                                                           param_names,
                                                                           param_values)
    destination_dir = os.path.join(generated_absolute_path, case_specific_directory)
    os.makedirs(destination_dir, exist_ok=True)
    print(destination_dir)
    # Copy each item from the working directory to the destination directory
    if keep_working_dir_contents:
        for item in os.listdir(working_directory_absolute_path):
            src_path = os.path.join(working_directory_absolute_path, item)
            dst_path = os.path.join(destination_dir, item)
            if os.path.isdir(src_path):
                # Copy the entire directory
                print("Sour. path: " + src_path)
                print("Dest. path: " + dst_path)
                os.makedirs(dst_path, exist_ok=True)
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                # Copy a single file
                print("Sour. path: " + src_path)
                print("Dest. path: " + destination_dir)
                shutil.copy2(src_path, destination_dir)
            print(f"Copied '{src_path}' to '{dst_path}'")
    else: 
        # Copy only .stl files from the working directory
        for item in os.listdir(working_directory_absolute_path):
            if item.lower().endswith(".stl"):
                src_path = os.path.join(working_directory, item)
                dst_path = os.path.join(destination_dir, item)
                shutil.copy2(src_path, dst_path)
                print(f"Copied '{src_path}' to '{dst_path}'")
    # Delete the working directory and all its contents
    if remove_working_directory:
        shutil.rmtree(working_directory_absolute_path)
    print(f"Deleted working directory: {working_directory_absolute_path}")


    # 5. We change the current directory back to the main one
    os.chdir(original_dir)
    


if __name__ == "__main__":
    # TODO delete these test params
    param_original = {
            "SOLIDITY": "0.45",
        }
    os.chdir("/home/olivier/generation_cesogen_ch/working_directory_ch")
    run_paraview_func("/home/olivier/generation_cesogen_ch/executables_and_scripts/",param_original)
    os.chdir("/home/olivier/generation_cesogen_ch")
    