import itertools
import pandas as pd
import os

TYPES = ["cesogen", "cahnhilliard"]

PARAM_SETS_CESOGEN = {
    #"TYPE_FILLING": ["gyroid", "p", "d", "iwp", "neovius", "lidinoid"],
    #"SCALING": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    #"THICKNESS": ["dilate_0.05","dilate_0.10","dilate_0.15","dilate_0.20",
    #              " ",
    #              "erode_0.05","erode_0.10","erode_0.15","erode_0.20"],
    # TODO Later take care of boolean operation

    "TYPE_FILLING": ["gyroid"],
    "SCALING_X": [0.2, 0.4, 0.6, 0.8],
    "SCALING_Y": [0.2, 0.4, 0.6, 0.8],
    "SCALING_Z": [0.2, 0.4, 0.6, 0.8],
    "THICKNESS": [-0.20, -0.10, 0, 0.10, 0.20],
    #"THICKNESS": [0],
    
    #"TYPE_FILLING": ["gyroid"],
    #"SCALING_X": [0.5],
    #"SCALING_Y": [0.5],
    #"SCALING_Z": [0.5],
    #"THICKNESS": [-0.2, -0.1, 0, 0.1, 0.2],
}

PARAM_SETS_CAHN_HILLIARD = {
    #"SEED"       : [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    #"SOLIDITY"   : [0.50],
    ##"TIME_END"   : [0.2e-5, 0.4e-5, 0.8e-5, 1.6e-5, 3.2e-5],,
    #"CH_BC": ["periodic","noflux"]
    "SEED": [9.0],
    "SOLIDITY": [0.50],
    "TIME_END": [1.6e-5],
    "CH_BC": ["periodic","noflux"]
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
        # Read the existing data to prevent overwriting
        existing_df = pd.read_excel(output_file)

        # Append only new entries
        df = pd.concat([existing_df, df]).drop_duplicates(subset=["ID"]).reset_index(drop=True)

    # Write the combined DataFrame back to the file
    df.to_excel(output_file, index=False)

    print(f"Excel file '{output_file}' has been updated with {len(df)} total rows.")

def run(excel_file_name="to_generate.xlsx"):
    """
    Run the Excel file generation with a specified output file name.
    Default: "to_generate.xlsx"
    """
    try:
        os.remove(excel_file_name)
        print(f"File '{excel_file_name}' has been deleted successfully.")
    except FileNotFoundError:
        print(f"File '{excel_file_name}' not found.")
    except PermissionError:
        print(f"Permission denied: Unable to delete '{excel_file_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

    # For Cahn-Hilliard:
    #main(1, excel_file_name)

    # For Cesogen:
    main(0, excel_file_name)

if __name__ == "__main__":
    run()
