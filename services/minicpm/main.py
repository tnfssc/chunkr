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
    # Plain texts OCR
    plain_ocr_result = model.chat(tokenizer, image_file, ocr_type='ocr')
    
    # Format texts OCR
    format_ocr_result = model.chat(tokenizer, image_file, ocr_type='format')
    
    # Fine-grained OCR
    fine_grained_ocr_result = model.chat(tokenizer, image_file, ocr_type='ocr', ocr_box='')
    fine_grained_format_result = model.chat(tokenizer, image_file, ocr_type='format', ocr_box='')
    fine_grained_color_ocr_result = model.chat(tokenizer, image_file, ocr_type='ocr', ocr_color='')
    fine_grained_color_format_result = model.chat(tokenizer, image_file, ocr_type='format', ocr_color='')
    
    # Multi-crop OCR
    multi_crop_ocr_result = model.chat_crop(tokenizer, image_file, ocr_type='ocr')
    multi_crop_format_result = model.chat_crop(tokenizer, image_file, ocr_type='format')
    
    # Render the formatted OCR results
    render_result = model.chat(tokenizer, image_file, ocr_type='format', render=True, save_render_file='./demo.html')
    
    return {
        'plain_ocr': plain_ocr_result,
        'format_ocr': format_ocr_result,
        'fine_grained_ocr': fine_grained_ocr_result,
        'fine_grained_format': fine_grained_format_result,
        'fine_grained_color_ocr': fine_grained_color_ocr_result,
        'fine_grained_color_format': fine_grained_color_format_result,
        'multi_crop_ocr': multi_crop_ocr_result,
        'multi_crop_format': multi_crop_format_result,
        'render': render_result
    }

def main():
    model, tokenizer = load_model_and_tokenizer()
    
    image_file = 'table_image.jpg'  # Replace with your image file path
    
    results = process_image(model, tokenizer, image_file)
    
    for key, value in results.items():
        print(f"\n{key.replace('_', ' ').title()} result:")
        print(value)

if __name__ == "__main__":
    main()