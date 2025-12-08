
import streamlit as st
import time
import os
import pandas as pd
from database import get_units, create_unit, upload_file_to_db, get_files, delete_file, rename_file, rename_unit, delete_unit

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
            if st.button("⬅️ Mi Unidad", key="back_root", type="secondary"):
                st.session_state['lib_current_unit_id'] = None
                st.rerun()
                
            u_name = st.session_state['lib_current_unit_name']
            u_id = st.session_state['lib_current_unit_id']
            
            # FOLDER MANAGEMENT (Rename/Delete)
            c_name, c_tools = st.columns([0.6, 0.4])
            with c_name:
                st.markdown(f"## 📂 {u_name}")
            with c_tools:
                # Rename Popover
                with st.popover("⚙️ Ajustes Carpeta"):
                    new_u = st.text_input("Renombrar Carpeta:", value=u_name)
                    if st.button("Guardar Nombre"):
                        if new_u and new_u != u_name:
                             rename_unit(u_id, new_u)
                             st.session_state['lib_current_unit_name'] = new_u
                             st.success("Renombrado")
                             time.sleep(1)
                             st.rerun()
                    
                    st.divider()
                    
                    # Delete
                    if st.button("🗑️ Borrar Carpeta", type="primary"):
                        if delete_unit(u_id):
                            st.session_state['lib_current_unit_id'] = None
                            st.success("Carpeta borrada")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("No se pudo borrar (¿Tiene archivos?)")

        else:
            st.markdown(f"## ☁️ Mi Unidad: {current_course_name}")

    with col_action:
        # "New" Button Logic (Expander)
        with st.popover("➕ Nuevo", use_container_width=True):
             render_upload_modal(current_course_id, assistant)

    st.divider()

    # --- STATE INIT ---
    if 'lib_breadcrumbs' not in st.session_state: st.session_state['lib_breadcrumbs'] = []
    
    current_unit_id = st.session_state['lib_current_unit_id']
    
    # --- BREADCRUMBS UI ---
    bc_cols = st.columns([0.1, 0.9])
    with bc_cols[0]:
        if st.button("🏠", help="Ir a Inicio", key="home_btn"):
             st.session_state['lib_current_unit_id'] = None
             st.session_state['lib_current_unit_name'] = None
             st.session_state['lib_breadcrumbs'] = []
             st.rerun()
             
    with bc_cols[1]:
        # Show path: Home > Folder A > Folder B
        path_str = " / ".join([b['name'] for b in st.session_state['lib_breadcrumbs']])
        if current_unit_id:
             current_name = st.session_state.get('lib_current_unit_name', 'Carpeta')
             if not path_str: path_str = f"{current_name}"
             else: path_str += f" / {current_name}"
        else:
             path_str = "Inicio"
        
        st.caption(f"📍 {path_str}")

    st.divider()

    # --- MAIN VIEW (UNIFIED) ---
    
    # 1. FETCH SUBFOLDERS
    # We pass current_unit_id as parent_id (or None for root)
    subfolders = get_units(current_course_id, parent_id=current_unit_id)
    
    # 2. RENDER FOLDERS (Grid)
    if subfolders:
        st.markdown("##### 📁 Carpetas")
        cols = st.columns(3)
        for i, unit in enumerate(subfolders):
            with cols[i % 3]:
                label = f"📁 {unit['name']}"
                if st.button(label, key=f"btn_unit_{unit['id']}", use_container_width=True):
                    # ENTER FOLDER
                    st.session_state['lib_current_unit_id'] = unit['id']
                    st.session_state['lib_current_unit_name'] = unit['name']
                    # Add to breadcrumbs
                    st.session_state['lib_breadcrumbs'].append({'id': unit['id'], 'name': unit['name']})
                    st.rerun()
                    
        # --- BULK DELETE (For current level) ---
        with st.expander("🗑️ Gestión Masiva / Papelera"):
            st.caption("Selecciona carpetas de este nivel para eliminar.")
            unit_options = {u['name']: u['id'] for u in subfolders}
            selected_names = st.multiselect("Carpetas:", list(unit_options.keys()), key=f"bd_{current_unit_id}")
            
            if selected_names:
                st.warning(f"⚠️ Eliminarás {len(selected_names)} carpetas y TODO su contenido.")
                if st.button(f"🗑️ Eliminar Selección", key=f"del_sel_{current_unit_id}", type="primary"):
                    deleted_count = 0
                    for name in selected_names:
                        if delete_unit(unit_options[name]): deleted_count += 1
                    
                    if deleted_count > 0:
                        st.success(f"✅ {deleted_count} eliminados.")
                        time.sleep(1)
                        st.rerun()
        st.divider()
    elif not current_unit_id:
        st.info("No hay carpetas. Crea una nueva ➕")

    # 3. RENDER FILES (If not root, or if root allows files)
    # We usually only show files if we are INSIDE a folder (unit_id is not None)
    # But if your app supports root files, remove the check. 
    # Provided code only fetches files for unit_id.
    
    if current_unit_id:
        st.markdown(f"##### 📄 Archivos en '{st.session_state.get('lib_current_unit_name')}'")
        files = get_files(current_unit_id)
        
        if not files:
            st.caption("Esta carpeta no tiene archivos.")
        else:
             # ... EXISTING FILE RENDERING LOOP ...
             # Since I am replacing the outer block, I need to keep the inner file loop.
             # I will copy the file loop from previous context or rewrite it concisely?
             # I should try to preserve the existing logic.
             pass 
             # Wait, replace_file_content replaces the BLOCK.
             # I need to output the file loop here.
             
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
                    new_name = st.text_input("Renombrar:", value=f['name'], key=f"ren_f_{f['id']}", label_visibility="collapsed")
                    if new_name != f['name']:
                         if st.button("💾", key=f"save_ren_f_{f['id']}", help="Guardar"):
                             rename_file(f['id'], new_name)
                             st.rerun()

                with c4:
                    if st.button("🗑️", key=f"del_f_{f['id']}", help="Eliminar"):
                        if delete_file(f['id']):
                            st.success("Eliminado")
                            time.sleep(0.5)
                            st.rerun()
                
                content = f.get('content_text')
                if content:
                    with st.expander("👁️ Ver Contenido"):
                        st.markdown(content, unsafe_allow_html=True)
                
                st.divider()

def render_upload_modal(course_id, assistant):
    st.markdown("### Subir Contenido")
    
    # 1. Target (If passing course_id, we need to know where to put it)
    current_unit_id = st.session_state.get('lib_current_unit_id')
    target_unit_id = current_unit_id
    
    # Fetch ALL units (recursive) so we can upload to subfolders
    db_units = get_units(course_id, fetch_all=True)
    unit_names = [u['name'] for u in db_units]
    
    if not current_unit_id:
        st.caption("Selecciona destino:")
        sel_opt = st.selectbox("Carpeta:", ["✨ Nueva Carpeta..."] + unit_names)
        
        new_folder_name = ""
        if sel_opt == "✨ Nueva Carpeta...":
             new_folder_name = st.text_input("Nombre de carpeta:", placeholder="Ej: Unidad 1")
        else:
            found = next((u for u in db_units if u['name'] == sel_opt), None)
            if found: target_unit_id = found['id']
    else:
        st.info(f"Guardando en: **{st.session_state['lib_current_unit_name']}**")

    # 2. Content
    topic = st.text_input("Nombre de archivo (Opcional para carpetas):", placeholder="Ej: Resumen")
    mode = st.radio("Tipo:", ["📂 Archivo", "📝 Texto", "📥 Importar Chat (Masivo)", "✨ Crear Carpeta"], horizontal=True)
    
    if mode == "✨ Crear Carpeta":
        st.info("Crea una carpeta vacía dentro de la ubicación actual.")
        new_folder_pure = st.text_input("Nombre de la Nueva Carpeta:", placeholder="Ej: Capítulos")
        
        if st.button("Crear Carpeta Sola", type="primary"):
            if new_folder_pure:
                # Use current_unit_id as parent so it nests correctly
                create_unit(course_id, new_folder_pure, parent_id=current_unit_id)
                st.success(f"Carpeta '{new_folder_pure}' creada.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Escribe un nombre.")

    elif mode == "📂 Archivo":
        files = st.file_uploader("Elige archivos:", accept_multiple_files=True)
        if st.button("Subir", type="primary"):
            if not files: 
                 st.error("Faltan archivos")
                 return
                 
            # Resolve Target
            if not target_unit_id:
                if sel_opt == "✨ Nueva Carpeta..." and new_folder_name:
                    ur = create_unit(course_id, new_folder_name)
                    if ur: target_unit_id = ur['id']
                    else: return
                else: return

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
                         content = str(f.read(), "utf-8", errors='ignore')
                    
                    # Name logic
                    fname = f.name
                    if topic:
                        fname = f"{topic}_{idx+1}.{f.name.split('.')[-1]}" if len(files)>1 else f"{topic}.{f.name.split('.')[-1]}"
                    
                    upload_file_to_db(target_unit_id, fname, content, "pdf" if f.type=="application/pdf" else "text")
                
                st.success("¡Listo!")
                time.sleep(1)
                st.rerun()

    elif mode == "📝 Texto":
        txt = st.text_area("Pega texto:")
        if st.button("Guardar Texto", type="primary"):
            if not txt or not topic:
                st.error("Falta texto o nombre")
                return
            
            # Resolve Target
            if not target_unit_id:
                if sel_opt == "✨ Nueva Carpeta..." and new_folder_name:
                    ur = create_unit(course_id, new_folder_name)
                    if ur: target_unit_id = ur['id']
                    else: return

            safe_name = "".join([c if c.isalnum() else "_" for c in topic]) + ".txt"
            upload_file_to_db(target_unit_id, safe_name, txt, "text")
            st.success("Texto Guardado")
            time.sleep(1)
            st.rerun()

    elif mode == "📥 Importar Chat (Masivo)":
        st.markdown("#### 🤖 Asistente de Importación")
        st.caption("Conversa con tu archivo para organizarlo perfectamente.")

        # --- STATE MANAGEMENT FOR IMPORT ---

        # --- STATE MANAGEMENT FOR IMPORT ---
        if 'imp_stage' not in st.session_state: st.session_state['imp_stage'] = 'upload'
        if 'imp_file_content' not in st.session_state: st.session_state['imp_file_content'] = None
        if 'imp_history' not in st.session_state: st.session_state['imp_history'] = []

        # 1. UPLOAD STAGE
        if st.session_state['imp_stage'] == 'upload':
            c_file = st.file_uploader("Sube tu archivo (.txt):", type=["txt"], key="imp_uploader")
            if c_file:
                # Read immediately
                raw = c_file.getvalue().decode("utf-8", errors='ignore')
                st.session_state['imp_file_content'] = raw
                
                # --- AUTO-SAVE SOURCE (Core Upgrade) ---
                # Save the raw file immediately so it's never lost
                if not st.session_state.get('imp_source_saved'):
                    u_id = st.session_state.get('lib_current_unit_id')
                    if not u_id:
                        # Fallback: try to find a default or create one? 
                        # Ideally user should be in a folder. If not, maybe skip or save to "General"?
                        # For now, let's try to get the first unit available.
                        units = get_units(course_id)
                        if units: u_id = units[0]['id']
                    
                    if u_id:
                         # Prefix with [FUENTE] to distinguish
                         src_name = f"[FUENTE] {c_file.name}"
                         upload_file_to_db(u_id, src_name, raw, "text")
                         st.toast(f"💾 Fuente original guardada: {src_name}")
                         st.session_state['imp_source_saved'] = True
                # ---------------------------------------

                st.session_state['imp_stage'] = 'analyzing'
                st.rerun()

        # 2. ANALYSIS STAGE (Auto-Transition)
        elif st.session_state['imp_stage'] == 'analyzing':
            with st.spinner("Leyendo archivo..."):
                summary = assistant.analyze_import_file(st.session_state['imp_file_content'])
                st.session_state['imp_history'].append({"role": "assistant", "content": summary})
                st.session_state['imp_stage'] = 'chatting'
                st.rerun()

        # 3. CHATTING STAGE
        elif st.session_state['imp_stage'] == 'chatting':
            # Restart Button
            if st.button("🔄 Subir otro archivo"):
                st.session_state['imp_stage'] = 'upload'
                st.session_state['imp_history'] = []
                st.session_state['imp_file_content'] = None
                st.rerun()

            st.divider()
            
            # Chat Container
            chat_container = st.container(height=400)
            with chat_container:
                for msg in st.session_state['imp_history']:
                    with st.chat_message(msg['role']):
                        st.markdown(msg['content'])

            # Input
            if prompt := st.chat_input("Ej: 'Guarda las fechas en la carpeta Calendario'"):
                # User Message
                st.session_state['imp_history'].append({"role": "user", "content": prompt})
                with chat_container:
                     with st.chat_message("user"):
                         st.markdown(prompt)

                # Assistant Response (Action or Text)
                with st.spinner("Procesando..."):
                    # Get available folders for context
                    db_units = get_units(course_id)
                    
                    response = assistant.chat_with_import_file(
                        st.session_state['imp_file_content'], 
                        prompt, 
                        st.session_state['imp_history'],
                        db_units
                    )
                    
                    # Check if Action (JSON)
                    if isinstance(response, dict):
                         # --- SMART BULK HANDLER (v3.0) ---
                         
                         # 1. Normalize actions to list
                         actions_list = []
                         if 'actions' in response:
                             actions_list = response['actions']
                         elif 'action_type' in response:
                             # Legacy single action
                             actions_list = [response]
                             
                         results = []
                         if not actions_list:
                             results.append("🤔 La IA respondió con JSON pero sin acciones claras.")

                         # 2. Iterate and Execute
                         for action in actions_list:
                             act_type = action.get('action_type')
                             
                             if act_type == 'create_folder':
                                  t_folder = action.get('target_folder', 'Sin Titulo')
                                  create_unit(course_id, t_folder)
                                  results.append(f"📁 Carpeta creada: **{t_folder}**")
                                  
                             elif act_type == 'save_file':
                                  t_folder = action.get('target_folder', 'General')
                                  f_name = action.get('file_name', 'archivo_ia.md')
                                  content_to_save = action.get('content', '')
                                  
                                  # Resolve Folder ID
                                  fresh_units = get_units(course_id)
                                  found = next((u for u in fresh_units if u['name'] == t_folder), None)
                                  
                                  target_id = None
                                  if not found:
                                      ur = create_unit(course_id, t_folder)
                                      target_id = ur['id'] if ur else None
                                  else:
                                      target_id = found['id']
                                      
                                  # Write to DB (RPC)
                                  if target_id and content_to_save:
                                      success = upload_file_to_db(target_id, f_name, content_to_save, "text")
                                      if success:
                                          results.append(f"✅ Guardado: **{f_name}** en *{t_folder}*")
                                      else:
                                          results.append(f"❌ Error DB al guardar {f_name}")
                                  else:
                                      results.append(f"⚠️ Contenido vacío para {f_name}")
                         
                         # 3. Consolidate Feedback
                         final_msg = "\n\n".join(results)
                         st.session_state['imp_history'].append({"role": "assistant", "content": final_msg})
                         st.rerun()
                        
                    else:
                        # Normal Text Response
                        st.session_state['imp_history'].append({"role": "assistant", "content": response})
                        st.rerun()
