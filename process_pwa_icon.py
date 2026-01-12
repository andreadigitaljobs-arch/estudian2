from PIL import Image
import base64
import io
import os

# Source and Destination
source_path = r"C:/Users/nombr/.gemini/antigravity/brain/cc151737-584a-4382-93aa-bfa49078d786/uploaded_image_1768219198023.jpg"
dest_dir = r"c:/Users/nombr/.gemini/antigravity/playground/hidden-glenn/assets"
dest_path = os.path.join(dest_dir, "pwa_icon.png")

try:
    # Open and Resize
    img = Image.open(source_path)
    img = img.resize((512, 512), Image.Resampling.LANCZOS)
    
    # Ensure dir exists
    os.makedirs(dest_dir, exist_ok=True)
    
    # Save as PNG
    img.save(dest_path, "PNG")
    print(f"SUCCESS: Saved to {dest_path}")
    
    # Base64 Encode
    with open(dest_path, "rb") as image_file:
        b64_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    # Write Base64 to a text file for easy reading (avoid console spam)
    with open("pwa_icon_b64.txt", "w") as f:
        f.write(b64_string)
        
    print("SUCCESS: Base64 saved to pwa_icon_b64.txt")

except Exception as e:
    print(f"ERROR: {e}")
