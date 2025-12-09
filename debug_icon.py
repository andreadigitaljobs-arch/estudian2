import streamlit as st
import os

st.title("Icon Debugger")

path = "assets/home_icon.png"

if os.path.exists(path):
    st.success(f"File exists: {path}")
    st.write(f"Size: {os.path.getsize(path)} bytes")
    st.image(path, caption="Home Icon from Assets")
else:
    st.error(f"File NOT found: {path}")
