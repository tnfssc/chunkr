from lmdeploy import pipeline, TurbomindEngineConfig
from lmdeploy.vl import load_image

model = 'OpenGVLab/InternVL2-40B'
image = load_image('test_image.jpg')
pipe = pipeline(model, backend_config=TurbomindEngineConfig(session_len=8192))
question = '''<image>
You are an expert at processing images of tables. Your task is to meticulously extract every single cell and its corresponding text from the table image to reconstruct it as an HTML table. Follow these guidelines:

1. Ensure 100% accuracy in cell extraction and text recognition.
2. Maintain the correct order of cells, especially when one cell spans multiple rows or columns.
3. Include empty cells in the HTML structure to preserve the table layout.
4. Use appropriate HTML tags for table structure (e.g., <table>, <tr>, <td>, <th>).
5. Implement colspan and rowspan attributes where necessary.
6. Preserve any formatting or styling present in the original table.

Only return the complete HTML code for the table, without any additional explanation or commentary.'''
response = pipe((question, image))
print(response.text)