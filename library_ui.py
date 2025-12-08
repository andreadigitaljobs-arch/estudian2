
import streamlit as st
import time
import os
import pandas as pd
from database import get_units, create_unit, upload_file_to_db, get_files, delete_file, rename_file

def render_library(assistant):
    """
    Renders the dedicated "Digital Library" (Drive-style) tab.
    """
    
    # --- CSS for Cards ---
    st.markdown("""
    <style>
    div.stButton > button.folder-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        color: #334155;
        padding: 20px;
        width: 100%;
        text-align: left;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    div.stButton > button.folder-card:hover {
        border-color: #7c3aed;
        background-color: #faf5ff;
        box-shadow: 0 4px 6px -1px rgba(124, 58, 237, 0.1);
        color: #7c3aed;
    }
    </style>
    """, unsafe_allow_html=True)

    current_course_id = st.session_state.get('current_course_id')
    current_course_name = st.session_state.get('current_course')
    
    if not current_course_id:
        st.info("👈 Selecciona un Diplomado en la barra lateral para ver su Biblioteca.")
        return

    # --- STATE MANAGEMENT ---
    if 'lib_current_unit_id' not in st.session_state: st.session_state['lib_current_unit_id'] = None
    if 'lib_current_unit_name' not in st.session_state: st.session_state['lib_current_unit_name'] = None

    # --- HEADER ---
    col_head, col_action = st.columns([3, 1])
    with col_head:
        if st.session_state['lib_current_unit_id']:
            # Breadcrumb
            if st.button("⬅️ Mi Unidad", type="secondary"):
                st.session_state['lib_current_unit_id'] = None
            st.markdown(f"## 📂 {st.session_state['lib_current_unit_name']}")
        else:
            st.markdown(f"## ☁️ Mi Unidad: {current_course_name}")

    with col_action:
        # "New" Button Logic (Expander)
        with st.popover("➕ Nuevo", use_container_width=True):
             render_upload_modal(current_course_id, assistant)

    st.divider()

    # --- MAIN VIEW ---
    if st.session_state['lib_current_unit_id'] is None:
        # === ROOT VIEW (FOLDERS) ===
        db_units = get_units(current_course_id)
        
        # Add "Global Memory" card first?
        # Regular Folders
        
        if not db_units:
            st.caption("Carpeta vacía. ¡Crea la primera!")
            
        # Grid Layout (3 cols)
        cols = st.columns(3)
        for i, unit in enumerate(db_units):
            with cols[i % 3]:
                # Hack to make button look like card
                label = f"📁 {unit['name']}"
                if st.button(label, key=f"btn_unit_{unit['id']}", use_container_width=True):
                    st.session_state['lib_current_unit_id'] = unit['id']
                    st.session_state['lib_current_unit_name'] = unit['name']
                    st.rerun()

    else:
        # === FOLDER VIEW (FILES) ===
        unit_id = st.session_state['lib_current_unit_id']
        files = get_files(unit_id)
        
        if not files:
            st.info("Carpeta vacía. Usa el botón '➕ Nuevo' arriba para subir contenido.")
        else:
            # Table View
            # Using dataframes for clean look? Or custom list?
            # Custom list allows actions.
            
            for f in files:
                c1, c2, c3, c4 = st.columns([0.5, 3, 1, 1])
                with c1:
                    icon = "📄"
                    if f['type'] == 'pdf': icon = "📕"
                    elif f['type'] == 'image': icon = "🖼️"
                    st.markdown(f"### {icon}")
                with c2:
                    st.markdown(f"**{f['name']}**")
                    st.caption(f"{f['created_at'][:10]}")
                with c3:
                    # Rename
                    pass 
                with c4:
                    if st.button("🗑️", key=f"del_f_{f['id']}", help="Eliminar archivo"):
                        if delete_file(f['id']):
                            st.success("Eliminado")
                            time.sleep(0.5)
                            st.rerun()
                st.divider()

def render_upload_modal(course_id, assistant):
    st.markdown("### Subir Contenido")
    
    # 1. Target (If passing course_id, we need to know where to put it)
    # If inside a folder, default to that folder.
    # If at root, ask for folder.
    
    current_unit_id = st.session_state.get('lib_current_unit_id')
    target_unit_id = current_unit_id
    
    db_units = get_units(course_id)
    unit_names = [u['name'] for u in db_units]
    
    if not current_unit_id:
        st.caption("Selecciona destino:")
        sel_opt = st.selectbox("Carpeta:", ["✨ Nueva Carpeta..."] + unit_names)
        
        new_folder_name = ""
        if sel_opt == "✨ Nueva Carpeta...":
             new_folder_name = st.text_input("Nombre:", placeholder="Ej: Unidad 1")
             # Logic to create folder happens on SAVE
        else:
            found = next((u for u in db_units if u['name'] == sel_opt), None)
            if found: target_unit_id = found['id']
    else:
        st.info(f"Guardando en: **{st.session_state['lib_current_unit_name']}**")

    # 2. Content
    topic = st.text_input("Nombre (Opcional):", placeholder="Ej: Resumen")
    mode = st.radio("Tipo:", ["📂 Archivo", "📝 Texto"], horizontal=True)
    
    if mode == "📂 Archivo":
        files = st.file_uploader("Elige archivos:", accept_multiple_files=True)
        if st.button("Subir", type="primary"):
            if not files: 
                 st.error("Faltan archivos")
                 return
                 
            # Resolve Target
            if not target_unit_id:
                # Create Folder Logic
                if sel_opt == "✨ Nueva Carpeta..." and new_folder_name:
                    ur = create_unit(course_id, new_folder_name)
                    if ur: target_unit_id = ur['id']
                    else: 
                        st.error("Error creando carpeta")
                        return
                else:
                    st.error("Selecciona carpeta")
                    return

            # Upload Logic
            with st.spinner("Subiendo..."):
                for idx, f in enumerate(files):
                    content = ""
                    # PDF Extraction Logic
                    if f.type == "application/pdf":
                        try:
                            content = assistant.extract_text_from_pdf(f.getvalue(), f.type)
                        except: content = "Error reading PDF"
                    elif f.type == "text/plain":
                        content = str(f.read(), "utf-8")
                    
                    # Name logic
                    fname = f.name
                    if topic:
                        fname = f"{topic}_{idx+1}.{f.name.split('.')[-1]}" if len(files)>1 else f"{topic}.{f.name.split('.')[-1]}"
                    
                    upload_file_to_db(target_unit_id, fname, content, "pdf" if f.type=="application/pdf" else "text")
                
                st.success("¡Listo!")
                time.sleep(1)
                st.rerun()

    else:
        txt = st.text_area("Pega texto:")
        if st.button("Guardar Texto", type="primary"):
            if not txt or not topic:
                st.error("Falta texto o nombre")
                return
            
             # Resolve Target (Copy Paste logic from above if needed, reusable?)
            if not target_unit_id:
                if sel_opt == "✨ Nueva Carpeta..." and new_folder_name:
                    ur = create_unit(course_id, new_folder_name)
                    if ur: target_unit_id = ur['id']
                    else: 
                        st.error("Error creando carpeta")
                        return
                        
            safe_name = "".join([c if c.isalnum() else "_" for c in topic]) + ".txt"
            upload_file_to_db(target_unit_id, safe_name, txt, "text")
            st.success("Texto Guardado")
            time.sleep(1)
            st.rerun()
