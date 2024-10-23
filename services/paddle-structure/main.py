import argparse
import os
from src.initialize import create_file_based_directories
from src.ppstructure import process_table_structure

def main(input_dir: str, output_dir: str):
    create_file_based_directories(input_dir, output_dir)

    for file_dir in os.listdir(output_dir):
        process_table_structure(file_dir + '/image.jpg', file_dir)



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Process input and output directories")
    parser.add_argument("--input-dir", default="./input", help="Input directory path")
    parser.add_argument("--output-dir", default="./output", help="Output directory path")
    args = parser.parse_args()

    main(args.input_dir, args.output_dir)
