
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
    get_full_course_backup 
)
import streamlit.components.v1 as components

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

def render_library(assistant):
    """
    Renders the dedicated "Digital Library" (Drive-style) tab.
    Refactored V270: Minimalist Toolbar UI
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
    .toolbar-btn {
        text-align: center; 
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
    t_c1, t_c2, t_c3, t_c4, t_c5, t_c6 = st.columns(6)
    
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
                
                # Tabs for different upload types
                up_t1, up_t2, up_t3 = st.tabs(["📂 Archivos", "✍🏻 Nota Rápida", "📥 Importar Chat"])
                
                with up_t1:
                    upl_files = st.file_uploader("Arrastra tus archivos aquí (PDF, Word, TXT, MD, etc):", accept_multiple_files=True)
                    if st.button("Subir a esta carpeta", type="primary"):
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
                                st.markdown(r.get('content')[:500] + "...")
                                # Action to jump to folder?
                                if st.button("Ir a la carpeta", key=f"jump_{r['id']}"):
                                     # Not easy to jump fully without parent ID chain logic, 
                                     # but we can try setting current unit if we had unit_id
                                     # search_library returns unit_name usually. 
                                     # Let's keep it simple.
                                     pass
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
                    st.write("Selecciona carpetas para borrar o renombrar (Ver interfaz clásica para renombrar individualmente).")
                    opts = {u['name']: u['id'] for u in subs}
                    sel_dels = st.multiselect("Seleccionar carpetas:", list(opts.keys()))
                    if sel_dels and st.button(f"🗑️ Borrar {len(sel_dels)} carpetas"):
                         for n in sel_dels:
                             delete_unit(opts[n])
                         st.success("Eliminadas.")
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
                                     zf.writestr(path, item['content'] or "")
                             buf.seek(0)
                             st.download_button("⬇️ Descargar ZIP", buf, "backup.zip", "application/zip")
                         else: st.warning("Biblioteca vacía.")

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
    if subfolders:
        st.markdown("##### 📁 Carpetas")
        
        # V275: Restore File Counts (User Request)
        unit_counts = get_course_file_counts(current_course_id)
        
        f_cols = st.columns(3)
        for i, unit in enumerate(subfolders):
            with f_cols[i % 3]:
                # Folder Card
                count = unit_counts.get(unit['id'], 0)
                label = f"📁 {unit['name']} ({count})"
                
                if st.button(label, key=f"fdir_{unit['id']}", use_container_width=True):
                    st.session_state['lib_current_unit_id'] = unit['id']
                    st.session_state['lib_current_unit_name'] = unit['name']
                    st.session_state['lib_breadcrumbs'].append(unit)
                    st.rerun()

    # B. Files
    if current_unit_id:
        files = get_files(current_unit_id)
        if files:
            st.markdown(f"##### 📄 Archivos ({len(files)})")
            
            for f in files:
                # File Row Layout: Icon | Name | Actions
                r_c1, r_c2, r_c3 = st.columns([0.05, 0.75, 0.2], vertical_alignment="bottom")
                
                with r_c1:
                    icon = "📝" if f['type'] == 'text' else "📎"
                    st.write(icon)
                
                with r_c2:
                    st.write(f"**{f['name']}**")
                    with st.expander("Ver contenido"):
                        st.markdown(f.get('content') or f.get('content_text') or "Sin contenido")
                
                with r_c3:
                    # Quick Actions Popover
                    with st.popover("⚡"):
                        st.markdown(f"**{f['name']}**")
                        if st.button("🤖 Analizar con IA", key=f"ai_{f['id']}"):
                             st.session_state['chat_context_file'] = f
                             st.session_state['redirect_target_name'] = "Ayudante de Tareas"
                             st.session_state['force_chat_tab'] = True
                             st.rerun()
                             
                        if st.button("🗑️ Eliminar", key=f"del_{f['id']}"):
                            delete_file(f['id'])
                            st.rerun()
                            
                        st.divider()
                        
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
                                background: white;
                                border: 1px solid #e2e8f0;
                                border-radius: 8px;
                                padding: 8px 16px;
                                color: #64748b;
                                font-size: 14px;
                                font-family: sans-serif;
                                cursor: pointer;
                                transition: all 0.2s;
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
            if not subfolders:
                st.info("Carpeta vacía. Usa el botón 'Subir' o 'Nueva' en la barra superior.")
    else:
        # At Root (and maybe no folders)
        if not subfolders:
             st.info("Biblioteca vacía. ¡Empieza creando una carpeta arriba!")

