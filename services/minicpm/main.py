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
    def latex_escape(text):
        return text.replace('\\', '\\textbackslash{}').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}').replace('~', '\\textasciitilde{}').replace('^', '\\textasciicircum{}')

    def format_result(title, result):
        escaped_result = latex_escape(result)
        return f"\\subsection{{{title}}}\n\\begin{{verbatim}}\n{escaped_result}\n\\end{{verbatim}}\n"

    results = {
        'Plain OCR': model.chat(tokenizer, image_file, ocr_type='ocr'),
        'Format OCR': model.chat(tokenizer, image_file, ocr_type='format'),
        'Fine-grained OCR': model.chat(tokenizer, image_file, ocr_type='ocr', ocr_box=''),
        'Fine-grained Format': model.chat(tokenizer, image_file, ocr_type='format', ocr_box=''),
        'Fine-grained Color OCR': model.chat(tokenizer, image_file, ocr_type='ocr', ocr_color=''),
        'Fine-grained Color Format': model.chat(tokenizer, image_file, ocr_type='format', ocr_color=''),
        'Multi-crop OCR': model.chat_crop(tokenizer, image_file, ocr_type='ocr'),
        'Multi-crop Format': model.chat_crop(tokenizer, image_file, ocr_type='format'),
    }

    latex_output = "\\documentclass{article}\n\\usepackage{verbatim}\n\\begin{document}\n\n\\section{OCR Results}\n"
    for title, result in results.items():
        latex_output += format_result(title, result)

    # Render the formatted OCR results
    render_result = model.chat(tokenizer, image_file, ocr_type='format', render=True, save_render_file='./demo.html')
    latex_output += f"\\subsection{{Rendered Result}}\nSaved as: ./demo.html\n"

    latex_output += "\\end{document}"
    return latex_output

def main():
    model, tokenizer = load_model_and_tokenizer()
    
    image_file = 'table_image.jpg'  # Replace with your image file path
    
    latex_results = process_image(model, tokenizer, image_file)
    
    # Print the LaTeX output
    print(latex_results)

if __name__ == "__main__":
    main()