# test.py
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
import psutil
import os
import gc

print(f"Available RAM: {psutil.virtual_memory().available / (1024 * 1024 * 1024):.2f} GB")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Total GPU memory: {torch.cuda.get_device_properties(0).total_memory / (1024 * 1024 * 1024):.2f} GB")
    print(f"Available GPU memory: {torch.cuda.memory_allocated(0) / (1024 * 1024 * 1024):.2f} GB")
else:
    print("CUDA is not available")

# Set environment variable for verbose logging
os.environ['TRANSFORMERS_VERBOSITY'] = 'info'

# Clear CUDA cache and run garbage collection
torch.cuda.empty_cache()
gc.collect()

try:
    if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 17 * (1024 ** 3):  # Check if GPU has more than 17GB
        device = "cuda"
    else:
        device = "cpu"
        print("Using CPU for model inference due to insufficient GPU memory or CUDA unavailability.")
    
    model = AutoModel.from_pretrained('openbmb/MiniCPM-V-2_6', 
                                      trust_remote_code=True,
                                      attn_implementation='sdpa', 
                                      torch_dtype=torch.bfloat16,
                                      low_cpu_mem_usage=True)
    model = model.eval().to(device)
    print(f"Model loaded successfully on {device}")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

tokenizer = AutoTokenizer.from_pretrained('openbmb/MiniCPM-V-2_6', trust_remote_code=True)

image = Image.open('table_image.jpg').convert('RGB')
question = 'You are an expert at processing images of tables. You can perfectly extract every single cell and the corresponding text from the table image to reconstruct it as an HTML table. You never miss any part of the table, not even a single cell. You make sure that empty cells are also included. Only return the HTML code.'
msgs = [{'role': 'user', 'content': [image, question]}]

res = model.chat(
    image=None,
    msgs=msgs,
    tokenizer=tokenizer,
    temperature=0.1,
    top_k=30,
    top_p=0.90
)

generated_text = ""
for new_text in res:
    generated_text += new_text
    print(new_text, flush=True, end='')
