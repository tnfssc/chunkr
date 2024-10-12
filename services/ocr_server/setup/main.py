import argparse
import os
import requests
import subprocess
import tarfile

MODEL_DIR = "../models"

def download_table_rec(force_download: bool):
    url = "https://paddleocr.bj.bcebos.com/ppstructure/models/slanet/en_ppstructure_mobile_v2.0_SLANet_infer.tar"
    model_name = "en_ppstructure_mobile_v2.0_SLANet_infer"
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
    
    print("Table recognition model downloaded and extracted successfully.")

    return os.path.join(MODEL_DIR, model_name)

def convert_to_onnx(model_path: str):
    print(model_path)
    subprocess.run([
        "uv",
        "run",
        "paddle2onnx",
        "--model_dir", model_path,
        "--model_filename", "model.pdmodel",
        "--params_filename", "model.pdiparams",
        "--save_file", os.path.join(model_path, "model.onnx")
    ])


def main(force_download: bool):
    model_path = download_table_rec(force_download)
    convert_to_onnx(model_path)

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--force_download", action="store_true")
    args = args.parse_args()
    os.makedirs(MODEL_DIR, exist_ok=True)
    main(args.force_download)
