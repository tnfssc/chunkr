import argparse
import os
import requests
import subprocess
import tarfile

MODEL_DIR = "../models"
ONNX_DIR = "../onnx"

models = {
    "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar",
    "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_rec_infer.tar",
    # "https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar"
}

def download_and_extract_model(force_download: bool, url: str, model_name: str) -> str:
    tar_filename = os.path.join(MODEL_DIR, f"{model_name}.tar")
    if not force_download and os.path.exists(tar_filename):
        return os.path.join(MODEL_DIR, model_name)
    
    response = requests.get(url)
    response.raise_for_status()

    with open(tar_filename, "wb") as file:
        file.write(response.content)

    with tarfile.open(tar_filename, "r") as tar:
        tar.extractall(path=MODEL_DIR)
        
    os.remove(tar_filename)

    return os.path.join(MODEL_DIR, model_name)

def convert_to_onnx(model_path: str, model_name: str):
    subprocess.run([
        "uv",
        "run",
        "paddle2onnx",
        "--model_dir", model_path,
        "--model_filename", "inference.pdmodel",
        "--params_filename", "inference.pdiparams",
        "--save_file", os.path.join(ONNX_DIR, f"{model_name}.onnx")
    ])

def main(force_download: bool):
    for url in models:
        model_name = os.path.splitext(url.split("/")[-1])[0]
        print(f"Downloading and converting {model_name}...")
        model_path = download_and_extract_model(force_download, url, model_name)
        convert_to_onnx(model_path, model_name)

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--force_download", action="store_true")
    args = args.parse_args()
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(ONNX_DIR, exist_ok=True)
    main(args.force_download)
