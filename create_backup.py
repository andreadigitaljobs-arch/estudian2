import shutil
import datetime
import os

# Configuration
PROJECT_ROOT = "c:/Users/nombr/.gemini/antigravity/playground/hidden-glenn"
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Generate timestamp
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
archive_name = os.path.join(BACKUP_DIR, f"Estudian2_Backup_{timestamp}")

# Files and folders to include
# We want to exclude the huge 'output' folder if possible, or maybe just include source code.
# User asked for a "Respaldo" generally implies the whole thing, but 'output' can be heavy.
# Let's include everything BUT 'output' and 'backups' to keep it light and focused on the 'System'.
# If they want data backup, they can just copy the folder. This is a "System Backup".

def ignore_patterns(path, names):
    keep = []
    for name in names:
        if name in ['output', 'backups', '__pycache__', '.git', '.DS_Store']:
            keep.append(name)
    return keep

# Create ZIP
try:
    shutil.make_archive(archive_name, 'zip', PROJECT_ROOT)
    print(f"Backup created successfully: {archive_name}.zip")
except Exception as e:
    print(f"Error creating backup: {e}")
