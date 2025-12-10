import streamlit as st
from supabase import create_client, Client
import datetime

# --- INIT ---
# --- INIT ---


# Fix [Errno 24] Too many open files: Use st.cache_resource
# TTL 1h. If it fails, it raises Exception and DOES NOT CACHE.
@st.cache_resource(ttl=3600)
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


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

# --- COURSES (DIPLOMADOS) ---
def get_user_courses(user_id):
    supabase = init_supabase()
    try:
        # Order by creation date descending
        res = supabase.table("courses").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return []

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
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Error creating unit: {e}")
        return None

def delete_unit(unit_id):
    supabase = init_supabase()
    try:
        supabase.table("units").delete().eq("id", unit_id).execute()
        return True
    except: return False

def rename_unit(unit_id, new_name):
    supabase = init_supabase()
    try:
        supabase.table("units").update({"name": new_name}).eq("id", unit_id).execute()
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
def get_files(unit_id):
    supabase = init_supabase()
    try:
        # RPC Bypass for API Cache issues
        res = supabase.rpc("get_unit_files", {"p_unit_id": unit_id}).execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching files (RPC): {e}")
        return []

def upload_file_to_db(unit_id, name, content_text, file_type):
    """
    Saves file metadata and content (text) to DB via RPC (Bypass API Cache).
    """
    supabase = init_supabase()
    try:
        # Use RPC to ensure content_text is passed correctly even if API schema is stale
        params = {
            "p_unit_id": unit_id,
            "p_name": name,
            "p_content": content_text,
            "p_type": file_type
        }
        res = supabase.rpc("create_library_file", params).execute()
        return True
    except Exception as e:
        st.error(f"Error uploading file (RPC): {e}")
        return False

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

def rename_file(file_id, new_name):
    supabase = init_supabase()
    try:
        supabase.table("library_files").update({"name": new_name}).eq("id", file_id).execute()
        return True
    except: return False



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
        # Get unit name for labeling
        u_res = supabase.table("units").select("name").eq("id", unit_id).single().execute()
        u_name = u_res.data['name'] if u_res.data else "Unknown Unit"
        
        # Get files
        files = supabase.table("library_files").select("name, content_text").eq("unit_id", unit_id).execute().data
        
        unit_text = ""
        for f in files:
            if f['content_text']:
                unit_text += f"\n--- ARCHIVO: {u_name}/{f['name']} ---\n{f['content_text']}\n"
        return unit_text
    except: return ""

def get_dashboard_stats(course_id, user_id):
    """
    Aggregates stats for the dashboard:
    - Total Files in Course
    - Total Chats for User
    - File Type Distribution
    """
    supabase = init_supabase()
    stats = {
        "files": 0,
        "chats": 0,
        "file_types": {"Documentos": 0, "Libros": 0} # Simplified categories
    }
    
    try:
        # 1. Get Unit IDs for this course
        units = supabase.table("units").select("id").eq("course_id", course_id).execute().data
        if units:
            unit_ids = [u['id'] for u in units]
            
            # 2. Get Files count & types
            # Not fetching content_text to save bandwidth
            files = supabase.table("library_files").select("type").in_("unit_id", unit_ids).execute().data
            stats['files'] = len(files)
            
            for f in files:
                if f['type'] == 'text':
                    stats['file_types']['Documentos'] += 1
                else:
                    stats['file_types']['Libros'] += 1
                    
        # 3. Get Chats count
        res_chats = supabase.table("chat_sessions").select("id", count="exact").eq("user_id", user_id).execute()
        stats['chats'] = res_chats.count if res_chats.count is not None else len(res_chats.data)
        
        return stats
    except Exception as e:
        print(f"Stats Error: {e}")
        return stats

# --- CHAT HISTORY PERSISTENCE (MULTI-CHAT) ---

def create_chat_session(user_id, name="Nuevo Chat"):
    supabase = init_supabase()
    try:
        data = {"user_id": user_id, "name": name}
        res = supabase.table("chat_sessions").insert(data).execute()
        return res.data[0] if res.data else None
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
