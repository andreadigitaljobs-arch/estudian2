
import streamlit as st
import time
import os
import base64
import pandas as pd
import re
import io
import zipfile
from db_handler import (
    get_units, create_unit, upload_file_to_db, get_files, delete_file, 
    rename_file, rename_unit, delete_unit, create_chat_session, save_chat_message, 
    search_library, update_user_footprint, get_course_files, move_file, 
    get_course_file_counts, move_file_up, move_file_down, ensure_unit_numbering,
    get_full_course_backup, update_file_content
)
import streamlit.components.v1 as components

# V308: Safe import with fallback
try:
    from streamlit_quill import st_quill
    QUILL_AVAILABLE = True
except ImportError:
    QUILL_AVAILABLE = False
    print("Warning: streamlit-quill not available, using fallback editor")

def format_transcript_with_ai(raw_text, assistant):
    """
    Uses AI to format a raw transcript with proper paragraphs and structure.
    Does NOT change content, only formatting.
    """
    if not assistant or not raw_text:
        return raw_text
    
    prompt = f"""
ERES UN EDITOR PROFESIONAL. Tu tarea es FORMATEAR esta transcripción.

REGLAS ESTRICTAS:
1. 📍 NO CAMBIES EL CONTENIDO. Solo reorganiza la estructura.
2. 📝 Detecta cambios de tema y crea TÍTULOS (## Título)
3. ✂️ Separa en PÁRRAFOS lógicos (cada 3-5 oraciones relacionadas)
4. 👥 MANTÉN la diarización (**Hablante X:**) si existe
5. 🎨 Aplica MODO ESTUDIO (colores HTML) a conceptos clave:
   - 🔴 <span class="sc-base">...</span> -> DEFINICIONES
   - 🟣 <span class="sc-key">...</span> -> IDEAS CLAVE
   - 🟡 <span class="sc-data">...</span> -> DATOS/ESTRUCTURA
   - 🔵 <span class="sc-example">...</span> -> EJEMPLOS
   - 🟢 <span class="sc-note">...</span> -> MATICES

TRANSCRIPCIÓN ORIGINAL:
{raw_text}

DEVUELVE SOLO LA TRANSCRIPCIÓN FORMATEADA. NO agregues explicaciones.
"""
    
    try:
        response = assistant.model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error al formatear: {e}")
        return raw_text


def clean_markdown_v3(text):
    """Removes all markdown baggage for a perfect copy."""
    import re
    if not text: return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Headers #
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Bold/Italic ** * __ _
    text = re.sub(r'(\*\*|__|\*|_)', '', text)
    # Bullets / Lists
    text = re.sub(r'^[ \t]*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    # Blockquotes >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # Links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Code blocks `
    text = text.replace("`", "")
    # Strange symbols mentioned by user: @
    text = text.replace("@", "")
    # Remove excessive empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def render_library_v2(assistant):
    """
    Renders the dedicated "Digital Library" (Drive-style) tab.
    Refactored V270: Minimalist Toolbar UI
    """
    
    # --- CSS for Windows Explorer Style Folders ---
    st.markdown("""
    <style>
    /* Folder Card Hover Effects */
    .folder-hover-card {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        transition: all 0.1s ease;
    }
    .folder-hover-card:hover {
        background-color: rgba(224, 242, 254, 0.5) !important;
        border-color: rgba(186, 230, 253, 0.8) !important;
        transform: scale(1.02) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    current_course_id = st.session_state.get('current_course_id')
    
    if not current_course_id:
        st.info("👈 Selecciona un Diplomado en la barra lateral para ver su Biblioteca.")
        return

    # --- STATE INITIALIZATION ---
    if 'lib_current_unit_id' not in st.session_state: st.session_state['lib_current_unit_id'] = None
    if 'lib_current_unit_name' not in st.session_state: st.session_state['lib_current_unit_name'] = None
    if 'lib_breadcrumbs' not in st.session_state: st.session_state['lib_breadcrumbs'] = []
    if 'lib_active_tool' not in st.session_state: st.session_state['lib_active_tool'] = None # 'upload', 'create', 'manage', 'backup', 'search'

    # --- DASHBOARD TRIGGER HANDLING ---
    if st.session_state.get('lib_auto_open_upload'):
        st.session_state['lib_active_tool'] = 'upload'
        st.session_state['lib_auto_open_upload'] = False
        # Optional: Toast to confirm
        # st.toast("Modo de subida activado")

    # ==========================================
    # 1. TOOLBAR (Minimalist Top Menu)
    # ==========================================
    
    # Helper to set tool
    def set_tool(tool_name):
        if st.session_state['lib_active_tool'] == tool_name:
            st.session_state['lib_active_tool'] = None # Toggle off
        else:
            st.session_state['lib_active_tool'] = tool_name

    # Toolbar Layout
    # v113: Added Cleaner Tool -> 7 cols
    t_c1, t_c2, t_c3, t_c4, t_c5, t_c6, t_c7 = st.columns([0.15, 0.14, 0.14, 0.14, 0.14, 0.14, 0.15])
    
    # Define button styles based on active state
    def get_type(tool_name):
        return "primary" if st.session_state['lib_active_tool'] == tool_name else "secondary"

    with t_c1:
        if st.button("📂 Raíz", use_container_width=True, help="Ir a la carpeta principal"):
            st.session_state['lib_current_unit_id'] = None
            st.session_state['lib_current_unit_name'] = None
            st.session_state['lib_breadcrumbs'] = []
            st.session_state['lib_active_tool'] = None # Close tools
            st.rerun()

    with t_c2:
        if st.button("📤 Subir", type=get_type('upload'), use_container_width=True, help="Subir archivos o crear notas"):
            set_tool('upload')
            st.rerun()

    with t_c3:
        if st.button("✨ Nueva", type=get_type('create'), use_container_width=True, help="Crear nueva carpeta"):
            set_tool('create')
            st.rerun()

    with t_c4:
        if st.button("⚙️ Gestión", type=get_type('manage'), use_container_width=True, help="Renombrar o borrar carpetas"):
            set_tool('manage')
            st.rerun()

    with t_c5:
        if st.button("🔍 Buscar", type=get_type('search'), use_container_width=True, help="Buscar en toda la biblioteca"):
            set_tool('search')
            st.rerun()

    with t_c6:
        # CLEANER BUTTON
        if st.button("🧹 Limpieza", type=get_type('cleaner'), use_container_width=True, help="Encontrar y eliminar duplicados"):
            set_tool('cleaner')
            st.rerun()

    with t_c7:
         if st.button("📦 Backup", type=get_type('backup'), use_container_width=True, help="Descargar todo"):
            set_tool('backup')
            st.rerun()

    # Custom Separator (Minimalist)
    # Only show if a tool is active to separate it, otherwise just a thin line or nothing if very tight
    if st.session_state['lib_active_tool']:
         st.markdown("---")
    else:
         # Ultra thin separator when no tool is open
         st.markdown("<hr style='margin: 0px 0 10px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

    # ==========================================
    # 2. ACTION PANEL (Context Specific)
    # ==========================================
    
    tool = st.session_state['lib_active_tool']
    current_unit_id = st.session_state['lib_current_unit_id']

    if tool:
        with st.container(border=True):
            
            # --- UPLOAD TOOL ---
            if tool == 'upload':
                st.markdown("#### 📤 Subir Contenido")
                
                # Show current location
                current_location = st.session_state.get('lib_current_unit_name', 'Raíz')
                if current_unit_id:
                    st.info(f"📍 Subirás archivos a: **{current_location}**")
                else:
                    st.warning("⚠️ Estás en la raíz. Los archivos se subirán a la primera carpeta disponible o se creará una carpeta 'General'.")
                
                # Tabs for different upload types
                up_t1, up_t2, up_t3 = st.tabs(["📂 Archivos", "✍🏻 Nota Rápida", "📥 Importar Chat"])
                
                with up_t1:
                    upl_files = st.file_uploader("Arrastra tus archivos aquí (PDF, Word, TXT, MD, etc):", accept_multiple_files=True)
                    
                    # Dynamic button text
                    if current_unit_id:
                        btn_text = f"📤 Subir a '{current_location}'"
                    else:
                        btn_text = "📤 Subir (se creará carpeta si es necesario)"
                    
                    if st.button(btn_text, type="primary"):
                        target = current_unit_id
                        if not target:
                             # If at root, check if we need to enforce folder? 
                             # Assuming root upload is allowed if system supports it, but usually we want organization.
                             # Let's handle Root Uploads (create generic 'Uncategorized' or allow root files if DB supports)
                             # DB Handler supports root files (unit_id=None)? check upload_file_to_db logic.
                             # If parent_id in create_unit can be None, files usually need a unit. 
                             # Let's enforce Folder Selection if at root, OR create a "General" folder.
                             pass 
                        
                        # Logic from original
                        if upl_files:
                            for uf in upl_files:
                                try:
                                    content = ""
                                    if uf.type in ["text/plain", "application/json", "text/markdown"]:
                                        content = str(uf.read(), "utf-8", errors='ignore')
                                    elif uf.type == "application/pdf":
                                         if hasattr(assistant, 'extract_text_from_pdf'):
                                             content = assistant.extract_text_from_pdf(uf.getvalue())
                                         else: content = "PDF Content"
                                    elif "wordprocessingml" in uf.type:
                                         import docx
                                         doc = docx.Document(uf)
                                         content = "\n".join([p.text for p in doc.paragraphs])
                                    else:
                                        content = f"Binary: {uf.name}"
                                        
                                    # Fallback for root: create 'General' if needed or passing None if supported
                                    # DB Handler seems to require unit_id for files usually.
                                    # We'll assume allow root files if Current Unit is set.
                                    # If Current Unit is None (Root), we force user to pick a folder?
                                    if not current_unit_id:
                                         # Quick Fix: Auto-assign to first available folder or create "General"
                                         all_u = get_units(current_course_id)
                                         if all_u: 
                                             real_target = all_u[0]['id']
                                             st.toast(f"⚠️ Subiendo a '{all_u[0]['name']}' (No estabas en una carpeta)")
                                         else:
                                             res = create_unit(current_course_id, "General")
                                             real_target = res['id']
                                             st.toast("✨ Carpeta 'General' creada automáticamente")
                                    else:
                                        real_target = current_unit_id

                                    upload_file_to_db(real_target, uf.name, content, "text")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            st.success("¡Archivos Subidos!")
                            st.session_state['lib_active_tool'] = None # Close panel
                            time.sleep(1)
                            st.rerun()

                with up_t2:
                     note_title = st.text_input("Título:", placeholder="Ej: Idea.txt")
                     note_body = st.text_area("Contenido:", height=150)
                     if st.button("Guardar Nota"):
                         if note_title and note_body:
                             final_name = note_title if "." in note_title else f"{note_title}.txt"
                             real_target = current_unit_id
                             if not real_target:
                                 all_u = get_units(current_course_id)
                                 if all_u: real_target = all_u[0]['id']
                                 else: 
                                     r = create_unit(current_course_id, "Notas")
                                     real_target = r['id']
                             
                             upload_file_to_db(real_target, final_name, note_body, "text")
                             st.success("Nota guardada")
                             st.session_state['lib_active_tool'] = None
                             time.sleep(1)
                             st.rerun()

                with up_t3:
                    st.info("Importar historial de chat como archivo.")
                    # Simplified import logic (from original)
                    i_file = st.file_uploader("Historial:", key="chat_imp_Simple")
                    if i_file:
                        content = str(i_file.read(), "utf-8", errors='ignore')
                        if st.button("Procesar e Importar"):
                             # Just save as file for now to keep it simple
                             real_target = current_unit_id or (get_units(current_course_id)[0]['id'] if get_units(current_course_id) else create_unit(current_course_id, "Importados")['id'])
                             upload_file_to_db(real_target, i_file.name, content, "text")
                             st.success("Importado correctamente")
                             st.rerun()

            # --- CREATE FOLDER TOOL ---
            elif tool == 'create':
                st.markdown("#### ✨ Nueva Carpeta")
                c_f1, c_f2 = st.columns([0.7, 0.3])
                name = c_f1.text_input("Nombre de la carpeta:", label_visibility="collapsed", placeholder="Ej: Unidad 2")
                if c_f2.button("Crear", type="primary", use_container_width=True):
                    if name:
                        create_unit(current_course_id, name, parent_id=current_unit_id)
                        st.success(f"Carpeta '{name}' creada")
                        st.session_state['lib_active_tool'] = None
                        time.sleep(1)
                        st.rerun()

            # --- SEARCH TOOL ---
            elif tool == 'search':
                st.markdown("#### 🔍 Búsqueda Global")
                q = st.text_input("Buscar archivo:", placeholder="Escribe el nombre...", key="search_bar_glob")
                if q:
                    results = search_library(current_course_id, q)
                    if results:
                        st.write(f"Encontrados **{len(results)}** resultados:")
                        for r in results:
                            with st.expander(f"{r['name']} (En: {r.get('unit_name', 'Unknown')})"):
                                # Safe content handling
                                content = r.get('content') or r.get('content_text') or ""
                                preview = content[:500] if content else "(Sin contenido)"
                                st.markdown(preview + ("..." if len(content) > 500 else ""))
                                
                                # Navigate to folder button
                                if st.button("📂 Ir a la carpeta", key=f"jump_{r['id']}", type="primary"):
                                    # Get the unit_id from search result
                                    target_unit_id = r.get('unit_id')
                                    target_unit_name = r.get('unit_name', 'Carpeta')
                                    
                                    if target_unit_id:
                                        # Set current unit to the target folder
                                        st.session_state['lib_current_unit_id'] = target_unit_id
                                        st.session_state['lib_current_unit_name'] = target_unit_name
                                        
                                        # Build breadcrumb trail (simplified - just add the target unit)
                                        # For a full path, we'd need to query parent units recursively
                                        st.session_state['lib_breadcrumbs'] = [{'id': target_unit_id, 'name': target_unit_name}]
                                        
                                        # Close search tool
                                        st.session_state['lib_active_tool'] = None
                                        
                                        st.success(f"Navegando a: {target_unit_name}")
                                        time.sleep(0.5)
                                        st.rerun()
                                    else:
                                        st.warning("No se pudo determinar la ubicación del archivo")
                    else:
                        st.caption("No se encontraron resultados.")

            # --- MANAGE TOOL ---
            elif tool == 'manage':
                st.markdown("#### ⚙️ Gestión de Carpetas")
                # Show only if subfolders exist
                subs = get_units(current_course_id, parent_id=current_unit_id)
                if not subs:
                    st.info("No hay carpetas aquí para gestionar.")
                else:
                    # Tabs for different actions
                    tab_rename, tab_delete = st.tabs(["✏️ Renombrar", "🗑️ Borrar"])
                    
                    with tab_rename:
                        st.caption("Selecciona una carpeta para renombrar:")
                        folder_names = [u['name'] for u in subs]
                        selected_folder = st.selectbox("Carpeta:", folder_names, key="rename_folder_select")
                        
                        if selected_folder:
                            # Find the selected folder's ID
                            selected_unit = next((u for u in subs if u['name'] == selected_folder), None)
                            
                            new_name = st.text_input("Nuevo nombre:", value=selected_folder, key="rename_input")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Renombrar", type="primary", use_container_width=True):
                                    if new_name and new_name != selected_folder:
                                        rename_unit(selected_unit['id'], new_name)
                                        st.success(f"Carpeta renombrada: '{selected_folder}' → '{new_name}'")
                                        time.sleep(1)
                                        st.rerun()
                                    elif new_name == selected_folder:
                                        st.warning("El nombre es el mismo")
                                    else:
                                        st.error("Ingresa un nombre válido")
                    
                    with tab_delete:
                        st.caption("Selecciona carpetas para eliminar:")
                        opts = {u['name']: u['id'] for u in subs}
                        sel_dels = st.multiselect("Carpetas a borrar:", list(opts.keys()), key="delete_folders_select")
                        
                        if sel_dels:
                            st.warning(f"⚠️ Se eliminarán **{len(sel_dels)}** carpetas y todo su contenido")
                            if st.button(f"🗑️ Borrar {len(sel_dels)} carpetas", type="primary"):
                                for n in sel_dels:
                                    delete_unit(opts[n])
                                st.success("Carpetas eliminadas.")
                                time.sleep(1)
                                st.rerun()

            # --- BACKUP TOOL ---
            elif tool == 'backup':
                 st.markdown("#### 📦 Exportar Biblioteca")
                 st.caption("Descarga todo tu contenido en un ZIP.")
                 if st.button("Generar ZIP"):
                     with st.spinner("Comprimiendo..."):
                         data = get_full_course_backup(current_course_id)
                         if data:
                             buf = io.BytesIO()
                             with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                                 for item in data:
                                     path = f"{item['unit']}/{item['name']}"
                                     # Clean HTML tags from content before exporting
                                     raw_content = item['content'] or ""
                                     clean_content = clean_markdown_v3(raw_content)
                                     zf.writestr(path, clean_content)
                             buf.seek(0)
                             st.download_button("⬇️ Descargar ZIP", buf, "backup.zip", "application/zip")
                         else: st.warning("Biblioteca vacía.")

            # --- CLEANER TOOL (v113) ---
            elif tool == 'cleaner':
                st.markdown("#### 🧹 Limpieza de Duplicados")
                from db_handler import get_duplicate_candidates, delete_file_db
                
                cands = get_duplicate_candidates(current_course_id)
                if not cands:
                    st.success("✅ ¡Todo limpio! No se encontraron archivos duplicados.")
                else:
                    st.info(f"Se encontraron duplicados en {len(cands)} grupos.")
                    
                    for name, files in cands.items():
                        with st.expander(f"📄 {name} ({len(files)} copias)", expanded=True):
                            # Sort by date (newest first for display)
                            # Assuming files have 'created_at' but if not, use ID or assume DB order
                            # DB 'get_course_files' orders by created_at desc.
                            
                            cols = st.columns([0.6, 0.2, 0.2])
                            cols[0].caption("Ubicación & Fecha")
                            cols[1].caption("Acción")
                            
                            for f in files:
                                c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                                with c1:
                                    st.markdown(f"**📂 {f['unit_name']}**")
                                    # Show date if available (format it)
                                    if f.get('created_at'):
                                        dt = f['created_at'].split('T')[0]
                                        st.caption(f"Creado: {dt}")
                                    else:
                                        st.caption("Fecha desconocida")
                                
                                with c2:
                                    if st.button("🗑️ Borrar", key=f"del_{f['id']}", type="secondary"):
                                        if delete_file_db(f['id']):
                                            st.toast(f"Archivo eliminado: {name}")
                                            st.rerun()
                                            
                                with c3:
                                    # Preview button? (Simple text)
                                    pass

                            st.divider()
                            # Smart Actions
                            sc1, sc2 = st.columns(2)
                            with sc1:
                                if st.button("✨ Mantener MÁS NUEVO", key=f"k_new_{name}", help="Borra todos menos el más reciente"):
                                    # files[0] is newest because of DB order
                                    to_delete = files[1:]
                                    for d in to_delete:
                                        delete_file_db(d['id'])
                                    st.toast(f"Limpieza completada para: {name}")
                                    st.rerun()
                            with sc2:
                                if st.button("🕰️ Mantener MÁS ANTIGUO", key=f"k_old_{name}", help="Borra todos menos el más antiguo"):
                                    # files[-1] is oldest
                                    to_delete = files[:-1]
                                    for d in to_delete:
                                        delete_file_db(d['id'])
                                    st.toast(f"Limpieza completada para: {name}")
                                    st.rerun()

            # Close Button footer for Panel
            st.write("")
            if st.button("Cerrar Panel", key="close_panel"):
                st.session_state['lib_active_tool'] = None
                st.rerun()

    # ==========================================
    # 3. BREADCRUMBS & NAVIGATION
    # ==========================================
    
    # Breadcrumb Logic
    crumbs = st.session_state['lib_breadcrumbs']
    path_str = "Raíz" # Removed emoji from string to be cleaner with icon next to it
    for c in crumbs:
        path_str += f" > {c['name']}"

    # Minimalist Breadcrumbs (Compact)
    # No extra spacers to keep it thin
    bc_c1, bc_c2 = st.columns([0.85, 0.15])
    with bc_c1:
        # Minimalist path display
        breadcrumbs_html = f"<div style='color: #94a3b8; font-size: 0.85rem; margin-top: 0px;'>📍 {path_str}</div>"
        st.markdown(breadcrumbs_html, unsafe_allow_html=True)
    with bc_c2:
        if crumbs:
            if st.button("⬅️ Atrás", use_container_width=True, key="back_nav_btn"):
                st.session_state['lib_breadcrumbs'].pop()
                if st.session_state['lib_breadcrumbs']:
                    last = st.session_state['lib_breadcrumbs'][-1]
                    st.session_state['lib_current_unit_id'] = last['id']
                    st.session_state['lib_current_unit_name'] = last['name']
                else:
                    st.session_state['lib_current_unit_id'] = None
                    st.session_state['lib_current_unit_name'] = None
                st.rerun()

    # Minimal Separator instead of thick Divider
    st.markdown("<hr style='margin: 5px 0 15px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # ==========================================
    # 4. CONTENT GRID (Folders & Files)
    # ==========================================
    
    # A. Folders
    subfolders = get_units(current_course_id, parent_id=current_unit_id)
    
    # DEBUG: Show current state
    st.write(f"DEBUG - Current unit ID: {st.session_state.get('lib_current_unit_id')}")
    st.write(f"DEBUG - Query params: {dict(st.query_params)}")
    
    # Check for navigation via query params BEFORE rendering folders
    if "folder_id" in st.query_params:
        qp_folder_id = st.query_params["folder_id"]
        st.write(f"DEBUG - Navigating to folder_id: {qp_folder_id}")
        
        # Search in ALL course folders, not just current level
        all_folders = get_units(current_course_id)  # Get all folders in course
        target_folder = next((u for u in all_folders if str(u['id']) == qp_folder_id), None)
        
        if target_folder:
            st.write(f"DEBUG - Found target folder: {target_folder['name']}")
            # Always update current folder
            st.session_state['lib_current_unit_id'] = target_folder['id']
            st.session_state['lib_current_unit_name'] = target_folder['name']
            
            # Only add to breadcrumbs if not already there
            folder_already_in_breadcrumbs = any(b['id'] == target_folder['id'] for b in st.session_state['lib_breadcrumbs'])
            if not folder_already_in_breadcrumbs:
                st.session_state['lib_breadcrumbs'].append(target_folder)
            
            # Clear params and rerun
            st.query_params.clear()
            st.rerun()
        else:
            st.write(f"DEBUG - Target folder NOT FOUND for ID: {qp_folder_id}")
    
    if subfolders:
        st.markdown("##### 📁 Carpetas")
        
        # V275: Restore File Counts (User Request)
        unit_counts = get_course_file_counts(current_course_id)
        
        f_cols = st.columns(3)
        for i, unit in enumerate(subfolders):
            with f_cols[i % 3]:
                # Windows Explorer Style Folder (Transparent, No Card)
                count = unit_counts.get(unit['id'], 0)
                unit_id = unit['id']
                unit_name = unit['name']
                
                # Use st.markdown with anchor tag for clickable functionality (avoids iframe issues and key error)
                # CSS class .folder-hover-card handles the hover effects (defined at top of file)
                html_content = f"""
                <a href="?folder_id={unit_id}" target="_self" style="text-decoration: none; color: inherit; display: block;">
                    <div class="folder-hover-card" style="padding: 16px 8px; text-align: center; cursor: pointer; min-height: 180px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;">
                        <!-- Custom SVG Folder Icon -->
                        <div style="margin-bottom: 10px;">
                            <svg width="80" height="80" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19.5 21H4.5C3.67157 21 3 20.3284 3 19.5V4.5C3 3.67157 3.67157 3 4.5 3H9.5C10.3284 3 11 3.67157 11 4.5V5H19.5C20.3284 5 21 5.67157 21 6.5V19.5C21 20.3284 20.3284 21 19.5 21Z" fill="{('#4B22DD' if i % 2 == 0 else '#00C853')}"/></svg>
                        </div>
                        <div style="color: #1e293b; font-size: 14px; font-weight: 700; line-height: 1.3; font-family: 'Segoe UI', system-ui, sans-serif; max-width: 180px; word-wrap: break-word;">{unit_name}</div>
                        <div style="color: #64748b; font-size: 12px; font-weight: 500;">{count} archivos</div>
                    </div>
                </a>
                """
                st.markdown(html_content, unsafe_allow_html=True)


    if current_unit_id:
        files = get_files(current_unit_id)
        if files:
            # --- V336: BATCH MODE (NO RELOAD) ---
            
            # Toggle for Batch Mode (State Persisted)
            # Toggle for Batch Mode (State Persisted)
            col_t1, col_t2 = st.columns([0.7, 0.3], vertical_alignment="bottom")
            with col_t1:
                 st.markdown(f"##### 📄 Archivos ({len(files)})")
            with col_t2:
                # V337: Clean Toggle (Red Cue Removed)
                batch_mode = st.toggle("✅ Selección Múltiple", key="lib_batch_mode")
            
            if batch_mode:
                st.info("📦 Modo Lote: Marca las casillas y pulsa 'Eliminar' al final.")
                
                with st.form("batch_action_form"):
                    # Batch Actions Header inside Form
                    col_b1, col_b2 = st.columns([0.6, 0.4])
                    with col_b1:
                        st.caption("Selecciona los archivos a eliminar:")
                    with col_b2:
                        submit_batch = st.form_submit_button("🗑️ Eliminar Seleccionados", type="primary", use_container_width=True)
                    
                    st.divider()
                    
                    # Store selected IDs
                    selected_files_batch = []
                    
                    # File List inside Form (Simplified View)
                    for f in files:
                         r_c0, r_c1, r_c2 = st.columns([0.05, 0.05, 0.9])
                         with r_c0:
                             # Checkbox inside form
                             if st.checkbox("", key=f"batch_sel_{f['id']}", label_visibility="collapsed"):
                                 selected_files_batch.append(f['id'])
                         with r_c1:
                             st.write("📝" if f['type'] == 'text' else "📎")
                         with r_c2:
                             st.write(f"**{f['name']}**")
                    
                    # Form Logic
                    if submit_batch:
                         if selected_files_batch:
                             count = 0
                             for fid in selected_files_batch:
                                 delete_file(fid)
                                 count += 1
                             st.success(f"Eliminados {count} archivos.")
                             time.sleep(1)
                             st.rerun()
                         else:
                             st.warning("No seleccionaste nada.")

            else:
                # NORMAL MODE (Full Features, No Checkboxes causing reloads)
                # Just the standard list
                for f in files:
                    # File Row Layout: Icon | Name | Actions
                    r_c1, r_c2, r_c3 = st.columns([0.05, 0.75, 0.2], vertical_alignment="bottom")
                    
                    with r_c1:
                        icon = "📝" if f['type'] == 'text' else "📎"
                        st.write(icon)
                    
                    with r_c2:
                        st.write(f"**{f['name']}**")
                        
                        # V307: Editable Transcription Interface
                        file_content = f.get('content') or f.get('content_text') or "Sin contenido"
                        edit_key = f"edit_mode_{f['id']}"
                        
                        # Initialize edit mode state
                        if edit_key not in st.session_state:
                            st.session_state[edit_key] = False
                        
                        # Edit mode toggle
                        col_edit, col_ai = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Editar" if not st.session_state[edit_key] else "👁️ Ver", 
                                       key=f"toggle_edit_{f['id']}", use_container_width=True):
                                st.session_state[edit_key] = not st.session_state[edit_key]
                                st.rerun()
                        
                        with col_ai:
                            if st.button("🤖 Formatear", key=f"format_{f['id']}", use_container_width=True,
                                       help="Aplica formato inteligente (párrafos, títulos)"):
                                with st.spinner("Formateando con IA..."):
                                    formatted_text = format_transcript_with_ai(file_content, assistant)
                                    result = update_file_content(f['id'], formatted_text)
                                if result is True:
                                    st.success("✨ Formateado con éxito")
                                    st.session_state[edit_key] = False
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error al guardar formato: {result}")
                        
                        # Display content (editable or read-only)
                        if st.session_state[edit_key]:
                            # Edit mode: CKEditor WYSIWYG (V311 - No API Key Required)
                            st.caption("💡 Seleccioná texto y usá los botones para dar formato (como Google Docs)")
                            
                            editor_key = f"editor_content_{f['id']}"
                            if editor_key not in st.session_state:
                                st.session_state[editor_key] = file_content
                            
                            # Escape content for JavaScript
                            import json
                            import markdown
                            
                            # V325-FIX: Check if content is ALREADY html (starts with <)
                            # If so, do NOT run markdown() on it again, or it adds extra <p> wrappers.
                            if file_content.strip().startswith("<"):
                                 html_content = file_content
                            else:
                                 # Convert existing Markdown to HTML
                                 html_content = markdown.markdown(file_content)
                            
                            # Remove outer <p> tags if it's a single paragraph acting weird, 
                            # but usually markdown wraps everything in <p>. 
                            # CKEditor handles HTML input perfectly.
                            
                            safe_content = json.dumps(html_content)
                            
                            # Render Editor (Quill or Fallback)
                            
                            # V320: Robust Editor Logic
                            content_to_save = None
                            
                            # V324: ISOLATE EDITOR IN FORM TO PREVENT RELOADS
                            # Using st.form prevents Streamlit from rerunning on every keystroke in Quill
                            
                            editor_form_key = f"form_edit_{f['id']}"
                            
                            with st.form(key=editor_form_key):
                                if QUILL_AVAILABLE:
                                    # Toolbar configuration
                                    toolbar = [
                                        ["bold", "italic", "underline", "strike"],
                                        [{"header": [1, 2, 3, False]}],
                                        [{"list": "ordered"}, {"list": "bullet"}],
                                        [{"indent": "-1"}, {"indent": "+1"}],
                                        ["clean"]
                                    ]
                                    
                                    st.caption("📝 Editor Visual (Quill) - Presiona 'Guardar' al terminar")
                                    
                                    # quill_content will be captured only on form submit? 
                                    # Actually st_quill inside form updates on submit.
                                    quill_content = st_quill(
                                        value=html_content, 
                                        placeholder="Escribe aquí...", 
                                        html=True, 
                                        toolbar=toolbar,
                                        key=f"quill_{f['id']}"
                                    )
                                    content_to_save = quill_content
                                else:
                                    st.caption("📝 Editor de Texto (Modo Seguro)")
                                    clean_text = clean_markdown_v3(file_content)
                                    txt_content = st.text_area("Contenido", value=clean_text, height=500, key=f"txt_{f['id']}")
                                    content_to_save = txt_content
    
                                # Form Buttons
                                col_save, col_cancel = st.columns([1, 1])
                                with col_save:
                                    submit_save = st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True)
                                
                                with col_cancel:
                                    # Cancel button in form submits too, but we handle logic below
                                    submit_cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            
                            # LOGIC AFTER FORM SUBMISSION
                            if submit_save:
                                # 1. Validation
                                if content_to_save is None:
                                    if QUILL_AVAILABLE: content_to_save = html_content 
                                    else: content_to_save = clean_markdown_v3(file_content)
    
                                # 2. HTML CLEANING (Fix "Giant Jump" & Double Spacing)
                                # Quill adds <p> around everything. Default CSS has large margins.
                                # We need to Compact the HTML.
                                if isinstance(content_to_save, str):
                                    import re
                                    
                                    # DETECT IF WE ARE SAVING HTML OR TEXT
                                    if "<p>" in content_to_save or "<div>" in content_to_save:
                                        cleaned = content_to_save
                                        
                                        # 1. REMOVE ALL EMPTY PARAGRAPHS COMPLETELY
                                        # This kills the "double enter" visual but fixes the gap issue.
                                        # <p><br></p> -> ''
                                        cleaned = re.sub(r'<p><br></p>', '', cleaned)
                                        
                                        # 2. ALSO Remove paragraphs that only contain whitespace
                                        cleaned = re.sub(r'<p>\s*</p>', '', cleaned)
                                        
                                        # 3. Trim headers
                                        
                                        content_to_save = cleaned
    
                                result = update_file_content(f['id'], content_to_save)
                                if result is True:
                                    st.success("✅ Guardado exitosamente (Espacios Ajustados)")
                                    st.session_state[edit_key] = False
                                    # Cleanup keys
                                    if f"quill_{f['id']}" in st.session_state: del st.session_state[f"quill_{f['id']}"]
                                    if f"txt_{f['id']}" in st.session_state: del st.session_state[f"txt_{f['id']}"]
                                    
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error al guardar: {result}")
                            
                            if submit_cancel:
                                st.session_state[edit_key] = False
                                st.rerun()
                        else:
                            # View mode: Expander with formatted content
                            with st.expander("Ver contenido"):
                                # If content is HTML (starts with <p> or contains tags), treat as safe html
                                # Otherwise markdown.
                                # We can just always use unsafe_allow_html=True which handles both usually.
                                st.markdown(file_content, unsafe_allow_html=True)
                    
                    with r_c3:
                        # Quick Actions Popover
                        # v115: Polished UI - Full Width, No Dividers, Clean Look
                        with st.popover("⚡"):
                            st.markdown(f"**{f['name']}**")
                            # Add small spacer
                            st.write("")
                                 
                            if st.button("🗑️ Eliminar", key=f"del_{f['id']}", type="primary", use_container_width=True):
                                delete_file(f['id'])
                                st.rerun()
                                
                            # Spacer instead of Divider
                            st.write("")
                            
                            # --- MAGIC ARROWS (RESTORED V301) ---
                            m_c1, m_c2 = st.columns(2)
                            with m_c1:
                                if st.button("🔼 Subir", key=f"up_{f['id']}", use_container_width=True):
                                    move_file_up(current_unit_id, f['id'])
                                    st.rerun()
                            with m_c2:
                                if st.button("🔽 Bajar", key=f"down_{f['id']}", use_container_width=True):
                                    move_file_down(current_unit_id, f['id'])
                                    st.rerun()
                                
                            st.write("")
                            
                            # --- CLEAN COPY BUTTON (ROBUST V299) ---
                            raw_txt = f.get('content') or f.get('content_text') or ""
                            clean_txt = clean_markdown_v3(raw_txt)
                            
                            import json
                            safe_txt = json.dumps(clean_txt)
                            
                            components.html(f"""
                            <html>
                            <body style="margin:0; padding:0; display:flex; justify-content:center;">
                                <script>
                                function copyToClipboard() {{
                                    const text = {safe_txt};
                                    const btn = document.getElementById('copyBtn');
                                    
                                    function showSuccess() {{
                                        btn.innerHTML = '✅ Copiado';
                                        btn.style.borderColor = '#10b981';
                                        btn.style.color = '#10b981';
                                        setTimeout(() => {{
                                            btn.innerHTML = '📋 Copiar Texto';
                                            btn.style.borderColor = '#e2e8f0';
                                            btn.style.color = '#64748b';
                                        }}, 2000);
                                    }}
    
                                    // Plan A: Modern API
                                    if (navigator.clipboard && window.isSecureContext) {{
                                        navigator.clipboard.writeText(text).then(showSuccess).catch(err => fallbackCopy(text));
                                    }} else {{
                                        fallbackCopy(text);
                                    }}
    
                                    function fallbackCopy(text) {{
                                        const textArea = document.createElement("textarea");
                                        textArea.value = text;
                                        textArea.style.position = "fixed";
                                        textArea.style.left = "-9999px";
                                        textArea.style.top = "0";
                                        document.body.appendChild(textArea);
                                        textArea.focus();
                                        textArea.select();
                                        try {{
                                            const successful = document.execCommand('copy');
                                            if (successful) showSuccess();
                                        }} catch (err) {{
                                            console.error('Fallback failed', err);
                                        }}
                                        document.body.removeChild(textArea);
                                    }}
                                }}
                                </script>
                                <button id="copyBtn" onclick="copyToClipboard()" style="
                                    width: 100%;
                                    background: #f8fafc;
                                    border: none;
                                    border-radius: 8px;
                                    padding: 8px 12px;
                                    cursor: pointer;
                                    font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                                    font-size: 14px;
                                    color: #475569;
                                    font-weight: 600;
                                    transition: all 0.2s;
                                    margin-top: 4px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    gap: 8px;
                                ">
                                    📋 Copiar Texto
                                </button>
                            </body>
                            </html>
                            """, height=45)
                            
                        # Move Logic could go here (Simplified for now)
        else:
            st.info("Carpeta vacía. Usa el botón 'Subir' o 'Nueva' en la barra superior.")
    else:
        # At Root (and maybe no folders)
        if not subfolders:
             st.info("Biblioteca vacía. ¡Empieza creando una carpeta arriba!")

