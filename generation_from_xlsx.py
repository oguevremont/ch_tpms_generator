# Generated with help from ChatGPT

from enum import Enum, auto
import pandas as pd
import os
import shutil
import argparse
import random

import generate_cesogen
import generate_cahn_hilliard

def str2bool(v):
    return str(v).lower() in ('yes', 'true', 't', '1')

def read_excel_file(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    # Ensure required columns are present
    required_columns = {"ID", "param_name", "param_value", "type"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"The file must contain the following columns: {', '.join(required_columns)}")
    
    # Validate 'type' column values
    valid_types = {"cesogen", "cahnhilliard"}
    if not df["type"].isin(valid_types).all():
        raise ValueError(f"The 'type' column must contain only the values: {', '.join(valid_types)}")
    
    # Group by ID and process data
    result = []
    for id_value, group in df.groupby("ID"):
        # Extract type (assumes all rows for the same ID have the same type)
        unique_types = group["type"].unique()
        if len(unique_types) != 1:
            raise ValueError(f"ID {id_value} has inconsistent 'type' values.")
        type_value = unique_types[0]
        # Combine parameter names and values into semicolon-separated strings
        param_names = ";".join(group["param_name"].astype(str))
        param_values = ";".join(group["param_value"].astype(str))
        # Create a dictionary using the provided lists_to_dict function
        param_dict = lists_to_dict(param_names, param_values)
        # Append to the result
        result.append([str(id_value), str(type_value), param_dict])
    return result

def lists_to_dict(list_names, list_values):
    # Split the input strings into lists
    names = list_names.split(";")
    values = list_values.split(";")
    
    # Check if both lists have the same length
    if len(names) != len(values):
        raise ValueError("The number of parameter names and values must be the same.")
    
    # Create and return the dictionary
    return dict(zip(names, values))

# Define an Enum
class TypeMedium(Enum):
    Cesogen      = auto()
    CahnHilliard = auto()

def generate(id, type: TypeMedium, params: dict, working_directory,running_on_cluster=False):
    if not isinstance(type, TypeMedium):
        raise ValueError(f"Expected an instance of TypeMedium Enum, got {type(type)} instead.")

    file_path = f"generated_{str(random.randint(0,1e16))}.stl"
    if type == TypeMedium.Cesogen:
        generate_cesogen.run(params, file_path)
        # Example: Move a specific file (generated.stl) into the output directory
        if os.path.exists(file_path):
            # Create (or reuse) the directory 'generated_media/<id>/'
            output_dir = os.path.join("generated_media", str(id))
            os.makedirs(output_dir, exist_ok=True)
            destination = os.path.join(output_dir, os.path.basename("generated.stl"))
            shutil.move(file_path, destination)
            print(f"Moved '{file_path}' to '{destination}'")
        else:
            print(f"No file '{file_path}' found to move.")
    elif type == TypeMedium.CahnHilliard:
        generate_cahn_hilliard.run(params, working_directory,running_on_cluster)


    

def run(excel_file_name="to_generate.xlsx",job_id=None,running_on_cluster=False):
    print("We are in generation_from_xlsx.run()")
    list_of_cases = read_excel_file(excel_file_name)
    for index, list_of_params_for_case in enumerate(list_of_cases):
        id       = list_of_params_for_case[0]
        type_str = list_of_params_for_case[1]
        params   = list_of_params_for_case[2]
        if type_str == "cesogen":
            type_case = TypeMedium.Cesogen
        elif type_str == "cahnhilliard": 
            type_case = TypeMedium.CahnHilliard

        if job_id == None or job_id == id: # Depending if a job_id has been specified
            print(f"ID:{id}")
            working_dir = "working_directory"
            if job_id != None:
                working_dir = working_dir + "_" +id
            generate(id, type_case, params,working_dir,running_on_cluster)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run porous media generation job.")
    parser.add_argument("--excel_file_name", type=str, default="to_generate.xlsx",
                        help="Name of the Excel file to read job information from.")
    parser.add_argument("--job_id", type=str, default=None,
                        help="Job ID corresponding to the row in the Excel file.")
    parser.add_argument("--running_on_cluster", type=str2bool, default=False,
                    help="Whether to run on a cluster (true/false).")

    args = parser.parse_args()
    run(excel_file_name=args.excel_file_name, job_id=args.job_id, running_on_cluster=args.running_on_cluster)