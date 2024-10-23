import os
import cv2
from paddleocr import PPStructure, save_structure_res
from typing import List, Dict, Any

def process_table_structure(input_path: str, output_folder: str) -> List[Dict[Any, Any]]:
    """
    Process table structure from an image using PaddleOCR's PPStructure.
    
    Args:
        input_path: Path to the input image
        output_folder: Path to save the output results
        
    Returns:
        List of dictionaries containing table structure information
    """
    try:
        # Initialize the table engine
        table_engine = PPStructure(layout=False, show_log=True)
        
        # Read the image
        img = cv2.imread(input_path)
        if img is None:
            raise ValueError(f"Failed to read image at path: {input_path}")
            
        # Process the image
        result = table_engine(img)
        
        # Save the results
        file_name = os.path.basename(input_path).split('.')[0]
        save_structure_res(result, output_folder, file_name)
        
        # Remove the image data from result to make it serializable
        for line in result:
            line.pop('img', None)
            
        return result
        
    except Exception as e:
        print(f"Error processing table structure: {str(e)}")
        raise
