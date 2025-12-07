import streamlit as st
from supabase import create_client, Client
import datetime

# Singleton pattern using Streamlit cache
@st.cache_resource
def init_supabase():
    """Initializes the Supabase client using secrets."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}. Revisa tus 'secrets'.")
        return None

def sign_in(email, password):
    """Signs in a user."""
    supabase: Client = init_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return res.user
    except Exception as e:
        return None

def sign_up(email, password):
    """Signs up a new user."""
    supabase: Client = init_supabase()
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        return res.user
    except Exception as e:
        # st.error(f"Error registro: {e}")
        return None

def get_user_courses(user_id):
    """Fetches courses for a specific user."""
    supabase: Client = init_supabase()
    try:
        response = supabase.table("courses").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        return []

def create_course(user_id, course_name):
    """Creates a new course for a user."""
    supabase: Client = init_supabase()
    try:
        data = {"user_id": user_id, "name": course_name}
        supabase.table("courses").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating course: {e}")
        return False
