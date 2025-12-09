
import os

app_path = 'app.py'

# DEBUG PATCH: Force the background to be bright RED to prove to the user we are editing the live file.
# We will also inject a text "DEBUG MODE ACTIVE" clearly.

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Aggressively override the body background in the CSS block
    if ".stApp { background-color: white !important; }" in line:
        new_lines.append(".stApp { background-color: #FFE5E5 !important; } /* DEBUG RED TINT */\n")
    elif '<div class="login-title">Log in to your account</div>' in line:
        new_lines.append('                <div style="background: red; color: white; padding: 5px; font-weight: bold;">⚠️ DEBUG: UPDATE CONFIRMED ⚠️</div>\n')
        new_lines.append(line)
    else:
        new_lines.append(line)

with open(app_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("SUCCESS: Applied Visual Debug Markers (Red Background + Warning Text).")
