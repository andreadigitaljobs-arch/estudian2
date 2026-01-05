
import os
import codecs

filename = "study_assistant.py"

try:
    with open(filename, "rb") as f:
        raw_data = f.read()

    print(f"Read {len(raw_data)} bytes.")

    # Try decoding as UTF-8 first
    try:
        text = raw_data.decode("utf-8")
        print("Valid UTF-8 detected.")
    except UnicodeDecodeError:
        print("❌ Invalid UTF-8. Trying CP1252/Latin-1...")
        try:
            text = raw_data.decode("cp1252")
            print("✅ Decoded as CP1252.")
        except:
            text = raw_data.decode("latin-1", errors="replace")
            print("✅ Decoded as Latin-1 (fallback).")

    # Now write back as strict UTF-8
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    
    print("re-saved as UTF-8.")

except Exception as e:
    print(f"Error: {e}")
