import os
import time
from supabase import create_client

# --- CONFIGURATION ---
LOCAL_OUTPUT_ROOT = "output"

def get_supabase_client():
    print("Locked & Loaded: Starting Migration to Supabase 🚀")
    print("-------------------------------------------------")
    url = input("Enter Supabase URL: ").strip()
    key = input("Enter Supabase Service Key (or Anon Key): ").strip()
    
    if not url or not key:
        print("❌ Credentials missing. Aborting.")
        exit(1)
        
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        exit(1)

def migrate():
    supabase = get_supabase_client()
    
    # Authenticate (Optional - usually not needed with Service Role, but good practice)
    # email = input("Enter your email (to assign ownership): ").strip()
    # For now, we will assign to the first user found or just insert (RLS might block if not auth, assuming Key bypasses or we are owner)
    # We will try to find a user to assign the data to.
    
    user_id = None
    try:
        # Try to get the first user to assign ownership if we are admin
        # Or prompt user to login? That's complex for a script.
        # Simpler: Ask for User ID.
        print("\nNOTE: Data must belong to a user.")
        user_id = input("Enter your Supabase User UUID (found in 'profiles' table or Auth tab): ").strip()
    except: pass

    if not user_id:
        print("❌ User ID required to assign ownership.")
        exit(1)

    print(f"\n📂 Scanning '{LOCAL_OUTPUT_ROOT}'...")
    if not os.path.exists(LOCAL_OUTPUT_ROOT):
        print("❌ Output directory not found!")
        exit(1)

    # 1. SCAN COURSES (Directories in output/)
    courses = [d for d in os.listdir(LOCAL_OUTPUT_ROOT) if os.path.isdir(os.path.join(LOCAL_OUTPUT_ROOT, d))]
    
    for course_name in courses:
        print(f"\n🎓 Processing Course: {course_name}")
        
        # Create Course in DB
        res = supabase.table("courses").select("*").eq("name", course_name).eq("user_id", user_id).execute()
        if res.data:
            course_id = res.data[0]['id']
            print(f"   ✅ Course exists (ID: {course_id})")
        else:
            print(f"   ✨ Creating course...")
            res = supabase.table("courses").insert({"user_id": user_id, "name": course_name}).execute()
            course_id = res.data[0]['id']
            print(f"   ✅ Created (ID: {course_id})")

        # 2. SCAN UNITS (Subdirectories in Course)
        course_path = os.path.join(LOCAL_OUTPUT_ROOT, course_name)
        units = [d for d in os.listdir(course_path) if os.path.isdir(os.path.join(course_path, d))]
        
        for unit_name in units:
            unit_display_name = unit_name.capitalize() # e.g. 'transcripts' -> 'Transcripts'
            print(f"   📂 Unit: {unit_display_name}")
            
            # Create Unit in DB
            res = supabase.table("units").select("*").eq("course_id", course_id).eq("name", unit_display_name).execute()
            if res.data:
                unit_id = res.data[0]['id']
            else:
                res = supabase.table("units").insert({"course_id": course_id, "name": unit_display_name}).execute()
                unit_id = res.data[0]['id']
            
            # 3. SCAN FILES
            unit_path = os.path.join(course_path, unit_name)
            files = [f for f in os.listdir(unit_path) if os.path.isfile(os.path.join(unit_path, f))]
            
            for file_name in files:
                file_path = os.path.join(unit_path, file_name)
                print(f"      📄 Uploading {file_name}...", end=" ")
                
                # Check exist
                res = supabase.table("files").select("id").eq("unit_id", unit_id).eq("name", file_name).execute()
                if res.data:
                    print("Skipped (Exists)")
                    continue
                
                # Read Content
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    # Guess Type
                    ftype = "other"
                    if "transcript" in file_name or unit_name == "transcripts": ftype = "transcript"
                    elif "notes" in file_name or unit_name == "notes": ftype = "note"
                    elif "guide" in file_name or unit_name == "guides": ftype = "guide"
                    
                    supabase.table("files").insert({
                        "unit_id": unit_id, 
                        "name": file_name,
                        "content_text": content,
                        "type": ftype
                    }).execute()
                    print("✅ Done")
                except Exception as e:
                     msg = str(e)
                     if "42501" in msg or "row-level security" in msg:
                         print("\n❌ SECURITY ERROR: Permission denied.")
                         print("👉 CAUSE: You likely used the 'Anon' (Public) Key.")
                         print("👉 FIX: Please re-run and use the 'SERVICE_ROLE' (Secret) Key.")
                         print("   (Find it in Supabase > Project Settings > API > service_role key)\n")
                         exit(1)
                     print(f"❌ Failed: {e}")

    print("\n-------------------------------------------------")
    print("✅ Migration Complete! Refesh your Streamlit App.")

if __name__ == "__main__":
    migrate()
