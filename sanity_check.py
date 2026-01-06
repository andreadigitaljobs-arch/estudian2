import sys
import os

# Mock Streamlit secrets/session_state to avoid instant crash
import streamlit as st
from unittest.mock import MagicMock

if not hasattr(st, "secrets"):
    st.secrets = {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test"}
if not hasattr(st, "session_state"):
    st.session_state = {}
if not hasattr(st, "cache_data"):
    st.cache_data = lambda ttl=None, show_spinner=False: lambda func: func
if not hasattr(st, "cache_resource"):
    st.cache_resource = lambda ttl=None, show_spinner=False: lambda func: func

print("--- STARTING IMPORT CHECK ---")
try:
    print("1. Importing database...")
    import database
    print("   database imported successfully.")
    
    print("2. Checking database exports...")
    if hasattr(database, "delete_file_db"):
        print("   delete_file_db alias FOUND.")
    else:
        print("   delete_file_db alias MISSING.")
        
    if hasattr(database, "rename_file_db"):
        print("   rename_file_db alias FOUND.")
    else:
        print("   rename_file_db alias MISSING.")

    print("3. Importing library_render...")
    import library_render
    print("   library_render imported successfully.")
    
except Exception as e:
    print(f"\nCRITICAL IMPORT ERROR:\n{e}")
    import traceback
    traceback.print_exc()

print("--- CHECK COMPLETE ---")
