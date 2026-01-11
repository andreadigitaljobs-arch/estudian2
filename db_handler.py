import streamlit as st
import os
from supabase import create_client, Client
import datetime

# --- INIT ---
# --- INIT ---


# Fix [Errno 24] Too many open files: Use st.cache_resource
# TTL 1h. If it fails, it raises Exception and DOES NOT CACHE.
# CACHING REMOVED to ensure Auth state is always fresh per-request/per-user
# NOW USING SESSION SINGLETON to prevent "Too many open files"
def init_supabase():
    client = None
    
    # 1. Return existing session client if available
    if 'supabase_client_instance' in st.session_state:
        client = st.session_state['supabase_client_instance']
    else:
        # 2. Create new client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        client = create_client(url, key)
        # Store in Session State
        st.session_state['supabase_client_instance'] = client
    
    # 3. Auto-Hydrate from Session (ALWAYS run this to ensure up-to-date token)
    if 'supabase_session' in st.session_state and st.session_state['supabase_session']:
        try:
            sess = st.session_state['supabase_session']
            client.auth.set_session(sess.access_token, sess.refresh_token)
            client.postgrest.auth(sess.access_token)
        except: pass
        
    return client


# Auth Hydration Helper (Separate from Init)
def hydrate_auth(client):
    if 'supabase_session' in st.session_state and st.session_state['supabase_session']:
        try:
            sess = st.session_state['supabase_session']
            client.auth.set_session(sess.access_token, sess.refresh_token)
            client.postgrest.auth(sess.access_token)
        except Exception as e:
            print(f"Auth Hydration Error: {e}")


# Wrapper to ensure we always get a hydrated client used in app
def get_supabase():
    try:
        client = init_supabase()
        if client:
            hydrate_auth(client)
        return client
    except Exception as e:
        st.error(f"⚠️ Error Crítico de Conexión: {e}")
        st.cache_resource.clear() # Emergency Cache Clear
        return None



# --- AUTH ---
def sign_in(email, password):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # Store Session for RLS
        if res.session:
            st.session_state['supabase_session'] = res.session
        return res.user
    except Exception as e:
        print(f"Login Error: {e}") 
        msg = str(e)
        if "Email not confirmed" in msg:
            st.error("⚠️ Tu email no ha sido confirmado.")
        elif "Invalid login credentials" in msg:
            st.error("❌ Contraseña incorrecta.")
        else:
            st.error(f"Error de Login: {msg}")
        return None

def sign_up(email, password):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        # Store Session if auto-login
        if res.session:
            st.session_state['supabase_session'] = res.session
        return res.user
    except Exception as e:
        st.error(f"Error de Registro: {e}")
        return None

def update_user_nickname(new_nickname):
    """Updates user metadata to persist nickname."""
    supabase = init_supabase()
    try:
        attrs = {"data": {"nickname": new_nickname}}
        res = supabase.auth.update_user(attrs)
        return res.user
    except Exception as e:
        print(f"Error updating profile: {e}")
        return None

def update_last_course(course_name):
    """Persists the last active course name to user metadata."""
    supabase = init_supabase()
    try:
        attrs = {"data": {"last_course_name": course_name}}
        supabase.auth.update_user(attrs)
        return True
    except Exception as e:
        print(f"Error persisting course: {e}")
        return False

def update_user_footprint(user_id, footprint_data):
    """
    Updates the 'smart_footprint' in user metadata.
    footprint_data: dict with keys {'type', 'title', 'target_id', 'subtitle', 'timestamp'}
    types: 'chat', 'unit', 'file_interaction'
    """
    supabase = init_supabase()
    from datetime import datetime
    try:
        footprint_data['timestamp'] = datetime.utcnow().isoformat()
        attrs = {"data": {"smart_footprint": footprint_data}}
        supabase.auth.update_user(attrs)
    except Exception as e:
        print(f"Error updating footprint: {e}")

def get_user_footprint(user_id):
    """
    Retrieves the 'smart_footprint' from user metadata.
    """
    supabase = init_supabase()
    try:
        # Attempt to get from session user first (most common case is getting own footprint)
        user = supabase.auth.get_user()
        if user and user.user:
            # We don't strictly check user_id vs current because usually we only see own data
            return user.user.user_metadata.get('smart_footprint', {})
        return {}
    except:
        return {}

# --- COURSES (DIPLOMADOS) ---
def get_user_courses(user_id):
    supabase = init_supabase()
    try:
        # Order by creation date descending
        res = supabase.table("courses").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching courses: {e}")
        return None

def create_course(user_id, name):
    supabase = init_supabase()
    try:
        data = {"user_id": user_id, "name": name}
        res = supabase.table("courses").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Error creating course: {e}")
        return None

def delete_course(course_id):
    supabase = init_supabase()
    try:
        res = supabase.table("courses").delete().eq("id", course_id).execute()
        # If no data returned, nothing was deleted (likely RLS)
        if not res.data:
            st.error(f"No se pudo borrar el diplomado (posible bloqueo de seguridad RLS).")
            return False
        return True
    except Exception as e:
        st.error(f"Error deleting course: {e}")
        return False

def rename_course(course_id, new_name):
    supabase = init_supabase()
    try:
        res = supabase.table("courses").update({"name": new_name}).eq("id", course_id).execute()
        if not res.data:
            # Silent RLS failure or ID not found
            return False
        return True
    except Exception as e:
        st.error(f"Error renaming course: {e}")
        return False

# --- UNITS (CARPETAS) ---
@st.cache_data(ttl=2, show_spinner=False)
def get_units(course_id, parent_id=None, fetch_all=False):
    """
    Fetch folders.
    - If fetch_all=True, returns ALL folders (flat list) for the course.
    - If fetch_all=False (default):
        - If parent_id is None: returns only ROOT folders.
        - If parent_id is set: returns only direct CHILDREN of that folder.
    """
    supabase = init_supabase()
    try:
        query = supabase.table("units").select("*").eq("course_id", course_id)
        
        if not fetch_all:
            if parent_id is None:
                # Fetch Root Folders
                query = query.is_("parent_id", "null")
            else:
                # Fetch Subfolders
                query = query.eq("parent_id", parent_id)
                
        res = query.order("name").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching units: {e}")
        return []

def create_unit(course_id, name, parent_id=None):
    supabase = init_supabase()
    try:
        # Check if exists first to avoid duplicates
        query = supabase.table("units").select("*").eq("course_id", course_id).eq("name", name)
        if parent_id:
            query = query.eq("parent_id", parent_id)
        else:
            query = query.is_("parent_id", "null")
            
        existing = query.execute()
        if existing.data:
            return existing.data[0] # Return existing folder
            
        # Create new if not exists
        data = {"course_id": course_id, "name": name}
        if parent_id:
            data["parent_id"] = parent_id
            
        res = supabase.table("units").insert(data).execute()
        get_units.clear() # CACHE FIX
        return res.data[0] if res.data else None
    except Exception as e:
        # CONSULTANT FIX: Suppress noisy RLS errors on the UI for auto-creation
        print(f"Error creating unit (Background): {e}") 
        return None

def delete_unit(unit_id):
    supabase = init_supabase()
    try:
        supabase.table("units").delete().eq("id", unit_id).execute()
        get_units.clear() # CACHE FIX
        return True
    except Exception as e: 
        print(f"Error deleting unit: {e}")
        return False

def get_full_course_backup(course_id):
    """
    Fetches ALL files with content for valid export.
    Returns list of dicts: [{'name': '...', 'content': '...', 'unit_name': '...'}]
    """
    supabase = init_supabase()
    try:
        # 1. Get Units to map names recursively
        units = supabase.table("units").select("id, name, parent_id").eq("course_id", course_id).execute().data
        if not units: return []
        
        # Build Path Map
        # 1. Dict Access
        u_dict = {u['id']: u for u in units}
        
        # 2. Recursive Path Builder
        def get_path(uid):
            if uid not in u_dict: return "Unknown"
            curr = u_dict[uid]
            if curr.get('parent_id'):
                return f"{get_path(curr['parent_id'])}/{curr['name']}"
            return curr['name']
            
        unit_path_map = {u['id']: get_path(u['id']) for u in units}
        unit_ids = list(unit_path_map.keys())
        
        # 2. Get Files with Content (Heavy Fetch)
        # We need content_text
        all_files = []
        
        # Pagination might be needed if HUGE, but for now assuming < 500 files.
        # Supabase default limit is 1000.
        res = supabase.table("library_files") \
            .select("unit_id, name, content_text, type") \
            .in_("unit_id", unit_ids) \
            .execute()
            
        for f in res.data:
            # Only export TEXT files or MARKDOWN
            # If type is 'text' or it has content
            if f.get('content_text'):
                uname = unit_path_map.get(f['unit_id'], "Sin Unidad")
                all_files.append({
                    "name": f['name'],
                    "content": f['content_text'],
                    "unit": uname
                })
                
        return all_files
    except Exception as e:
        print(f"Backup Error: {e}")
        return []

def rename_unit(unit_id, new_name):
    supabase = init_supabase()
    try:
        supabase.table("units").update({"name": new_name}).eq("id", unit_id).execute()
        get_units.clear() # CACHE FIX
        return True
    except: return False

def search_library(course_id, search_term):
    """
    Search for files across an entire course (all units).
    Returns list of files enriched with 'unit_name'.
    """
    supabase = init_supabase()
    try:
        # 1. Get all units for this course to filter scope
        units = supabase.table("units").select("id, name").eq("course_id", course_id).execute().data
        if not units: return []
        
        unit_ids = [u['id'] for u in units]
        unit_map = {u['id']: u['name'] for u in units}
        
        # 2. Search files
        # ilike is case-insensitive pattern matching
        term_pattern = f"%{search_term}%"
        res = supabase.table("library_files") \
            .select("*") \
            .in_("unit_id", unit_ids) \
            .ilike("name", term_pattern) \
            .execute()
            
        files = res.data if res.data else []
        
        # 3. Enrich with Unit Name
        for f in files:
            f['unit_name'] = unit_map.get(f['unit_id'], "Carpeta Desconocida")
            
        return files
    except Exception as e:
        print(f"Search Error: {e}")
        return []

# --- FILES (ARCHIVOS) ---
@st.cache_data(ttl=5, show_spinner=False)
def get_files(unit_id):
    supabase = init_supabase()
    try:
        # RPC Bypass for API Cache issues
        res = supabase.rpc("get_unit_files", {"p_unit_id": unit_id}).execute()
        return res.data
    except Exception as e:
        # print(f"Error fetching files (RPC): {e}") # Log silently
        return []

def upload_file_to_db(unit_id, name, content_text, file_type):
    # SANITIZE: Remove asterisks and quotes from filename globally
    if name:
        name = name.replace("*", "").replace('"', "").replace("'", "").strip()
    """
    Saves file metadata and content (text) to DB via RPC (Bypass API Cache).
    """
    supabase = init_supabase()
    try:
        data = {
            "unit_id": unit_id,
            "name": name,
            "content_text": content_text,
            "type": file_type
        }
        res = supabase.table("library_files").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False

def move_file(file_id, new_unit_id):
    """
    Moves a file to a different unit (Update unit_id).
    """
    supabase = init_supabase()
    try:
        supabase.table("library_files").update({"unit_id": new_unit_id}).eq("id", file_id).execute()
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False
move_file_db = move_file # Compatibility Alias

def get_file_content(file_id):
    supabase = init_supabase()
    try:
        res = supabase.rpc("read_file_text", {"p_file_id": file_id}).execute()
        # RPC returns the string directly or as data
        return res.data if res.data else ""
    except: return ""

def delete_file(file_id):
    supabase = init_supabase()
    try:
        supabase.table("library_files").delete().eq("id", file_id).execute()
        return True
    except: return False
delete_file_db = delete_file # Compatibility Alias

def rename_file(file_id, new_name):
    # SANITIZE
    if new_name:
        new_name = new_name.replace("*", "").replace('"', "").replace("'", "").strip()
    supabase = init_supabase()
    try:
        supabase.table("library_files").update({"name": new_name}).eq("id", file_id).execute()
        get_files.clear() # CACHE FIX
        return True
    except: return False
rename_file_db = rename_file # Compatibility Alias

def update_file_content(file_id, new_content):
    """
    Updates the content_text of a file.
    Used for manual edits or AI formatting.
    """
    supabase = init_supabase()
    try:
        supabase.table("library_files").update({"content_text": new_content}).eq("id", file_id).execute()
        get_files.clear()  # Invalidate cache
        return True
    except Exception as e:
        error_msg = f"DB Error: {str(e)}"
        print(error_msg)
        return error_msg # Return the actual error message



def get_course_full_context(course_id):
    """
    Efficiently fetches all text content for a course (from all units).
    Returns a string with concatenated content.
    """
    supabase = init_supabase()
    try:
        # 1. Get all units for course
        units = supabase.table("units").select("id, name").eq("course_id", course_id).execute().data
        if not units: return ""
        
        unit_ids = [u['id'] for u in units]
        unit_map = {u['id']: u['name'] for u in units}
        
        # 2. Get all files for these units
        # Supabase Python client 'in_' filter for array
        files = supabase.table("library_files").select("unit_id, name, content_text").in_("unit_id", unit_ids).execute().data
        
        full_context = ""
        for f in files:
            u_name = unit_map.get(f['unit_id'], "Unknown Unit")
            if f['content_text']:
                full_context += f"\n--- ARCHIVO: {u_name}/{f['name']} ---\n{f['content_text']}\n"
                
        return full_context
    except Exception as e:
        print(f"Error fetching global context: {e}")
        return ""

def get_unit_context(unit_id):
    """
    Efficiently fetches text content for a specific unit.
    """
    supabase = init_supabase()
    try:
        # 1. Get Target Unit Info (to find course_id)
        target = supabase.table("units").select("id, course_id, name").eq("id", unit_id).single().execute()
        if not target.data: return ""
        
        c_id = target.data['course_id']
        root_name = target.data['name']
        
        # 2. Get ALL units for this course to build tree
        all_units = supabase.table("units").select("id, parent_id, name").eq("course_id", c_id).execute().data
        
        # 3. Find Descendants
        # iterative expansion
        valid_ids = {unit_id} # Set for fast lookup
        
        # Simple loop to separate generations (crude but effective for shallow trees)
        # Better: Build adjacency list
        parent_map = {}
        for u in all_units:
            pid = u.get('parent_id')
            if pid:
                if pid not in parent_map: parent_map[pid] = []
                parent_map[pid].append(u)
        
        # BFS/DFS
        queue = [unit_id]
        while queue:
            curr = queue.pop(0)
            children = parent_map.get(curr, [])
            for child in children:
                valid_ids.add(child['id'])
                queue.append(child['id'])
        
        # 4. Fetch files for ALL valid units
        files = supabase.table("library_files").select("name, content_text, unit_id").in_("unit_id", list(valid_ids)).execute().data
        
        # 5. Compile Text
        # Create a map for unit names to be nice
        unit_names = {u['id']: u['name'] for u in all_units}
        
        unit_text = f"--- CONTENIDO DE CARPETA MAESTRA: {root_name} (Incluyendo Subcarpetas) ---\n"
        
        for f in files:
            if f['content_text']:
                u_sub_name = unit_names.get(f['unit_id'], "Unknown")
                unit_text += f"\n--- ARCHIVO: {u_sub_name}/{f['name']} ---\n{f['content_text']}\n"
                
        return unit_text
    except: return ""

@st.cache_data(ttl=10, show_spinner=False)
def get_dashboard_stats(course_id, user_id):
    """
    Aggregates stats for the dashboard (Optimized: Head Count Only).
    """
    supabase = init_supabase()
    stats = {
        "files": 0,
        "chats": 0,
        "file_types": {"Documentos": 0, "Libros": 0} 
    }
    
    try:
        # 1. Get Unit IDs (Lightweight)
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if units:
            unit_ids = [u['id'] for u in units]
            
            # 2. Get Files COUNT (Optimized)
            # Use `count='exact', head=True` to avoid fetching data
            res_files = supabase.table("library_files").select("id", count="exact", head=True).in_("unit_id", unit_ids).execute()
            stats['files'] = res_files.count if res_files.count is not None else 0
            
            # Note: File Type distribution is expensive to count without fetching data or doing multiple count queries.
            # For speed, we will approximate or skip file types if not critical, OR do one light fetch of just 'type' column
            # if the number of files isn't huge (e.g. < 1000). 
            # Given user has "latency issues", let's skip the heavy breakdown or cache it longer.
            # Let's do a light fetch of ONLY type column (minimal bandwidth)
            res_types = supabase.table("library_files").select("type").in_("unit_id", unit_ids).execute()
            if res_types.data:
                 for f in res_types.data:
                     if f['type'] == 'text': stats['file_types']['Documentos'] += 1
                     else: stats['file_types']['Libros'] += 1
                    
        # 3. Get Chats count
        res_chats = supabase.table("chat_sessions").select("id", count="exact", head=True).eq("user_id", user_id).execute()
        stats['chats'] = res_chats.count if res_chats.count is not None else 0
        
        return stats
    except Exception as e:
        # print(f"Stats Error: {e}")
        return stats

# --- CHAT HISTORY PERSISTENCE (MULTI-CHAT) ---

def create_chat_session(user_id, name="Nuevo Chat"):
    supabase = init_supabase()
    try:
        data = {"user_id": user_id, "name": name}
        res = supabase.table("chat_sessions").insert(data).execute()
        # Return the session ID, not the full object
        return res.data[0]['id'] if res.data else None
    except Exception as e:
        print(f"Error creating chat session: {e}")
        return None

def get_chat_sessions(user_id):
    supabase = init_supabase()
    try:
        # Order by newest first? Or creation date? Usually newest first is better for UI.
        res = supabase.table("chat_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching chat sessions: {e}")
        return []

def get_recent_chats(user_id, limit=3):
    """Fetch recent chats for dashboard."""
    supabase = init_supabase()
    try:
        res = supabase.table("chat_sessions") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        return res.data
    except Exception as e:
        print(f"Error fetching recent chats: {e}")
        return []

    except Exception as e:
        print(f"Error fetching recent chats: {e}")
        return []

def check_and_update_streak(user):
    """
    Checks and updates the user's login streak based on last_visit date.
    Returns the current streak count.
    """
    from datetime import datetime, timedelta
    supabase = init_supabase()
    
    try:
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        meta = user.user_metadata or {}
        
        last_date_str = meta.get("streak_date")
        current_streak = meta.get("streak_count", 0)
        
        # If no history, init
        if not last_date_str:
            new_streak = 1
            supabase.auth.update_user({"data": {"streak_date": today_str, "streak_count": new_streak}})
            return new_streak
            
        # If already visited today, return current
        if last_date_str == today_str:
            return current_streak if current_streak > 0 else 1
            
        # Check if yesterday
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        # Calculate difference properly
        # Note: UTC dates are clean to compare
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        delta = (today_date - last_date).days
        
        if delta == 1:
            # Streak continues!
            new_streak = current_streak + 1
        else:
            # Broken streak (delta > 1) or time travel? Reset to 1 (today is a new day)
            new_streak = 1
            
        # Push update
        supabase.auth.update_user({"data": {"streak_date": today_str, "streak_count": new_streak}})
        return new_streak
        
    except Exception as e:
        print(f"Streak Error: {e}")
        return 1

def rename_chat_session(session_id, new_name):
    supabase = init_supabase()
    try:
        supabase.table("chat_sessions").update({"name": new_name}).eq("id", session_id).execute()
        return True
    except Exception as e:
        print(f"Error renaming chat session: {e}")
        return False

def delete_chat_session(session_id):
    supabase = init_supabase()
    try:
        supabase.table("chat_sessions").delete().eq("id", session_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False

def get_chat_messages(session_id):
    supabase = init_supabase()
    try:
        res = supabase.table("chat_messages").select("*").eq("session_id", session_id).order("created_at", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching chat messages: {e}")
        return []

def save_chat_message(session_id, role, content):
    supabase = init_supabase()
    try:
        data = {
            "session_id": session_id,
            "role": role,
            "content": content
        }
        supabase.table("chat_messages").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return False

def get_course_files(course_id, type_filter=None):
    """
    Fetches all files in a course, optionally filtered by type.
    """
    supabase = init_supabase()
    try:
        # 1. Get all unit IDs
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if not units: return []
        
        unit_ids = [u['id'] for u in units]
        
        # 2. Query files in these units
        query = supabase.table("library_files").select("id, name, type, unit_id").in_("unit_id", unit_ids)
        
        if type_filter:
            query = query.eq("type", type_filter)
            
        res = query.order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching course files: {e}")
        return []

def get_recent_files(course_id, limit=5):
    """
    Fetches the most recently created files for a course (Dashboard).
    """
    supabase = init_supabase()
    try:
        # 1. Get all unit IDs
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if not units: return []
        
        unit_ids = [u['id'] for u in units]
        
        # 2. Query files
        res = supabase.table("library_files") \
            .select("id, name, type, created_at, unit_id") \
            .in_("unit_id", unit_ids) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
            
        return res.data
    except Exception as e:
        print(f"Error fetching recent files: {e}")
        return []

def get_last_transcribed_file_name(course_id):
    """
    Returns the name of the last successfully transcribed file for a given course.
    """
    files = get_course_files(course_id, type_filter="transcript")
    if files:
        # get_course_files already orders by created_at desc
        # We need to remove the .txt extension and numbering if present for clean display
        import re
        raw_name = files[0]['name']
        # Remove extension
        name = os.path.splitext(raw_name)[0]
        # Remove leading "01. " numbering if present
        name = re.sub(r'^\d+\.\s*', '', name)
        return name
    return None

def upload_file_v2(unit_id, filename, content, f_type="note"):
    """
    Saves a file to the database (library_files).
    Upsert: Update if exists, Insert if new.
    """
    supabase = init_supabase()
    user = st.session_state.get('user')
    if not user: return None
    
    try:
        # Check existence in library_files
        res = supabase.table('library_files').select('id').eq('unit_id', unit_id).eq('name', filename).execute()
        
        if res.data:
            # Update
            f_id = res.data[0]['id']
            # Column is 'content_text', not 'content'
            supabase.table('library_files').update({'content_text': content}).eq('id', f_id).execute()
        else:
            # Insert - use content_text
            supabase.table('library_files').insert({
                'unit_id': unit_id,
                'name': filename,
                'content_text': content,
                'type': f_type,
                # 'user_id': user.id # library_files might not have user_id if it uses RLS via auth.uid() or if it's inherited from unit. 
                # Checking get_files(line 579) it selects id,name,type,unit_id.
                # create_library_file RPC doesn't pass user_id. 
                # So I'll omit user_id and rely on RLS/Default.
                # Wait, create_library_file RPC (Line 310) takes p_unit_id, p_name, p_content, p_type. User ID is likely inferred.
            }).execute()
        return True
    except Exception as e:
        print(f"Error saving file {filename}: {e}")
        st.error(f"Error guardando archivo: {e}")
        return False

def get_user_memory(course_id):
    """
    Retrieves the content of the 'MEMORY_OVERRIDE.md' file which acts as the 'Long Term Memory' 
    of user corrections.
    """
    supabase = init_supabase()
    try:
        # Search for file named 'MEMORY_OVERRIDE.md' in this course
        res = supabase.table("library_files") \
            .select("content_text") \
            .eq("name", "MEMORY_OVERRIDE.md") \
            .eq("type", "text") \
            .limit(1) \
            .execute()
            
        if res.data:
            return res.data[0]['content_text']
        else:
            return ""
    except Exception as e:
        print(f"Error fetching memory: {e}")
        return ""

def save_user_memory(course_id, new_memory_text, unit_id_fallback):
    """
    Appends or creates the MEMORY_OVERRIDE.md file with the new correction.
    """
    supabase = init_supabase()
    try:
        # 1. Get existing content
        current_mem = get_user_memory(course_id)
        
        # 2. Append new text
        updated_content = (current_mem + "\n" + new_memory_text).strip()
        
        # 3. Check if file exists to Update or Insert
        res = supabase.table("library_files") \
            .select("id") \
            .eq("name", "MEMORY_OVERRIDE.md") \
            .limit(1) \
            .execute()
            
        if res.data:
            # Update
            fid = res.data[0]['id']
            supabase.table("library_files").update({"content_text": updated_content}).eq("id", fid).execute()
        else:
            # Insert (Create in fallback unit)
            # Find a valid unit if fallback is None
            final_unit = unit_id_fallback
            if not final_unit:
                # Get first unit
                u_res = supabase.table("units").select("id").eq("course_id", course_id).limit(1).execute()
                if u_res.data:
                    final_unit = u_res.data[0]['id']
            
            if final_unit:
                supabase.table("library_files").insert({
                    "unit_id": final_unit,
                    "name": "MEMORY_OVERRIDE.md",
                    "type": "text",
                    "content_text": updated_content
                }).execute()
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        return False

def get_course_file_counts(course_id):
    """
    Returns a dict {unit_id: file_count} for the given course.
    Optimized: Uses 1 query to fetch file unit_ids and counts via Python.
    """
    supabase = init_supabase()
    try:
        # 1. Get Unit IDs for this course (to filter files)
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if not units: return {}
        
        unit_ids = [u['id'] for u in units]
        
        # 2. Fetch only unit_id of files (Lightweight)
        # We use .select("unit_id") to avoid fetching content
        res = supabase.table("library_files").select("unit_id").in_("unit_id", unit_ids).execute()
        
        # 3. Aggregate in Python
        from collections import Counter
        counts = Counter([f['unit_id'] for f in res.data])
        return dict(counts)
    except Exception as e:
        print(f"Error counting files: {e}")
        return {}
# --- REORDERING LOGIC (MAGIC ARROWS) ---
def ensure_unit_numbering(unit_id):
    """
    Ensures all files in a unit start with '01. ', '02. ', etc.
    Returns the sorted list of files.
    """
    files = get_files(unit_id) # Uses cache, but we will invalidate it
    if not files: return []
    
    # Check if already numbered
    needs_renumbering = False
    import re
    
    # Sort by current name to establish baseline order if not numbered
    # If they have numbers, this respects them. If not, alphabetical.
    files.sort(key=lambda x: x['name'])
    
    for idx, f in enumerate(files):
        prefix = f"{idx+1:02d}. "
        if not f['name'].startswith(prefix):
            needs_renumbering = True
            break
            
    if needs_renumbering:
        # Renaming loop
        # Renaming loop
        for idx, f in enumerate(files):
            # V139: Robust Regex - Handles "1. ", "01. ", "001. " to prevent duplication
            clean_name = re.sub(r'^\d+\.\s*', '', f['name'])
            new_name = f"{idx+1:02d}. {clean_name}"
            if f['name'] != new_name:
                rename_file_db(f['id'], new_name)
        
        # Invalidate cache locally
        get_files.clear()
        return get_files(unit_id) # Fetch fresh
        
    return files

def move_file_up(unit_id, file_id):
    files = ensure_unit_numbering(unit_id)
    # Find current index
    curr_idx = next((i for i, f in enumerate(files) if f['id'] == file_id), -1)
    
    if curr_idx <= 0: return # Already top or not found
    
    # Swap with prev
    file_a = files[curr_idx]
    file_b = files[curr_idx - 1] # The one above
    
    # We only swap NAMES (since numbering is in the name)
    # But wait, ensure_unit_numbering guarantees "01. Foo", "02. Bar"
    # To swap "02. Bar" UP, it becomes "01. Bar" and "01. Foo" becomes "02. Foo"
    
    # Extract raw names without prefix
    import re
    name_a_raw = re.sub(r'^\d{2}\.\s*', '', file_a['name'])
    name_b_raw = re.sub(r'^\d{2}\.\s*', '', file_b['name'])
    
    # New names
    # A moves up (takes B's index/prefix)
    # B moves down (takes A's index/prefix)
    
    prefix_top = f"{curr_idx:02d}. "     # e.g. 01.
    prefix_bot = f"{curr_idx+1:02d}. "   # e.g. 02.
    
    # Rename B (prev top) to Bot
    rename_file_db(file_b['id'], prefix_bot + name_b_raw)
    # Rename A (prev bot) to Top
    rename_file_db(file_a['id'], prefix_top + name_a_raw)
    
    get_files.clear() # FORCE UI UPDATE
    return True

def move_file_down(unit_id, file_id):
    files = ensure_unit_numbering(unit_id)
    curr_idx = next((i for i, f in enumerate(files) if f['id'] == file_id), -1)
    
    if curr_idx == -1 or curr_idx == len(files) - 1: return # Not found or already bottom
    
    # Swap with next
    file_a = files[curr_idx]
    file_b = files[curr_idx + 1] # The one below
    
    import re
    name_a_raw = re.sub(r'^\d{2}\.\s*', '', file_a['name'])
    name_b_raw = re.sub(r'^\d{2}\.\s*', '', file_b['name'])
    
    # A moves down (takes B's index)
    # B moves up (takes A's index)
    
    prefix_top = f"{curr_idx+1:02d}. "
    prefix_bot = f"{curr_idx+2:02d}. "
    
    # Rename A to Bot
    rename_file_db(file_a['id'], prefix_bot + name_a_raw)
    # Rename B to Top
    rename_file_db(file_b['id'], prefix_top + name_b_raw)
    
    get_files.clear() # FORCE UI UPDATE
    return True

# --- DASHBOARD V2 ANALYTICS ---

def search_global(user_id, course_id, query_text):
    """
    Searches across Files and Chats for the dashboard.
    Returns a unified list of results: [{'type': 'file'|'chat', 'id': '...', 'name': '...', 'preview': '...'}]
    """
    supabase = init_supabase()
    results = []
    
    try:
        # 1. Search Files (Name or Content)
        # Get unit IDs for course
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if units:
            unit_ids = [u['id'] for u in units]
            
            # Search Name
            res_name = supabase.table("library_files").select("id, name, unit_id, type").in_("unit_id", unit_ids).ilike("name", f"%{query_text}%").limit(5).execute()
            
            for f in res_name.data:
                results.append({
                    "type": "file", 
                    "id": f['id'], 
                    "name": f['name'], 
                    "unit_id": f['unit_id'],
                    "icon": "📄" if f['type'] == 'text' else "📎",
                    "preview": "Archivo en biblioteca"
                })

        # 2. Search Chats (Name)
        res_chats = supabase.table("chat_sessions").select("id, name, created_at").eq("user_id", user_id).ilike("name", f"%{query_text}%").limit(5).execute()
        
        for c in res_chats.data:
            results.append({
                "type": "chat",
                "id": c['id'],
                "name": c['name'],
                "icon": "💬",
                "preview": f"Chat iniciado el {c['created_at'][:10]}"
            })
            
        return results
    except Exception as e:
        print(f"Global Search Error: {e}")
        return []

def get_weekly_activity(user_id, course_id):
    """
    Returns a pandas DataFrame with 'Date', 'Type' (Files/Chats), 'Count' for the last 30 days.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    supabase = init_supabase()
    
    data = []
    today = datetime.utcnow().date()
    # Expand to 30 days for better visuals
    range_days = 30
    dates = [(today - timedelta(days=i)).isoformat() for i in range(range_days - 1, -1, -1)]
    
    try:
        start_date = dates[0] + "T00:00:00"
        
        # 1. Fetch Files (Last 30 days)
        # Get unit IDs for course
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        unit_ids = [u['id'] for u in units] if units else []
        
        if unit_ids:
            res_files = supabase.table("library_files") \
                .select("created_at") \
                .in_("unit_id", unit_ids) \
                .gte("created_at", start_date) \
                .execute()
            
            for f in res_files.data:
                d = f['created_at'][:10]
                data.append({"Date": d, "Activity": "Archivos"})

        # 2. Fetch Chats (Last 30 days)
        res_chats = supabase.table("chat_sessions") \
            .select("created_at") \
            .eq("user_id", user_id) \
            .gte("created_at", start_date) \
            .execute()
            
        for c in res_chats.data:
            d = c['created_at'][:10]
            data.append({"Date": d, "Activity": "Chats"})
            
        # Create complete timeline to avoid gaps
        df = pd.DataFrame(data)
        
        # If completely empty, make a dummy "zero" entry for today so chart renders flat but valid
        if df.empty:
            df = pd.DataFrame([{"Date": today.isoformat(), "Activity": "Archivos"}, {"Date": today.isoformat(), "Activity": "Chats"}])
            df = df[0:0] # Empty it back out but keep columns? No, better to just return structured zeros
            
        # Grouping Logic
        if not df.empty:
            df['Count'] = 1
            # Group by Date and Activity
            grouped = df.groupby(['Date', 'Activity']).count().reset_index()
            
            # Pivot to fill missing dates with 0
            pivot = grouped.pivot(index='Date', columns='Activity', values='Count').fillna(0)
            
            # Reindex to ensure all 30 days are present
            idx = pd.Index(dates, name='Date')
            pivot = pivot.reindex(idx, fill_value=0)
            
            # CRITICAL FIX: Ensure both columns exist for consistent coloring
            expected_cols = ['Archivos', 'Chats']
            for col in expected_cols:
                if col not in pivot.columns:
                    pivot[col] = 0
            
            # Enforce Order: Archivos (Purple), Chats (Orange)
            pivot = pivot[expected_cols]
            
            pivot = pivot.reset_index()
            
            return pivot
        else:
             # Return empty DataFrame with structure
             return pd.DataFrame({"Date": dates, "Archivos": [0]*range_days, "Chats": [0]*range_days})

    except Exception as e:
        print(f"Activity Error: {e}")
        # Return mostly empty structure
        return pd.DataFrame({"Date": dates, "Archivos": [0]*range_days, "Chats": [0]*range_days})

# --- DUPLICATE DETECTION ---
def get_duplicate_files(course_id):
    """
    Scans for files with duplicate names in the course.
    Returns a list of dicts: {'name': 'foo.pdf', 'count': 2, 'ids': [1, 2], 'paths': ['Unit1/foo.pdf', 'Unit2/foo.pdf']}
    """
    supabase = init_supabase()
    try:
        # Get all files for the course (minimal fields)
        # We need Unit Name to show path
        res = supabase.table("library_files").select("id, name, unit_id").eq("course_id", course_id).execute()
        files = res.data
        if not files: return []
        
        # Get Units for context
        units_res = supabase.table("units").select("id, name").eq("course_id", course_id).execute()
        unit_map = {u['id']: u['name'] for u in units_res.data}
        
        # Count
        name_map = {}
        for f in files:
            n = f['name']
            if n not in name_map: name_map[n] = []
            name_map[n].append({
                'id': f['id'],
                'unit': unit_map.get(f['unit_id'], "Unknown")
            })
            
        # Filter Dupes
        duplicates = []
        for name, entries in name_map.items():
            if len(entries) > 1:
                duplicates.append({
                    'name': name,
                    'count': len(entries),
                    'entries': entries
                })
        
        return duplicates
    except Exception as e:
        print(f"Error checking duplicates: {e}")
        return []
