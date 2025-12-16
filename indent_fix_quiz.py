
import os

file_path = r"c:/Users/nombr/.gemini/antigravity/playground/hidden-glenn/app.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Target Lines: 2280 to 2348 (1-indexed) -> Index 2279 to 2347
# Slice [2279:2348] covers indices 2279...2347.

start_index = 2279
end_index = 2348

# Indent
new_lines = lines[:start_index]
for line in lines[start_index:end_index]:
    if line.strip(): # Only indent if not empty
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

new_lines.extend(lines[end_index:])

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print(f"Indentation complete for lines {start_index+1} to {end_index}.")
