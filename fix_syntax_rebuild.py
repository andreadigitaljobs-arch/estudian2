
import os

app_path = 'app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
target_line_content = "st.markdown('<div class=\"footer-text\">Don't have an account?</div>', unsafe_allow_html=True)"
replacement_line = '            st.markdown("""<div class="footer-text">Don\'t have an account?</div>""", unsafe_allow_html=True)\n'

for i, line in enumerate(lines):
    if "Don't have an account?" in line and "st.markdown" in line:
        lines[i] = replacement_line
        found = True
        print(f"Fixed Syntax Error at line {i+1}")
        break

if found:
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: Syntax Error Patched (Rebuild Fix).")
else:
    print("ERROR: Could not find the syntax error line to patch.")
