
import os

app_path = 'app.py'

tab4_image_logic = [
    '    with col_img:\n',
    '        # Image Display (Dynamic Update)\n',
    '        import base64\n',
    '        img_b64_quiz = ""\n',
    '        img_path_quiz = "assets/quiz_helper_header.jpg"\n',
    '        if os.path.exists(img_path_quiz):\n',
    '            with open(img_path_quiz, "rb") as image_file:\n',
    '                img_b64_quiz = base64.b64encode(image_file.read()).decode()\n',
    '        \n',
    "        st.markdown(f'''\n",
    '            <div class="purple-frame" style="padding: 20px;">\n',
    '                <img src="data:image/jpeg;base64,{img_b64_quiz}" style="width: 100%; border-radius: 15px; object-fit: cover;">\n',
    '            </div>\n',
    "        ''', unsafe_allow_html=True)\n"
]

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Replace Tab 4 Image
# We look for 'render_image_card("illustration_quiz_1765052844536.png")'
# and the line before it 'with col_img:'
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'with col_img:' in line and 'with tab4:' in lines[i-3]: # Context check
        start_idx = i
        # We expect the next line to be the render call
        if 'render_image_card' in lines[i+1]:
            end_idx = i + 1
            break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Tab 4 image logic at lines {start_idx+1}-{end_idx+1}")
    # Replace the lines
    lines[start_idx:end_idx+1] = tab4_image_logic
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: app.py patched for Tab 4.")
else:
    print("ERROR: Tab 4 target lines not found.")
    # Debug print around likely area
    for i, line in enumerate(lines):
        if 'with tab4:' in line:
            print(f"Found tab4 at {i}. Content nearby:\n{''.join(lines[i:i+5])}")
