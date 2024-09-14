from fastapi import FastAPI, File, UploadFile, Form, Query
from pydantic import BaseModel
from typing import List, Dict
import base64
import json
import io
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
import math
import uvicorn
from concurrent.futures import ThreadPoolExecutor

try:
    from .split import split_pdf_bytes
except ImportError:
    from split import split_pdf_bytes

app = FastAPI()


class BoundingBox(BaseModel):
    left: float
    top: float
    width: float
    height: float
    page_number: int
    bb_id: str


class ConversionResponse(BaseModel):
    png_pages: List[Dict[str, str]]


@app.get("/")
def read_root():
    return {"message": "Welcome to the PDF to PNG converter API"}


@app.post("/convert", response_model=ConversionResponse)
async def convert_pdf_to_png(
    bounding_boxes: str = Form(...),  # Receive bounding_boxes as a JSON string
    file: UploadFile = File(...),
    dpi: int = Form(150)
):
    # Convert JSON string to list of BoundingBox
    bounding_boxes = [BoundingBox(**box) for box in json.loads(bounding_boxes)]
    png_pages = []

    pdf_bytes = await file.read()

    # Get PDF dimensions and DPI
    pdf = PdfReader(io.BytesIO(pdf_bytes))
    first_page = pdf.pages[0]
    pdf_width = float(first_page.mediabox.width)
    pdf_height = float(first_page.mediabox.height)

    # Convert PDF to images
    pdf_images = convert_from_bytes(pdf_bytes, dpi=dpi)

    for bounding_box in bounding_boxes:
        # PDF page numbers start from 1, but list indexing starts from 0
        img = pdf_images[bounding_box.page_number - 1]

        # Calculate scaling factor
        scale_x = img.width / pdf_width
        scale_y = img.height / pdf_height

        # Adjust bounding box coordinates
        left = math.floor(bounding_box.left * scale_x)
        top = math.floor(bounding_box.top * scale_y)
        right = math.ceil((bounding_box.left + bounding_box.width) * scale_x)
        bottom = math.ceil((bounding_box.top + bounding_box.height) * scale_y)

        # Crop image based on adjusted bounding box
        cropped_img = img.crop((left, top, right, bottom))

        # Convert to PNG
        buffer = io.BytesIO()
        cropped_img.save(buffer, format="PNG")
        png_data = buffer.getvalue()
        base64_png = base64.b64encode(png_data).decode()

        png_pages.append(
            {"bb_id": bounding_box.bb_id, "base64_png": base64_png}
        )

    return {"png_pages": png_pages}


@app.post("/split")
async def split_pdf(
    file: UploadFile = File(...),
    pages_per_split: int = Form(...)
):
    pdf_bytes = await file.read()
    split_pdfs = split_pdf_bytes(pdf_bytes, pages_per_split)
    return {"split_pdfs": split_pdfs}


@app.post("/convert_all_pages")
async def convert_all_pdf_pages(
    file: UploadFile = File(...),
    dpi: int = Form(300),
    format: str = Query("png", pattern="^(png|jpg)$"),
    split: bool = Form(True)
):
    pdf_bytes = await file.read()

    def process_page(page_data):
        if split:
            pdf_bytes = base64.b64decode(page_data["base64_pdf"])
            page_number = page_data["split_number"]
            first_page = last_page = 1
        else:
            page_number = page_data["page_number"]
            first_page = last_page = page_number

        img = convert_from_bytes(
            pdf_bytes, dpi=dpi, first_page=first_page, last_page=last_page)[0]
        buffer = io.BytesIO()
        if format == "jpg":
            img = img.convert("RGB")
            img.save(buffer, format="JPEG", optimize=True, quality=85)
        else:
            img.save(buffer, format="PNG", optimize=True)
        return {
            "page_number": page_number,
            "base64_image": base64.b64encode(buffer.getvalue()).decode(),
            "format": format
        }

    if split:
        split_pdfs = split_pdf_bytes(pdf_bytes, pages_per_split=1)
        page_data = split_pdfs
    else:
        total_pages = len(PdfReader(io.BytesIO(pdf_bytes)).pages)
        page_data = [{"page_number": i + 1} for i in range(total_pages)]

    with ThreadPoolExecutor() as executor:
        all_pages = list(executor.map(process_page, page_data))

    return {"pages": all_pages}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
