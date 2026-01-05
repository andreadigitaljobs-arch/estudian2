
import os

files = ["app.py", "library_ui.py", "database.py"]

for filename in files:
    try:
        with open(filename, "rb") as f:
            raw = f.read()
        
        # Decode/Encode cycle to normalize
        try:
            text = raw.decode("utf-8")
        except:
            text = raw.decode("cp1252", errors="replace")
            print(f"Converted {filename} from CP1252/Binary to UTF-8")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
            
    except Exception as e:
        print(f"Error {filename}: {e}")
