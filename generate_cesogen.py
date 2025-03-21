import os

def run(params,file_path="./generated.stl"):
    # Call cesogen
    print("Generate Cesogen")

    running_on_mac = False

    finesse = 0.01

    command_line_str = f"./executables_and_scripts/cesogen -s {finesse} box scale 0.5,0.5,0.5 TYPE_FILLING scale SCALING_X,SCALING_Y,SCALING_Z THICKNESS intersection -o {file_path}"
    if running_on_mac:
        command_line_str = "docker run --rm -v $(pwd):/workspace -w /workspace ubuntu " + command_line_str  
          
    for key, value in params.items():
        # key is the placeholder name (e.g., "PARAM1"), value is the actual parameter value (e.g., "10")
        if key == "THICKNESS":
            thickness_value = float(value)  # Ensure it's a float
            if thickness_value < 0:
                value = f"erode {abs(thickness_value)}"
            else:
                value = f"dilate {thickness_value}"
        command_line_str = command_line_str.replace(key, str(value))

    # Execute the resulting command
    os.system(command_line_str)
    return 1
