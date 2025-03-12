import os

def run(params):
    # Call cesogen
    print("Generate Cesogen")

    command_line_str = "./executables_and_scripts/cesogen -s 0.02 box scale 0.5,0.5,0.5 TYPE_FILLING scale SCALING,SCALING,SCALING intersection -o generated.stl"

    for key, value in params.items():
        # key is the placeholder name (e.g., "PARAM1"), value is the actual parameter value (e.g., "10")
        command_line_str = command_line_str.replace(key, str(value))

    # Execute the resulting command
    os.system(command_line_str)
    return 1
