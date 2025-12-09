import base64
import os

img_path = r"C:/Users/nombr/.gemini/antigravity/brain/77f96b02-9d0f-404a-abf3-9d78274ca303/uploaded_image_1_1765234751302.jpg"

if os.path.exists(img_path):
    with open(img_path, "rb") as f:
        data = f.read()
        b64_str = base64.b64encode(data).decode('utf-8')
        print(b64_str)
else:
    print("File not found")
