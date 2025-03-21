import os
import csv
import analyze_cfd_results
import argparse

def process_pressure_drops(job_id=None):
    base_dir = "generated_media"
    csv_filename = "processed_pressure_drops_database.csv"
    data_filename = 'pressure_drop.dat'

    # Verify that the base directory exists
    if not os.path.exists(base_dir):
        print(f"Directory '{base_dir}' does not exist. Nothing to do.")
        return

    # Get all subfolders in the base directory
    subfolders = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]

    for folder_name in subfolders:
        # Get the full path of the subfolder
        subfolder_path = os.path.join(base_dir, folder_name)

        if job_id == None or job_id == folder_name:
            # Search recursively for 'pressure_drop.dat' within the subfolder
            data_file = None
            for root, _, files in os.walk(subfolder_path):
                if data_filename in files:
                    data_file = os.path.join(root, data_filename)
                    break

            if data_file and os.path.exists(data_file):
                print(f"Processing {data_file}...")

                try:
                    # Run the analysis and get the results as a dictionary
                    result_dict = analyze_cfd_results.extract_pressure_drop(data_file)

                    # Add the results to the CSV database
                    add_dict_to_csv(result_dict, csv_filename, key_name=folder_name)

                    print(f"Processed and added results for {folder_name}.")

                except Exception as e:
                    print(f"Error processing '{data_file}': {e}")
            else:
                print(f"No {data_filename} found in {folder_name}, skipping...")


def add_dict_to_csv(data_dict, csv_filename, key_name):
    """
    Add a dictionary of porous media characteristics to a CSV file.
    If the CSV file does not exist, it is created with appropriate headers.
    """
    # Add the folder name as a unique identifier (e.g., "id")
    entry_dict = {"id": key_name}
    entry_dict.update(data_dict)

    # Determine headers based on dictionary keys
    headers = list(entry_dict.keys())

    # Check if the CSV file already exists
    file_exists = os.path.isfile(csv_filename)

    # Open the CSV file in append mode if it exists, otherwise write mode
    mode = 'a' if file_exists else 'w'

    with open(csv_filename, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        # If creating a new file, write the header
        if not file_exists:
            writer.writeheader()
        # Write the current dictionary entry
        writer.writerow(entry_dict)

def run(job_id = None):
    process_pressure_drops(job_id)
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-process CFD simulation results.")
    parser.add_argument("--job_id", type=int, required=True, help="Job ID to process.")

    args = parser.parse_args()
    run(job_id=args.job_id)