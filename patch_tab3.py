
import os

app_path = 'app.py'
new_img_path = "assets/study_guide_header.jpg"

tab3_image_logic = [
    '    with col_img:\n',
    '        # Image Display (Dynamic Update)\n',
    '        import base64\n',
    '        img_b64_guide = ""\n',
    '        img_path_guide = "assets/study_guide_header.jpg"\n',
    '        if os.path.exists(img_path_guide):\n',
    '            with open(img_path_guide, "rb") as image_file:\n',
    '                img_b64_guide = base64.b64encode(image_file.read()).decode()\n',
    '        \n',
    "        st.markdown(f'''\n",
    '            <div class="purple-frame" style="padding: 20px;">\n',
    '                <img src="data:image/jpeg;base64,{img_b64_guide}" style="width: 100%; border-radius: 15px; object-fit: cover;">\n',
    '            </div>\n',
    "        ''', unsafe_allow_html=True)\n"
]

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace Tab 3 Image
# We look for 'render_image_card("illustration_guide_1765052821852.png")'
# and the line before it 'with col_img:'
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'with col_img:' in line and 'with tab3:' in lines[i-3]: # Context check
        start_idx = i
        # We expect the next line to be the render call
        if 'render_image_card' in lines[i+1]:
            end_idx = i + 1
            break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Tab 3 image logic at lines {start_idx+1}-{end_idx+1}")
    # Replace the lines
    lines[start_idx:end_idx+1] = tab3_image_logic
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: app.py patched for Tab 3.")
else:
    print("ERROR: Tab 3 target lines not found.")
    # Debug print around likely area
    for i, line in enumerate(lines):
        if 'with tab3:' in line:
            print(f"Found tab3 at {i}. Content nearby:\n{''.join(lines[i:i+5])}")
