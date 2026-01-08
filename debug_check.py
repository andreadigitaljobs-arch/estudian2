import sys
import os

print("--- DIAGNOSTIC START ---")
print(f"Python Version: {sys.version}")

def check_import(name, critical=False):
    try:
        __import__(name)
        print(f"   [OK] {name} imported")
        return True
    except ImportError as e:
        level = "[CRITICAL]" if critical else "[WARNING]"
        print(f"   {level} {name} missing: {e}")
        return False
    except Exception as e:
        import traceback
        print(f"   [ERROR] Runtime error importing {name}: {e}")
        print(traceback.format_exc())
        return False

print("Check 1: Dependencies")
check_import("streamlit", critical=True)
check_import("google.generativeai", critical=True)
check_import("imageio_ffmpeg", critical=False)

print("Check 2: Local Modules")
sys.path.append(os.getcwd())
check_import("db_handler", critical=True)

# Verify upload_file_to_db specifically
try:
    import db_handler
    if hasattr(db_handler, 'upload_file_to_db'):
        print("   [OK] db_handler.upload_file_to_db exists")
    else:
        print("   [CRITICAL] db_handler.upload_file_to_db MISSING")
except: pass

print("Check 3: App Import (The Big One)")
if check_import("app", critical=True):
    print("   [SUCCESS] App imported cleanly.")
else:
    print("   [FAILURE] App failed to import.")

print("--- DIAGNOSTIC END ---")
