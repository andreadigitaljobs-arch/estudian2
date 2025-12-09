
import os

app_path = 'app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

found = False
target_substring = "Don't have an account?"

for i, line in enumerate(lines):
    if target_substring in line and "st.markdown" in line:
        # Use a completely safe formatting for the replacement
        # Switching outer quotes to double quotes, and escaping inner single quote just in case
        lines[i] = '             st.markdown("<div class=\'signup-text\'>Don\'t have an account?</div>", unsafe_allow_html=True)\n'
        found = True
        print(f"Fixed Syntax Error at line {i+1}")
        break

if found:
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("SUCCESS: Syntax Error Patched.")
else:
    print("ERROR: Could not find the syntax error line to patch.")
