import torch
from transformers import AutoTokenizer, AutoModel, BitsAndBytesConfig
from PIL import Image
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

path = "OpenGVLab/InternVL2-40B"

# Define the quantization configuration
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0,
    llm_int8_has_fp16_weight=False,
)

model = AutoModel.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,
    quantization_config=quantization_config,
    low_cpu_mem_usage=True,
    trust_remote_code=True
).eval()
tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True, use_fast=False)

pixel_values = load_image('test_image.jpg').to(torch.bfloat16).cuda()
generation_config = dict(max_new_tokens=1024, do_sample=True)

question = '''<image>
You are an expert at processing images of tables. Your task is to meticulously extract every single cell and its corresponding text from the table image to reconstruct it as an HTML table. Follow these guidelines:

1. Ensure 100% accuracy in cell extraction and text recognition.
2. Maintain the correct order of cells, especially when one cell spans multiple rows or columns.
3. Include empty cells in the HTML structure to preserve the table layout.
4. Use appropriate HTML tags for table structure (e.g., <table>, <tr>, <td>, <th>).
5. Implement colspan and rowspan attributes where necessary.
6. Preserve any formatting or styling present in the original table.

Only return the complete HTML code for the table, without any additional explanation or commentary.'''

response = model.chat(tokenizer, pixel_values, question, generation_config)
print(response)