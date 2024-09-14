from PyPDF2 import PdfReader, PdfWriter
import io
import base64
from typing import List, Dict, Union

def split_pdf_bytes(pdf_bytes: bytes, pages_per_split: int) -> List[Dict[str, Union[int, str]]]:
    split_pdfs = []
    
    with io.BytesIO(pdf_bytes) as pdf_file:
        reader = PdfReader(pdf_file)
        total_pages = len(reader.pages)
        
        for i in range(0, total_pages, pages_per_split):
            start_page = i
            end_page = min(i + pages_per_split, total_pages)
            
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])
            
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            
            base64_pdf = base64.b64encode(output.getvalue()).decode()
            split_pdfs.append({
                "split_number": i//pages_per_split + 1,
                "base64_pdf": base64_pdf
            })
    
    return split_pdfs