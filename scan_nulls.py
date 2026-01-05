
import os
import glob

# Scan all .py files
files = glob.glob("*.py") + ["requirements.txt"]

print("SCANNING FOR NULL BYTES...")
for f in files:
    try:
        with open(f, "rb") as fp:
            content = fp.read()
            if b'\x00' in content:
                count = content.count(b'\x00')
                print(f"❌ CORRUPTED: {f} ({count} null bytes)")
            else:
                pass
                # print(f"✅ OK: {f}")
    except Exception as e:
        print(f"⚠️ Error reading {f}: {e}")

print("SCAN COMPLETE.")
