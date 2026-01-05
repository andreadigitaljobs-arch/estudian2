
import os

files = ["app.py", "database.py", "library_ui.py", "study_assistant.py", "requirements.txt"]

for f in files:
    try:
        with open(f, "rb") as fp:
            data = fp.read()
        
        if b'\x00' in data:
            print(f"Cleaning {f}...")
            clean = data.replace(b'\x00', b'')
            
            # Also ensure UTF-8
            # try:
            #     text = clean.decode('utf-8')
            # except:
            #     text = clean.decode('latin-1')
            # clean = text.encode('utf-8')

            with open(f, "wb") as fp:
                fp.write(clean)
            print("Fixed.")
    except Exception as e:
        print(f"Err {f}: {e}")
