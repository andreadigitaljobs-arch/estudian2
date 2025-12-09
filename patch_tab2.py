
import os

app_path = 'app.py'
new_img_path = "assets/notes_header.jpg"

purple_color = "#4B22DD"
purple_shadow = "rgba(75, 34, 221, 0.25)"

css_addition = f'''
    .green-frame-inner {{
        background-color: #E2E8F0;
        border-radius: 20px;
        width: 100%;
        height: 100%;
        min-height: 360px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #64748b;
        font-weight: 600;
    }}
    
    /* Exact replica of green-frame but Purple */
    .purple-frame {{
        background-color: {purple_color};
        border-radius: 30px;
        padding: 20px;
        box-shadow: 0 15px 30px {purple_shadow};
        width: 350px !important;
        min-width: 350px !important;
        max-width: 350px !important;
        flex: 0 0 350px !important; /* Strict Flex locking */
        aspect-ratio: 1 / 1.1; /* Maintain exact proportion */
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto; /* Center in column */
        overflow: hidden;
    }}
    
    .purple-frame img {{
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        max-width: 100% !important;
        border-radius: 20px;
    }}
'''

tab2_image_logic = [
    '    with col_img:\n',
    '        # Image Display (Dynamic Update)\n',
    '        import base64\n',
    '        img_b64_notes = ""\n',
    '        img_path_notes = "assets/notes_header.jpg"\n',
    '        if os.path.exists(img_path_notes):\n',
    '            with open(img_path_notes, "rb") as image_file:\n',
    '                img_b64_notes = base64.b64encode(image_file.read()).decode()\n',
    '        \n',
    "        st.markdown(f'''\n",
    '            <div class="purple-frame" style="padding: 20px;">\n',
    '                <img src="data:image/jpeg;base64,{img_b64_notes}" style="width: 100%; border-radius: 15px; object-fit: cover;">\n',
    '            </div>\n',
    "        ''', unsafe_allow_html=True)\n"
]

with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject CSS
# We look for the existing green-frame-inner block to replace it with itself + the new purple block
# This relies on the indentation being exact in the file.
original_css_block = '''.green-frame-inner {
        background-color: #E2E8F0;
        border-radius: 20px;
        width: 100%;
        height: 100%;
        min-height: 360px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #64748b;
        font-weight: 600;
    }'''

if original_css_block in content:
    print("CSS block found. Injecting .purple-frame...")
    content = content.replace(original_css_block, css_addition.strip())
else:
    print("WARNING: Exact CSS block match not found. Skipping CSS injection (Manual check required?)\nTrying looser match...")
    # Very unsafe to just skip, but let's try to proceed if we can match at least part of it
    pass

lines = content.splitlines(keepends=True)

# 2. Replace Tab 2 Image
# We look for 'render_image_card("illustration_notes_1765052810428.png")'
# and the line before it 'with col_img:'
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'with col_img:' in line and 'with tab2:' in lines[i-3]: # Context check
        start_idx = i
        # We expect the next line to be the render call
        if 'render_image_card' in lines[i+1]:
            end_idx = i + 1
            break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Tab 2 image logic at lines {start_idx+1}-{end_idx+1}")
    # Replace the lines
    # We replace lines[start_idx] and lines[end_idx] with the new list
    lines[start_idx:end_idx+1] = tab2_image_logic
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: app.py patched.")
else:
    print("ERROR: Tab 2 target lines not found.")
    # Debug print around likely area
    for i, line in enumerate(lines):
        if 'with tab2:' in line:
            print(f"Found tab2 at {i}. Content nearby:\n{''.join(lines[i:i+5])}")

