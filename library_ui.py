
import streamlit as st
import time
import os
import base64
import pandas as pd
from database import get_units, create_unit, upload_file_to_db, get_files, delete_file, rename_file, rename_unit, delete_unit, create_chat_session, save_chat_message

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
    
    if not current_course_id:
        st.info("👈 Selecciona un Diplomado en la barra lateral para ver su Biblioteca.")
        return

    # --- STATE MANAGEMENT ---
    if 'lib_current_unit_id' not in st.session_state: st.session_state['lib_current_unit_id'] = None
    if 'lib_current_unit_name' not in st.session_state: st.session_state['lib_current_unit_name'] = None
    if 'lib_breadcrumbs' not in st.session_state: st.session_state['lib_breadcrumbs'] = []

    current_unit_id = st.session_state['lib_current_unit_id']

    # --- NAVIGATION UI ---
    # FIX: Tighter columns [0.1, 0.1, 0.8] to keep buttons grouped "pegaditos"
    col_nav = st.columns([0.1, 0.1, 0.8])
    
    with col_nav[0]:
        # Home Button
        if st.button("🏠 Inicio", key="home_btn", help="Volver al Inicio"):
             st.session_state["lib_current_unit_id"] = None
             st.session_state["lib_current_unit_name"] = None
             st.session_state["lib_breadcrumbs"] = []
             st.rerun()

    with col_nav[1]:
        # Back Button (Only if not at root)
        if current_unit_id:
            if st.button("⬅️ Atrás", key="back_btn", help="Subir un nivel"):
                # Logic: Pop current, go to previous
                if st.session_state['lib_breadcrumbs']:
                    st.session_state['lib_breadcrumbs'].pop() # Remove current
                    
                    if st.session_state['lib_breadcrumbs']:
                        # Go to parent
                        prev = st.session_state['lib_breadcrumbs'][-1]
                        st.session_state['lib_current_unit_id'] = prev['id']
                        st.session_state['lib_current_unit_name'] = prev['name']
                    else:
                        # Back to Home
                        st.session_state['lib_current_unit_id'] = None
                        st.session_state['lib_current_unit_name'] = None
                else:
                    # Fallback
                    st.session_state['lib_current_unit_id'] = None
                
                st.rerun()

    # --- FOLDER VIEW ---
    subfolders = get_units(current_course_id, parent_id=current_unit_id)
    
    if subfolders:
        st.markdown("##### 📁 Carpetas")
        cols = st.columns(3)
        for i, unit in enumerate(subfolders):
            with cols[i % 3]:
                if st.button(f"📁 {unit['name']}", key=f"btn_unit_{unit['id']}", use_container_width=True):
                    st.session_state['lib_current_unit_id'] = unit['id']
                    st.session_state['lib_current_unit_name'] = unit['name']
                    st.session_state['lib_breadcrumbs'].append({'id': unit['id'], 'name': unit['name']})
                    st.rerun()
                    
        # Management Section (Rename & Delete)
        with st.expander("⚙️ Gestión de Carpetas (Renombrar/Borrar)"):
            c_rename, c_delete = st.columns(2, gap="large")
            
            # 1. DEFINE OPTIONS FIRST
            unit_options = {u['name']: u['id'] for u in subfolders}
            
            # 2. CONSULTANT FIX: PROTECT SYSTEM FOLDERS
            # We filter out these folders so they cannot be Renamed or Deleted.
            SYSTEM_FOLDERS = ["Transcriptor", "Apuntes Simples", "Guía de Estudio", "Transcripts", "Notes", "Guides"]
            
            # 3. FILTER
            editable_units = {name: uid for name, uid in unit_options.items() if name not in SYSTEM_FOLDERS}
            
            with c_rename:
                st.markdown("###### ✏️ Renombrar Carpeta")
                
                if not editable_units:
                    st.caption("No hay carpetas personalizadas para renombrar.")
                else:
                    sel_rename = st.selectbox("Selecciona carpeta:", ["-- Seleccionar --"] + list(editable_units.keys()), key="ren_unit_sel")
                    
                    if sel_rename != "-- Seleccionar --":
                        new_name = st.text_input("Nuevo nombre:", key="ren_new_name")
                        if st.button("Renombrar Carpeta", use_container_width=True):
                            if new_name:
                                 target_id = editable_units[sel_rename]
                                 if rename_unit(target_id, new_name):
                                     st.success(f"Renombrado a '{new_name}'")
                                     time.sleep(1)
                                     st.rerun()
                                 else:
                                     st.error("Error al renombrar.")
                            else:
                                 st.warning("Escribe un nuevo nombre.")

            with c_delete:
                st.markdown("###### 🗑️ Borrar Carpeta(s)")
                
                if not editable_units:
                     st.caption("No hay carpetas personalizadas para borrar.")
                else:
                    # Bulk Selection
                    pass
                    sel_del_list = st.multiselect("Selecciona carpetas para borrar:", list(editable_units.keys()), key="del_unit_mul")
                    
                    if sel_del_list:
                        count = len(sel_del_list)
                        st.warning(f"⚠️ ¿Seguro que quieres borrar {count} carpeta(s) y TODO su contenido?")
                        if st.button(f"Sí, Borrar {count} Carpetas", type="primary", use_container_width=True):
                            success_count = 0
                            fail_count = 0
                            
                            progress_bar = st.progress(0)
                            for i, name in enumerate(sel_del_list):
                                 target_id = editable_units[name]
                                 if delete_unit(target_id):
                                     success_count += 1
                                 else:
                                     fail_count += 1
                                 progress_bar.progress((i + 1) / count)
                            
                            if fail_count == 0:
                                 st.success(f"✅ {success_count} carpetas eliminadas correctamente.")
                            else:
                                 st.warning(f"⚠️ {success_count} eliminadas, {fail_count} fallaron.")
                                 
                            time.sleep(1)
                            st.rerun()
        st.write("") # Spacer instead of divider
    elif not current_unit_id:
        st.info("No hay carpetas. Crea una nueva ➕")

    # --- FILE VIEW ---
    # Global callback to close popovers
    def close_all_popovers():
        st.session_state['popover_reset_token'] += 1
        st.session_state['popover_needs_reset'] = True # Trigger flicker
        st.toast("Menú cerrado", icon="✅")

    if current_unit_id:
        st.markdown(f"##### 📄 Archivos en '{st.session_state.get('lib_current_unit_name')}'")
        files = get_files(current_unit_id)
        
        # Check reset flag
        should_reset = st.session_state.get('popover_needs_reset', False)

        if not files:
            st.caption("Carpeta vacía.")
        else:
            for f in files:
                # COMPACT LAYOUT
                c1, c2, c3, c4 = st.columns([0.1, 0.7, 0.1, 0.1], vertical_alignment="bottom")
                
                with c1:
                    icon = "📄" if f['type'] == "text" else "📕"
                    st.write(f"## {icon}")
                
                with c2:
                    st.markdown(f"**{f['name']}**")
                    with st.expander("Ver contenido"):
                        safe_content = f.get('content') or f.get('content_text') or ""
                        st.markdown(safe_content, unsafe_allow_html=True)

                with c3:
                    # CONSULTANT: SMART POPOVER (Choice Menu)
                    # NUCLEAR RESET: If resetting, render a dummy button -> Forces Popover unmount
                    if should_reset:
                        st.button("⚡", key=f"dummy_reset_{f['id']}", disabled=True, help="Refrescando...")
                    else:
                        # Normal Popover Render using rotating identity
                        token = st.session_state.get('popover_reset_token', 0)
                        suffix_char = "." if (token % 2 != 0) else ""
                        pop_label = f"⚡{suffix_char}" 
                        pop_help = f"Acciones Rápidas {suffix_char}"

                        with st.popover(pop_label, help=pop_help):
                            # Layout: Title + Close Button
                            p_col1, p_col2 = st.columns([0.8, 0.2])
                            with p_col1:
                                st.markdown(f"<div style='margin-top: 10px; font-weight: bold;'>{f['name']}</div>", unsafe_allow_html=True)
                            with p_col2:
                                # 'X' button to close popover
                                st.button("✖", key=f"close_pop_{f['id']}", help="Cerrar menú", on_click=close_all_popovers)
                            
                            st.divider() # Neat separator
                            
                            if st.button("🤖 Resolver Tarea", key=f"btn_task_{f['id']}", use_container_width=True):
                                st.session_state['chat_context_file'] = f
                                st.session_state['redirect_target_name'] = "Ayudante de Tareas"
                                st.session_state['force_chat_tab'] = True
                                st.rerun()
                                
                            if st.button("👨🏻‍🏫 Hablar con Profe", key=f"btn_tutor_{f['id']}", use_container_width=True):
                                st.session_state['chat_context_file'] = f
                                if 'user' in st.session_state:
                                    uid = st.session_state['user'].id
                                    sess_name = f"Análisis: {f['name']}"
                                    new_sess = create_chat_session(uid, sess_name)
                                    st.session_state['current_chat_session'] = new_sess
                                    st.session_state['tutor_chat_history'] = [] 
                                    prompt_msg = f"He abierto el archivo **{f['name']}**. ¿Me puedes dar un resumen o interpretación de su contenido?"
                                    st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt_msg})
                                st.session_state['redirect_target_name'] = "Tutoria 1 a 1"
                                st.session_state['force_chat_tab'] = True
                                st.rerun()

                with c4:
                    if st.button("🗑️", key=f"del_{f['id']}", help="Eliminar archivo"):
                        if delete_file(f['id']):
                            st.toast(f"Archivo eliminado: {f['name']}")
                            time.sleep(0.5)
                            st.rerun()
                            
            # END OF LOOP - HANDLE RESET
            if should_reset:
                st.session_state['popover_needs_reset'] = False
                st.rerun()
    
    # --- ACTION AREA (Upload/Create) ---
    st.markdown("### ➕ Añadir Contenido")
    
    target_unit_id = current_unit_id
    
    # If root, allow valid selection
    if not current_unit_id:
        all_units = get_units(current_course_id, fetch_all=True)
        u_map = {u['name']: u['id'] for u in all_units}
        sel = st.selectbox("Destino:", ["✨ Nueva Carpeta..."] + list(u_map.keys()))
        if sel == "✨ Nueva Carpeta...":
             new_folder_name = st.text_input("Nombre de Carpeta:", placeholder="Ej: Unidad 1")
        else:
             target_unit_id = u_map[sel]
    else:
        new_folder_name = None
    
    tab2, tab1, tab4, tab3 = st.tabs(["✨ Crear Carpeta", "📂 Subir Archivos", "✍🏻 Escribir contenido", "📥 Importar chat masivo"])
    
    with tab1:
        upl_files = st.file_uploader("Archivos (PDF, TXT, Imágenes):", accept_multiple_files=True)
        if st.button("Subir Archivos", type="primary"):
            if not target_unit_id:
                 # Check if user entered a new folder name
                 if new_folder_name:
                     res = create_unit(current_course_id, new_folder_name, parent_id=None)
                     if res: target_unit_id = res['id']
                 else:
                     st.error("Selecciona una carpeta destino o crea una nueva.")
                     st.stop()
            
            if target_unit_id and upl_files:
                for uf in upl_files:
                    try:
                        content = ""
                        # Simple text handler for now, can be expanded
                        if uf.type in ["text/plain", "application/json", "text/markdown"]:
                            content = str(uf.read(), "utf-8", errors='ignore')
                        elif uf.type == "application/pdf":
                             # If assistant has pdf extractor, use it, else placeholder
                             if hasattr(assistant, 'extract_text_from_pdf'):
                                 content = assistant.extract_text_from_pdf(uf.getvalue())
                             else:
                                 content = "PDF Content Placeholder"
                        else:
                            content = f"Binary content: {uf.name}"
                            
                        upload_file_to_db(target_unit_id, uf.name, content, "text")
                    except Exception as e:
                        st.error(f"Error subiendo {uf.name}: {e}")
                st.success("¡Archivos subidos correctamente!")
                time.sleep(1)
                st.rerun()
    
    with tab2:
        nf_name = st.text_input("Nombre de sub-carpeta:", key="new_sub_folder")
        if st.button("Crear Carpeta"):
            if nf_name:
                create_unit(current_course_id, nf_name, parent_id=current_unit_id)
                st.rerun()

    with tab4:
        st.markdown("###### 📝 Editor de Texto Simple")
        
        # Folder Selection for Saving
        all_units = get_units(current_course_id, fetch_all=True)
        if not all_units:
            st.warning("Primero crea una carpeta en la pestaña 'Crear Carpeta'.")
        else:
            unit_opts = {u['name']: u['id'] for u in all_units}
            # Default to current if set
            def_idx = 0
            if current_unit_id and current_unit_id in unit_opts.values():
                 def_name = next(k for k,v in unit_opts.items() if v == current_unit_id)
                 if def_name in list(unit_opts.keys()):
                     def_idx = list(unit_opts.keys()).index(def_name)
            
            sel_target_name = st.selectbox("Guardar en:", list(unit_opts.keys()), index=def_idx, key="save_note_target")
            target_save_id = unit_opts[sel_target_name]

            note_title = st.text_input("Título de la nota (ej: Resumen.txt):", placeholder="Mi_Nota.txt", key="new_note_title")
            note_content = st.text_area("Contenido:", height=200, placeholder="Escribe o pega tu texto aquí...", key="new_note_content")
            
            c_save, c_clear = st.columns([0.2, 0.8])
            
            # Clear Button Logic
            if c_clear.button("🗑️ Borrar todo"):
                st.session_state['new_note_content'] = ""
                st.rerun()

            if c_save.button("💾 Guardar Nota", type="primary", use_container_width=True):
                if not note_title:
                    st.error("Escribe un título para la nota.")
                elif not note_content:
                    st.error("La nota está vacía.")
                else:
                    # Append .txt if missing
                    final_name = note_title
                    if "." not in final_name: final_name += ".txt"
                    
                    try:
                        upload_file_to_db(target_save_id, final_name, note_content, "text")
                        st.success(f"✅ Nota '{final_name}' guardada en '{sel_target_name}'.")
                        time.sleep(1)
                        # Optional: Don't rerun whole app if you want to stay here, but refreshing shows file in list if visible
                        # User requested NOT to be redirected. So simple check.
                        # We are in Tab4. Rerun keeps us in Tab4 if st.session_state of tabs is managed, but st.tabs usually resets.
                        # Wait, st.tabs usually resets to first tab on rerun unless we track active tab index?
                        # Streamlit doesn't natively track active tab index easily without component.
                        # But rewriting the UI might stay looking similar. 
                        # Let's try basic rerun first as it refreshes data.
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando nota: {e}")

    with tab3:
        st.markdown("###### 🧠 Importador Inteligente de Historiales")
        st.caption("Conversa con la IA para organizar tu archivo. Pídele resúmenes, extraer fechas o dividir por temas.")
        
        chat_file = st.file_uploader("Sube el historial del chat:", type=['txt', 'json', 'md'], key="chat_import_upl")
        
        # Session State for Import Chat
        if 'import_chat_history' not in st.session_state: st.session_state['import_chat_history'] = []
        
        if chat_file is not None:
            raw_text = str(chat_file.read(), "utf-8", errors='ignore')
            
            # --- INITIAL ANALYSIS (Agent Kickoff) ---
            if 'last_imported_file' not in st.session_state or st.session_state['last_imported_file'] != chat_file.name:
                st.session_state['import_chat_history'] = [] # Reset history on new file
                st.session_state['last_imported_file'] = chat_file.name
                
                with st.spinner("🤖 Analizando archivo..."):
                    greeting = assistant.analyze_import_file(raw_text)
                    st.session_state['import_chat_history'].append({"role": "assistant", "content": greeting})
            
            # --- CHAT UI ---
            # Display History
            for msg in st.session_state['import_chat_history']:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
                    
            # Chat Input
            if prompt := st.chat_input("Escribe tu instrucción (ej: 'Separa los temas de Marketing')"):
                # 1. User Message
                st.session_state['import_chat_history'].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # 2. Assistant Response
                with st.chat_message("assistant"):
                    with st.spinner("Procesando y organizando..."):
                        # Get existing folders to help AI decide
                        all_units = get_units(current_course_id, fetch_all=True)
                        response_payload = assistant.chat_with_import_file(raw_text, prompt, st.session_state['import_chat_history'], available_folders=all_units)
                        
                        # LOGIC: Check if it's JSON Actions or just Text
                        final_msg_content = ""
                        
                        if isinstance(response_payload, dict) and "actions" in response_payload:
                            # It's an Action!
                            thoughts = response_payload.get("thoughts", "Procesando acciones...")
                            st.markdown(thoughts)
                            final_msg_content += f"{thoughts}\n\n"
                            
                            actions = response_payload.get("actions", [])
                            for action in actions:
                                act_type = action.get("action_type")
                                t_folder = action.get("target_folder")
                                f_name = action.get("file_name")
                                f_content = action.get("content")
                                
                                if act_type == "save_file":
                                    # 1. Find or Create Folder
                                    # Try to find existing first
                                    target_uid = None
                                    for u in all_units:
                                        if u['name'].lower() == t_folder.lower():
                                            target_uid = u['id']
                                            break
                                    
                                    # Create if not exists
                                    if not target_uid:
                                        res = create_unit(current_course_id, t_folder, parent_id=current_unit_id) # create in current root or sub
                                        if res: 
                                            target_uid = res['id']
                                            st.toast(f"📂 Carpeta creada: {t_folder}", icon="✨")
                                    
                                    # 2. Save File
                                    if target_uid:
                                        upload_file_to_db(target_uid, f_name, f_content, "text")
                                        st.success(f"✅ Archivo guardado: **{t_folder}/{f_name}**")
                                        final_msg_content += f"- ✅ Guardado: `{t_folder}/{f_name}`\n"
                                    else:
                                        st.error(f"Error accediendo a carpeta {t_folder}")
                                
                        else:
                            # Just Plain Text
                            st.markdown(response_payload)
                            final_msg_content = response_payload
                        
                        # Append to history
                        st.session_state['import_chat_history'].append({"role": "assistant", "content": final_msg_content})
                        
                        # Refresh to show new files in background? Not strictly necessary if we rely on Toast, but user might want to see.
                        # We won't rerun broadly to avoid resetting chat, relying on the 'success' messages.
        
