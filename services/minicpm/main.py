import torch
from transformers import AutoTokenizer, AutoModel
from PIL import Image

def load_model_and_tokenizer():
    # Check CUDA availability and set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"GPU model: {torch.cuda.get_device_name(0)}")

    tokenizer = AutoTokenizer.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True)
    model = AutoModel.from_pretrained('ucaslcl/GOT-OCR2_0', trust_remote_code=True, low_cpu_mem_usage=True, device_map='auto', use_safetensors=True, pad_token_id=tokenizer.eos_token_id)
    return model.eval().to(device), tokenizer

def process_image(model, tokenizer, image_file):
    # Only use Format OCR
    format_ocr_result = model.chat(tokenizer, image_file, ocr_type='format')
    return format_ocr_result

def main():
    model, tokenizer = load_model_and_tokenizer()
    
    image_file = 'table_image.jpg'  # Replace with your image file path
    
    ocr_result = process_image(model, tokenizer, image_file)
    
    # Print the OCR result
    print(ocr_result)

if __name__ == "__main__":
    main()