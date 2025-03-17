import os

def run(params):
    # Call cesogen
    print("Generate Cesogen")

    running_on_mac = True

    finesse = 0.01

    if running_on_mac:
        command_line_str = f"docker run --rm -v $(pwd):/workspace -w /workspace ubuntu ./executables_and_scripts/cesogen -s {finesse} box scale 0.5,0.5,0.5 TYPE_FILLING scale SCALING,SCALING,SCALING THICKNESS intersection -o generated.stl"
    else:
        command_line_str = f"./executables_and_scripts/cesogen -s {finesse} box scale 0.5,0.5,0.5 TYPE_FILLING scale SCALING,SCALING,SCALING intersection -o generated.stl"

    for key, value in params.items():
        # key is the placeholder name (e.g., "PARAM1"), value is the actual parameter value (e.g., "10")
        if key == "THICKNESS":
            value = value.replace("_", " ")
        command_line_str = command_line_str.replace(key, str(value))

    # Execute the resulting command
    os.system(command_line_str)
    return 1
