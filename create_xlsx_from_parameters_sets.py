import itertools
import pandas as pd
import numpy as np
import os

TYPES = ["cesogen", "cahnhilliard"]

PARAM_SETS_CESOGEN = {
    "TYPE_FILLING": ["gyroid", "p", "d", "iwp", "neovius", "lidinoid"],
    "SCALING": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    #"TYPE_FILLING": ["gyroid"],
    #"SCALING": [0.2],
}

PARAM_SETS_CAHN_HILLIARD = {
    #"SEED"       : [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    #"SOLIDITY"   : [0.50],
    ##"TIME_END"   : [0.2e-5, 0.4e-5, 0.8e-5, 1.6e-5, 3.2e-5],
    "SEED"               : [9.0],
    "SOLIDITY"           : [0.50],
    "TIME_END"           : [1.6e-5],
    "CH_BC"              : ["noflux", "none"]
    # The none boundary condition corresponds to a Periodic BC.
    # (The NS periodic BC takes over)
}

def generate_id(type_str, param_names, param_values):
    """
    Generate an ID string in the format:
    <type>_<paramname1>_<paramvalue1>_<paramname2>_<paramvalue2>_...
    """
    parts = [type_str]
    for name, value in zip(param_names, param_values):
        parts.append(name)
        parts.append(str(value))
    return "_".join(parts)

def main(type_int, output_file):
    if type_int == 0:
        PARAM_SETS = PARAM_SETS_CESOGEN
    elif type_int == 1:
        PARAM_SETS = PARAM_SETS_CAHN_HILLIARD
    type_str = TYPES[type_int]

    param_names = list(PARAM_SETS.keys())
    param_values_lists = list(PARAM_SETS.values())

    all_combos = itertools.product(*param_values_lists)
    
    rows = []
    for combo in all_combos:
        # Generate the ID using the new function
        id_str = generate_id(type_str, param_names, combo)
        
        # Also keep a semicolon-separated list of param names and values for additional info
        joined_param_names = ";".join(param_names)                 
        joined_param_values = ";".join(str(v) for v in combo)      

        row_dict = {
            "ID": id_str,
            "type": type_str,
            "param_name": joined_param_names,
            "param_value": joined_param_values
        }
        rows.append(row_dict)

    df = pd.DataFrame(rows, columns=["ID", "type", "param_name", "param_value"])
    
    if os.path.exists(output_file):
        # Read the existing data
        existing_df = pd.read_excel(output_file)
        # Combine the new data with the existing data
        df = pd.concat([existing_df, df], ignore_index=True)

    # Write the combined DataFrame back to the file
    df.to_excel(output_file, index=False)
    
    print(f"Excel file '{output_file}' has been created/added with {len(df)} rows.")

def run():
    output_file = "to_generate.xlsx"
    if os.path.exists(output_file):
        os.remove(output_file)
        print("File removed successfully.")
    else:
        print("File does not exist.")

    # Uncomment one of the following calls:
    # For Cesogen:
    #main(0, output_file)
    
    # For Cahn-Hilliard:
    main(1, output_file)

if __name__ == "__main__":
    run()
