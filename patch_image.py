
import os

app_path = 'app.py'
new_img_path = "assets/transcriptor_header_v2.jpg"

new_code_block = [
    '        # Image Display (Dynamic Update)\n',
    '        import base64\n',
    '        img_path = "assets/transcriptor_header_v2.jpg"\n',
    '        img_b64 = ""\n',
    '        if os.path.exists(img_path):\n',
    '            with open(img_path, "rb") as image_file:\n',
    '                img_b64 = base64.b64encode(image_file.read()).decode()\n',
    '        \n',
    "        st.markdown(f'''\n",
    '            <div class="green-frame" style="padding: 20px;">\n',
    '                <img src="data:image/jpeg;base64,{img_b64}" style="width: 100%; border-radius: 15px; object-fit: cover;">\n',
    '            </div>\n',
    "        ''', unsafe_allow_html=True)\n"
]

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ensure we are targeting the right lines
# 980 (index 979) should contain st.markdown
# 989 (index 988) should contain unsafe_allow_html
print(f"Line 980 check: {lines[979]}")
print(f"Line 989 check: {lines[988]}")

if "st.markdown" in lines[979] and "unsafe_allow_html" in lines[988]:
    # Replace lines 979 to 988 (inclusive) -> 979:989 slice
    lines[979:989] = new_code_block
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: app.py patched.")
else:
    print("ERROR: Targeting verification failed. Lines do not match expected content.")
