
import os

target_files = ["study_assistant.py", "database.py"]

for filename in target_files:
    try:
        if not os.path.exists(filename):
            continue
            
        print(f"Checking {filename}...")
        with open(filename, "rb") as f:
            content = f.read()
            
        if b'\x00' in content:
            print(f"⚠️ Null bytes found in {filename}. Cleaning...")
            clean_content = content.replace(b'\x00', b'')
            # Try to decode to ensure text validity
            text = clean_content.decode('utf-8', errors='ignore')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ {filename} fixed.")
        else:
            print(f"✅ {filename} is clean.")
            
    except Exception as e:
        print(f"Error processing {filename}: {e}")
