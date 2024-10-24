import os
import base64
import requests
import json
from typing import List, Dict, Any
from enum import Enum
from datetime import datetime

class ModelType(Enum):
    OPENGV_LOCAL = "OpenGVLab/Mini-InternVL-Chat-4B-V1-5"
    REMOTE_LLM = "remote_llm"  # Replace with actual model name from config if needed

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_opengv(image_path: str) -> str:
    try:
        base64_image = encode_image_to_base64(image_path)
        
        payload = {
            "model": ModelType.OPENGV_LOCAL.value,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Convert this table into HTML format with 100% accuracy. Create an exact replica of the table, ensuring every single cell, row, and column is included. Use <table style='border-collapse: collapse; width: 100%;'>, <tr>, <td style='border: 1px solid black; padding: 8px;'> tags. For header cells, use <th style='border: 1px solid black; padding: 8px; background-color: #f2f2f2;'>. Copy all text content verbatim, preserving all numbers, punctuation, and formatting exactly as shown. Do not summarize or omit any information. If the image doesn't contain a table, output 'No table found in image.'"
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }

        response = requests.post(
            "http://localhost:8000/v1/chat/completions",
            json=payload
        )
        
        print(f"Raw response: {response.text}")
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                if isinstance(response_json, dict):
                    return response_json["choices"][0]["message"]["content"]
                elif isinstance(response_json, str):
                    return response_json
            except json.JSONDecodeError:
                return response.text
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error processing image: {str(e)}"

def process_image_remote(image_path: str, config: Dict[str, str]) -> str:
    try:
        base64_image = encode_image_to_base64(image_path)
        
        payload = {
            "model": config["model"],
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Convert this table into HTML format..."  # existing prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 8000,
            "temperature": 0.0
        }

        response = requests.post(
            f"{config['url']}/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['key']}"
            },
            json=payload
        )
        
        if response.status_code == 200:
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error processing image: {str(e)}"

def main(input_dir: str, output_base_dir: str, model_type: ModelType, config: Dict[str, str] = None):
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = model_type.value.split('/')[-1] if model_type == ModelType.OPENGV_LOCAL else "remote_llm"
    output_dir = os.path.join(output_base_dir, f"{timestamp}_{model_name}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each image
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_dir, filename)
            
            # Process the image with selected model
            result = (
                process_image_opengv(image_path)
                if model_type == ModelType.OPENGV_LOCAL
                else process_image_remote(image_path, config)
            )
            
            # Save the result
            output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.html")
            with open(output_file, 'w') as f:
                f.write(result)
            
            print(f"Processed {filename} -> {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process images using vLLM API")
    parser.add_argument("--input-dir", default="./input", help="Input directory containing images")
    parser.add_argument("--output-dir", default="./output", help="Output directory for results")
    parser.add_argument("--model", choices=["local", "remote"], default="local", help="Model to use")
    parser.add_argument("--config", help="Path to config file for remote model")
    args = parser.parse_args()
    
    config = None
    if args.model == "remote":
        if not args.config:
            raise ValueError("Config file path required for remote model")
        with open(args.config) as f:
            config = json.load(f)
    
    model_type = ModelType.OPENGV_LOCAL if args.model == "local" else ModelType.REMOTE_LLM
    main(args.input_dir, args.output_dir, model_type, config)
