
import os

files = ["database.py", "library_ui.py"]

for f in files:
    try:
        print(f"Sanitizing {f}...")
        with open(f, "rb") as fp:
            content = fp.read()
        
        if b'\x00' in content:
            clean = content.replace(b'\x00', b'')
            with open(f, "wb") as fp:
                fp.write(clean)
            print(f"✅ Fixed {f}")
        else:
            print(f"✨ {f} was already clean")
            
    except Exception as e:
        print(f"Error: {e}")
