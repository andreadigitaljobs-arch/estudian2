
try:
    with open("study_assistant.py", "rb") as f:
        data = f.read(100)
    print(f"BYTES: {data}")
    print(f"DECODED: {data.decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"ERROR: {e}")
