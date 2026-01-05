
import os
import glob

print("SCANNING...")
for ext in ["*.py", "*.txt"]:
    for f in glob.glob(ext):
        try:
            with open(f, "rb") as fp:
                data = fp.read()
            if b'\x00' in data:
                count = data.count(b'\x00')
                print(f"❌ DEAD: {f} ({count} nulls)")
            else:
                pass
        except Exception as e:
            print(f"Error {f}: {e}")
