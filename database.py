import streamlit as st
from supabase import create_client, Client
import datetime

# --- INIT ---
# --- INIT ---
# Fix [Errno 24] Too many open files: Use Session State Singleton
def init_supabase():
    try:
        # Reuse existing client if available in this session
        if 'supabase_client_inst' in st.session_state:
            client = st.session_state['supabase_client_inst']
        else:
            # Create new if not exists
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            client = create_client(url, key)
            st.session_state['supabase_client_inst'] = client
        
        # Hydrate Auth if session exists (Always update headers)
        if 'supabase_session' in st.session_state and st.session_state['supabase_session']:
            try:
                sess = st.session_state['supabase_session']
                # Update auth state on the shared client
                client.auth.set_session(sess.access_token, sess.refresh_token)
                # FORCE POSTGREST AUTH HEADER (Critical for RLS)
                client.postgrest.auth(sess.access_token)
            except Exception as e:
                print(f"Auth Hydration Error: {e}")
                
        return client
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
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
def get_units(course_id):
    supabase = init_supabase()
    try:
        res = supabase.table("units").select("*").eq("course_id", course_id).order("name").execute()
        return res.data
    except Exception as e:
        print(f"Error fetching units: {e}")
        # st.error(f"Debug: Error fetching units: {e}") # Uncomment for tough debugging
        return []

def create_unit(course_id, name):
    supabase = init_supabase()
    try:
        # Check if exists first? Supabase might error on duplicate if we set unique constraint, 
        # but for now let's just insert.
        data = {"course_id": course_id, "name": name}
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

# --- FILES (ARCHIVOS) ---
def get_files(unit_id):
    supabase = init_supabase()
    try:
        res = supabase.table("files").select("id, name, type, created_at, content_text").eq("unit_id", unit_id).order("name").execute()
        return res.data
    except: return []

def upload_file_to_db(unit_id, name, content_text, file_type):
    """
    Saves file metadata and content (text) to DB.
    For MVP we store text content directly in DB column 'content_text'.
    For binaries (images/PDFs) we would use Storage, but for now we focus on Text content for RAG.
    """
    supabase = init_supabase()
    try:
        data = {
            "unit_id": unit_id,
            "name": name,
            "type": file_type,
            "content_text": content_text
        }
        res = supabase.table("files").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return False

def get_file_content(file_id):
    supabase = init_supabase()
    try:
        res = supabase.table("files").select("content_text").eq("id", file_id).single().execute()
        return res.data['content_text'] if res.data else ""
    except: return ""

def delete_file(file_id):
    supabase = init_supabase()
    try:
        supabase.table("files").delete().eq("id", file_id).execute()
        return True
    except: return False

def rename_file(file_id, new_name):
    supabase = init_supabase()
    try:
        supabase.table("files").update({"name": new_name}).eq("id", file_id).execute()
        return True
    except: return False

def get_files(unit_id):
    supabase = init_supabase()
    try:
        # Fetch metadata for listing
        res = supabase.table("files").select("id, name, type, created_at").eq("unit_id", unit_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        print(f"Error fetching files: {e}")
        return []

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
        files = supabase.table("files").select("unit_id, name, content_text").in_("unit_id", unit_ids).execute().data
        
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
        files = supabase.table("files").select("name, content_text").eq("unit_id", unit_id).execute().data
        
        unit_text = ""
        for f in files:
            if f['content_text']:
                unit_text += f"\n--- ARCHIVO: {u_name}/{f['name']} ---\n{f['content_text']}\n"
        return unit_text
    except: return ""
