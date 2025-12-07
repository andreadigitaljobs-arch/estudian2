import streamlit as st
import database
import time
from datetime import datetime

st.set_page_config(page_title="Test DB", layout="wide")

st.title("🧪 Database Logic Test")

# 1. Login Test
res_user = database.sign_in("admin@test.com", "admin123")
if not res_user:
    st.warning("⚠️ No se pudo loguear 'admin@test.com'. Intenta registrarlo manualmente o usa credenciales válidas.")
    # Attempt create simple user
    res_user = database.sign_up("admin@test.com", "admin123")
    if res_user: st.success("Created test user.")
    
if res_user:
    st.success(f"✅ Logged in as: {res_user.email} | ID: {res_user.id}")
    user_id = res_user.id
    
    # 2. Test Create Course
    course_name = f"Test Course {datetime.now().strftime('%H%M%S')}"
    new_course = database.create_course(user_id, course_name)
    if new_course:
        st.write(f"Created Course: {new_course}")
        c_id = new_course['id']
        
        # 3. Test Create Unit
        new_unit = database.create_unit(c_id, "Unit 1 - Basics")
        if new_unit:
            st.write(f"Created Unit: {new_unit}")
            u_id = new_unit['id']
            
            # 4. Test Upload File
            success = database.upload_file_to_db(u_id, "test_note.txt", "This is a test content.", "note")
            if success:
                st.write("File uploaded.")
                
                # 5. Read File
                files = database.get_files(u_id)
                st.write("Files in Unit:", files)
            else:
                st.error("Upload failed")
        else:
            st.error("Unit creation failed")
    else:
        st.error("Course creation failed")

else:
    st.error("Login failed completely.")
