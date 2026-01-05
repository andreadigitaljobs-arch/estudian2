
import os

target_files = ["study_assistant.py", "database.py", "library_ui.py", "app.py"]

for filename in target_files:
    try:
        if not os.path.exists(filename):
            print(f"Skipping {filename} (Not found)")
            continue
            
        # Read as binary to detect nulls
        with open(filename, "rb") as f:
            content = f.read()
            
        if b'\x00' in content:
            print(f"⚠️ Null bytes found in {filename} ({content.count(b'\x00')} instances). cleaning...")
            clean_content = content.replace(b'\x00', b'')
            
            # Write back
            with open(filename, "wb") as f:
                f.write(clean_content)
            print(f"✅ {filename} fixed.")
        else:
            print(f"✅ {filename} is clean.")
            
    except Exception as e:
        print(f"Error processing {filename}: {e}")
