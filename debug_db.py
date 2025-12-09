import os
import streamlit as st
from supabase import create_client

# Load secrets directly to avoid Streamlit Context issues in standalone script
# NOTE: This script is for the USER to run locally to verify data visibility.
url = input("Supabase URL: ")
key = input("Supabase Key (Service Role for full access, Anon for simulation): ")
user_id = input("User UUID: ")

supabase = create_client(url, key)

print("\n--- DEBUGGING ---")
print(f"Checking for User: {user_id}")

# 1. Get Courses
res = supabase.table("courses").select("*").eq("user_id", user_id).execute()
print(f"Courses Found: {len(res.data)}")
for c in res.data:
    print(f" - {c['name']} (ID: {c['id']})")
    
    # 2. Get Units for this Course
    u_res = supabase.table("units").select("*").eq("course_id", c['id']).execute()
    print(f"   Units Found: {len(u_res.data)}")
    for u in u_res.data:
        print(f"    - {u['name']} (ID: {u['id']})")
        
        # 3. Get Files
        f_res = supabase.table("files").select("*").eq("unit_id", u['id']).execute()
        print(f"      Files Found: {len(f_res.data)}")

print("\n--- END DEBUG ---")
