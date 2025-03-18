import os
import csv
import analyze_porous_media

def main(job_id=None):
    base_dir = "generated_media"
    csv_filename = "processed_porous_media_database.csv"

    # Verify that the base directory exists
    if not os.path.exists(base_dir):
        print(f"Directory '{base_dir}' does not exist. Nothing to do.")
        return

    subfolders = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]

    for folder_name in subfolders:
        # Construct the path to generated.stl for this subfolder
        if job_id == None or job_id == folder_name:
            print(f"Folder name is {folder_name}")
            stl_path = os.path.join(base_dir, folder_name, "generated.stl")

            if os.path.exists(stl_path):
                print(f"Processing {stl_path}...")

                try:
                    # Run the analysis and get the results as a dictionary
                    result_dict = analyze_porous_media.run(stl_path)

                    # Add the results to the CSV database
                    add_dict_to_csv(result_dict, csv_filename, key_name=folder_name)

                    print(f"Processed and added results for {folder_name}.")

                except Exception as e:
                    print(f"Error processing '{stl_path}': {e}")
            else:
                print(f"No generated.stl found in {folder_name}, skipping...")

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

def run(job_id=None):
    main(job_id)
    return 1

if __name__ == "__main__":
    run()