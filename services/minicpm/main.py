import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def load_image(image_file, input_size=448):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    pixel_values = transform(image).unsqueeze(0)
    return pixel_values

# Load the model
path = 'OpenGVLab/InternVL2-8B'
model = AutoModel.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    use_flash_attn=True,
    trust_remote_code=True
).eval().cuda()

tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True, use_fast=False)

# Load and preprocess the image
pixel_values = load_image('table_image.jpg').to(torch.bfloat16).cuda()

# Set up the generation config
generation_config = dict(
    max_new_tokens=4096,  # Increased from 1024 to 4096
    do_sample=True,  # Set to False for deterministic output
    temperature=0.1,  # Low temperature for more focused output
    top_k=1,          # Only consider the most likely token
    top_p=0.9,        # High top_p for more focused sampling
    num_beams=1       # Use greedy decoding
)

# Your prompt
question = '''<image>
You are an expert at processing images of tables. You can perfectly extract every single cell and the corresponding text from the table image to reconstruct it as an HTML table. You never miss any part of the table, and always maintain the correct order of the cells, especially when one cell maps to multiple rows or columns. You make sure that empty cells are also included. Only return the HTML code.'''

# Generate the response
response = model.chat(tokenizer, pixel_values, question, generation_config)

print(f'User: {question}\nAssistant: {response}')
