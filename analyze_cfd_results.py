import os
import csv
import sys
import numpy as np

verbosity = True

def extract_pressure_drop(data_file):
    try:
        time_steps    = []
        pressure_drop = []

        with open(data_file, 'r') as input_file:
            lines = input_file.readlines()

            # Skip the header (first line) and process each data line
            for line in lines[1:]:
                parts = line.strip().split()
                time_steps.append(float(parts[0]))
                pressure_drop.append(float(parts[1]))

        time_steps         = np.array(time_steps)
        pressure_drop      = np.array(pressure_drop)
        last_pressure_drop = pressure_drop[-1]

        result_dict = {
            "last_pressure_drop": last_pressure_drop,
            #"time_steps": time_steps,
            #"pressure_drop": pressure_drop
        }
        return result_dict
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File {data_file} not found.")
    except IndexError:
        raise ValueError(f"Error: File {data_file} is empty or not formatted correctly.")
    except Exception as e:
        raise RuntimeError(f"Error processing file {data_file}: {e}")

def run(data_file):
    pressure_drop = extract_pressure_drop(data_file)


if __name__ == "__main__":
    if len(sys.argv) > 1:  # Check if an argument is provided
        argument = sys.argv[1]  # Get the first argument
        run(argument)
    else:
        print("No argument provided. Please provide one.")
