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
    # Fine-grained OCR
    fine_grained_result = model.chat(tokenizer, image_file, ocr_type='format', ocr_box='')
    
    # Multi-crop OCR
    multi_crop_result = model.chat_crop(tokenizer, image_file, ocr_type='format')
    
    return fine_grained_result, multi_crop_result

def main():
    model, tokenizer = load_model_and_tokenizer()
    
    image_file = 'table_image.jpg'  # Replace with your image file path
    
    fine_grained_result, multi_crop_result = process_image(model, tokenizer, image_file)
    
    print("Fine-grained OCR result:")
    print(fine_grained_result)
    print("\nMulti-crop OCR result:")
    print(multi_crop_result)

if __name__ == "__main__":
    main()