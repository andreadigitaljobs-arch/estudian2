
import os
from database import init_supabase

def clean_filenames():
    print("Starting Bulk Rename...")
    supabase = init_supabase()
    
    # Fetch all files
    # We select ID and Name
    try:
        res = supabase.table("library_files").select("id, name").execute()
        files = res.data
        
        print(f"Found {len(files)} files.")
        
        count = 0
        for f in files:
            old_name = f['name']
            
            # Logic: Replace underscores with spaces
            new_name = old_name.replace("_", " ")
            
            # Optional: Fix double spaces
            while "  " in new_name:
                new_name = new_name.replace("  ", " ")
                
            # Strip extension artifact if it was duplicated like .txt.txt
            # But keep valid extension
            
            if new_name != old_name:
                try:
                    print(f"Renaming: {old_name} -> {new_name}")
                    supabase.table("library_files").update({"name": new_name}).eq("id", f['id']).execute()
                    count += 1
                except Exception as up_e:
                    print(f"Update Failed for {old_name}: {up_e}")
                
        print(f"Finished! Renamed {count} files.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_filenames()
