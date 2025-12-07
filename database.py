import streamlit as st
from supabase import create_client, Client
import datetime

# --- INIT ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
        return None

# --- AUTH ---
def sign_in(email, password):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res.user
    except: return None

def sign_up(email, password):
    supabase = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res.user
    except: return None

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

# --- UNITS (CARPETAS) ---
def get_units(course_id):
    supabase = init_supabase()
    try:
        res = supabase.table("units").select("*").eq("course_id", course_id).order("name").execute()
        return res.data
    except: return []

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
        res = supabase.table("files").select("id, name, type, created_at").eq("unit_id", unit_id).order("name").execute()
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
