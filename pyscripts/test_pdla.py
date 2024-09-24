
import unittest
import requests
import os
import json
from pathlib import Path
from annotate import draw_bounding_boxes
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
import uuid
import time
import numpy as np
import glob
import shutil
import csv
from PyPDF2 import PdfReader, PdfWriter
import concurrent.futures

dotenv.load_dotenv(override=True)

class GrowthFunc(Enum):
    LINEAR = 'linear'
    EXPONENTIAL = 'exponential'
    LOGARITHMIC = 'logarithmic'
    QUADRATIC = 'quadratic'
    CUBIC = 'cubic'

class TestPDLAServer(unittest.TestCase):
    BASE_URL = os.getenv("PDLASERVER_URL")
    MAX_WORKERS = 4  # Adjust this value based on your system's capabilities

    def setUp(self):
        print("Setting up test environment...")
        self.input_folder = Path(__file__).parent / "input"
        self.output_folder = Path(__file__).parent / "output"
        if not self.input_folder.exists() or not self.input_folder.is_dir():
            raise FileNotFoundError(f"Input folder not found at {self.input_folder}")
        if not self.output_folder.exists():
            self.output_folder.mkdir(parents=True)
        
        self.test_pdfs = list(self.input_folder.glob("*.pdf"))
        if not self.test_pdfs:
            raise FileNotFoundError(f"No PDF files found in {self.input_folder}")
        print(f"Found {len(self.test_pdfs)} PDF files for testing.")

    def process_pdf(self, pdf_path):
        url = f"{self.BASE_URL}/"
        print(f"Processing PDF file: {pdf_path}")
        with open(pdf_path, "rb") as pdf_file:
            files = {"file": (pdf_path.name, pdf_file, "application/pdf")}
            data = {"fast": "false", "density": 72, "extension": "jpeg"}
            
            print(f"Sending POST request to PDLA server for {pdf_path.name}...")
            response = requests.post(url, files=files, data=data)
        
        print(f"Response status code for {pdf_path.name}: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        json_response = response.json()
        print(f"Received JSON response with {len(json_response)} items for {pdf_path.name}.")
        self.assertIsInstance(json_response, list)
        self.assertTrue(len(json_response) > 0)
        
        # Check if the response contains expected fields
        first_item = json_response[0]
        expected_fields = ["left", "top", "width", "height", "page_number", "page_width", "page_height", "text", "type"]
        for field in expected_fields:
            print(f"Checking for field: {field} in {pdf_path.name}")
            self.assertIn(field, first_item)
        
        # Save output to JSON file
        output_json_path = self.output_folder / f"{pdf_path.stem}_json.json"
        print(f"Saving JSON output to: {output_json_path}")
        with open(output_json_path, "w") as json_file:
            json.dump(json_response, json_file, indent=2)
        
        # Annotate the PDF
        output_pdf_path = self.output_folder / f"{pdf_path.stem}_Annotated.pdf"
        print(f"Annotating PDF and saving to: {output_pdf_path}")
        draw_bounding_boxes(str(pdf_path), json_response, str(output_pdf_path))
        print(f"Finished processing {pdf_path.name}")

    def test_pdla_high_quality_extraction(self):
        url = f"{self.BASE_URL}/"
        print(f"Testing PDLA high quality extraction at URL: {url}")
        
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = [executor.submit(self.process_pdf, pdf_path) for pdf_path in self.test_pdfs]
            for future in as_completed(futures):
                future.result()  # This will raise any exceptions that occurred during execution

    def throughput_test(self, growth_func: GrowthFunc, start_page: int, end_page: int, num_pdfs: int):
        print("Starting throughput test...")
        if not isinstance(growth_func, GrowthFunc):
            raise ValueError("growth_func must be an instance of GrowthFunc Enum")

        run_id = f"run_{uuid.uuid4().hex}"
        run_dir = self.input_folder / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created run directory: {run_dir}")

        original_pdf = self.test_pdfs[0]
        pdf_test_paths = []

        # Create a new PDF with only the specified page range
        base_pdf_writer = PdfWriter()
        with open(original_pdf, 'rb') as file:
            pdf_reader = PdfReader(file)
            for page_num in range(start_page - 1, end_page):
                base_pdf_writer.add_page(pdf_reader.pages[page_num])

        base_pdf_path = run_dir / f"{original_pdf.stem}_base.pdf"
        with open(base_pdf_path, 'wb') as output_file:
            base_pdf_writer.write(output_file)

        # Create all test PDFs
        for i in range(num_pdfs):
            if growth_func == GrowthFunc.LINEAR:
                multiplier = i + 1
            elif growth_func == GrowthFunc.EXPONENTIAL:
                multiplier = 2 ** i
            elif growth_func == GrowthFunc.LOGARITHMIC:
                multiplier = max(1, int(np.log2(i + 2)))
            elif growth_func == GrowthFunc.QUADRATIC:
                multiplier = (i + 1) ** 2
            elif growth_func == GrowthFunc.CUBIC:
                multiplier = (i + 1) ** 3
            else:
                raise ValueError("Unsupported growth function")

            test_pdf_name = f"{original_pdf.stem}_{multiplier}x.pdf"
            test_pdf_path = run_dir / test_pdf_name

            # Create the test PDF by duplicating the base PDF
            test_pdf_writer = PdfWriter()
            for _ in range(multiplier):
                with open(base_pdf_path, 'rb') as base_file:
                    base_reader = PdfReader(base_file)
                    for page in base_reader.pages:
                        test_pdf_writer.add_page(page)

            with open(test_pdf_path, 'wb') as output_file:
                test_pdf_writer.write(output_file)

            print(f"Created {test_pdf_path} with multiplier {multiplier}x")
            pdf_test_paths.append(test_pdf_path)

        # Process all created PDFs and log results
        csv_path = self.output_folder / f"throughput_results_{growth_func.value}_{run_id}.csv"
        fieldnames = ['PDF Name', 'Number of Pages', 'Processing Time (seconds)', 'Throughput (pages/sec)']
        
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            csvfile.flush()

            for pdf_path in pdf_test_paths:
                start_time = time.time()
                self.process_pdf(pdf_path)
                end_time = time.time()
                
                processing_time = end_time - start_time
                num_pages = len(PdfReader(pdf_path).pages)
                throughput = num_pages / processing_time
                
                row_data = {
                    'PDF Name': pdf_path.name,
                    'Number of Pages': num_pages,
                    'Processing Time (seconds)': processing_time,
                    'Throughput (pages/sec)': throughput
                }
                
                writer.writerow(row_data)
                csvfile.flush()  # Ensure data is written to file
                print(f"Processed {pdf_path.name}: {num_pages} pages in {processing_time:.2f} seconds. Throughput: {throughput:.2f} pages/sec")

        print(f"Throughput test results saved to {csv_path}")
        print("Throughput test completed successfully.")
    def test_parallel_requests(self, num_parallel_requests=5):
        print("Starting parallel requests test...")
        input_folder = Path("input")
        pdf_files = list(input_folder.glob("*.pdf"))
        
        if not pdf_files:
            raise ValueError("No PDF files found in the input folder.")
        
        # Use the first PDF file as the source
        source_pdf = pdf_files[0]
        print(f"Using source PDF: {source_pdf}")

        # Create temporary directory for duplicates
        temp_dir = self.output_folder / "temp_parallel_test"
        temp_dir.mkdir(exist_ok=True)

        # Create duplicates
        test_pdfs = []
        for i in range(num_parallel_requests):
            new_path = temp_dir / f"test_pdf_{i}.pdf"
            shutil.copy(source_pdf, new_path)
            test_pdfs.append(new_path)
        
        print(f"Created {len(test_pdfs)} duplicate PDFs for testing")

        def process_pdf_wrapper(pdf_path):
            start_time = time.time()
            try:
                response = self.process_pdf(pdf_path)
                end_time = time.time()
                processing_time = end_time - start_time
                num_pages = len(PdfReader(pdf_path).pages)
                throughput = num_pages / processing_time
                
                if response.status_code != 200:
                    error_message = f"Response status code for {pdf_path.name}: {response.status_code}\n"
                    error_message += f"Request URL: {response.request.url}\n"
                    error_message += f"Request method: {response.request.method}\n"
                    error_message += f"Request headers: {response.request.headers}\n"
                    error_message += f"Response headers: {response.headers}\n"
                    error_message += f"Response content: {response.text}\n"
                    print(error_message)
                    return pdf_path.name, processing_time, num_pages, throughput, error_message
                
                return pdf_path.name, processing_time, num_pages, throughput, None
            except Exception as e:
                end_time = time.time()
                processing_time = end_time - start_time
                error_message = f"Error processing {pdf_path.name}: {str(e)}"
                print(error_message)
                return pdf_path.name, processing_time, 0, 0, error_message
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_parallel_requests) as executor:
            futures = [executor.submit(process_pdf_wrapper, pdf) for pdf in test_pdfs]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Log results
        csv_path = self.output_folder / f"parallel_requests_results_{num_parallel_requests}_requests.csv"
        fieldnames = ['PDF Name', 'Processing Time (seconds)', 'Number of Pages', 'Throughput (pages/sec)', 'Error']
        
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pdf_name, processing_time, num_pages, throughput, error in results:
                row_data = {
                    'PDF Name': pdf_name,
                    'Processing Time (seconds)': processing_time,
                    'Number of Pages': num_pages,
                    'Throughput (pages/sec)': throughput,
                    'Error': error if error else 'None'
                }
                writer.writerow(row_data)
                if error:
                    print(f"Error processing {pdf_name}: {error}")
                else:
                    print(f"Processed {pdf_name} in {processing_time:.2f} seconds. Throughput: {throughput:.2f} pages/sec")
        
        print(f"Parallel requests test results saved to {csv_path}")
        print("Parallel requests test completed successfully.")

        # Clean up temporary files
        shutil.rmtree(temp_dir)
        print("Cleaned up temporary test files")

if __name__ == "__main__":
    tester = TestPDLAServer()
    tester.setUp()
    # Example of running throughput_test with user-provided parameters
    # tester.throughput_test(GrowthFunc.LINEAR, start_page=18, end_page=88, num_pdfs=5)
    tester.test_parallel_requests(num_parallel_requests=2)