
import os

file_path = r"c:/Users/nombr/.gemini/antigravity/playground/hidden-glenn/library_ui.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Target Lines: 442 to End (1-indexed) -> Index 441 to End
start_index = 441

# Indent
new_lines = lines[:start_index]
for line in lines[start_index:]:
    if line.strip(): # Only indent if not empty
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("Indentation complete.")
