import numpy as np
import pandas as pd
from paddleocr import PaddleOCR
import json
import os
from table_ocr.utils.table_extraction import extract_table_from_ocr

print("Initializing PaddleOCR...")
paddle_ocr = PaddleOCR(use_angle_cls=True)
print("PaddleOCR initialized.")


def text_box_from_ocr(image_path) -> list[tuple[tuple[float, float, float, float], str]]:
    """Given an image path, returns a list of tuple of box(x, y, w, h) and text"""

    def standardize_box(coords):
        a, _, c, _ = np.array(coords)
        x, y = a
        w, h = c - a

        return x, y, w, h

    result = paddle_ocr.ocr(image_path, cls=True)

    return [(standardize_box(box), text) for box, (text, _) in result[0]]


def extract_table(image_path, output_dir='.') -> pd.DataFrame:
    ocr = text_box_from_ocr(image_path)
    table = extract_table_from_ocr(ocr)
    
    # Save OCR results and table as JSON files
    ocr_path = os.path.join(output_dir, 'ocr_results.json')
    table_path = os.path.join(output_dir, 'table_data.json')
    
    with open(ocr_path, 'w') as f:
        json.dump(ocr, f)
    
    table.to_json(table_path, orient='split')
    
    return table

def main():
    print("Starting OCR")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "resources/table_lg.png")
    table = extract_table(image_path=image_path)
    print(table)

if __name__ == "__main__":
    main()
