import os
import shutil

def create_file_based_directories(input_folder: str, output_folder: str) -> None:
    """
    Creates a directory for each file in the input folder, named after the file,
    and copies the file into its directory.
    
    Args:
        input_folder (str): Path to the folder containing input files
        output_folder (str): Path to the output folder
    """
    # Check if input folder exists
    if not os.path.exists(input_folder):
        raise ValueError(f"Input folder '{input_folder}' does not exist")
    
    # Iterate through files in the input folder
    for filename in os.listdir(input_folder):
        # Get the full path of the file
        file_path = os.path.join(input_folder, filename)
            
        # Get file name without extension
        file_name = os.path.splitext(filename)[0]
        
        # Create directory with the same name as the file
        new_directory = os.path.join(output_folder, file_name)
        os.makedirs(new_directory, exist_ok=True)
        
        # Copy the file to its directory
        if not os.path.exists(file_path):
            destination = os.path.join(new_directory, 'image.jpg')
            shutil.copy2(file_path, destination)
