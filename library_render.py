
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
    
    # --- CSS for Windows-Style Explorer (Transparent Buttons, Big Icons) ---
    st.markdown("""
    <style>
    /* --- FOLDER ICON STYLE (UNIVERSAL - V5 - SCOPED) --- */
    
    /* 
       Targeting: 
       1. Blocks that have a 3rd column...
       2. BUT DO NOT have a 4th column (Crucial to avoid hitting the 6-col toolbar)
    */
    
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) div.stButton > button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) div.stButton > button[kind="secondary"] 
    {
        background-color: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        color: #202124 !important;
        
        display: block !important;
        text-align: center !important;
        
        padding: 0px !important;
        width: 100%;
        height: auto !important;
        min-height: 140px !important;
        
        box-shadow: none !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        overflow: visible !important;
        white-space: pre-wrap !important;
    }
    
    /* CONTENT INJECTION (The Folder Icon) */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) button[kind="secondary"]::before,
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) button[kind="secondary"]::before,
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) div.stButton > button[kind="secondary"]::before,
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) div.stButton > button[kind="secondary"]::before
    {
        content: "📁" !important;
        font-size: 100px !important;
        display: block !important;
        line-height: 1.2 !important;
        margin-bottom: 0px !important;
    }
    
    /* HOVER EFFECT */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) button[kind="secondary"]:hover,
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) button[kind="secondary"]:hover {
        background-color: #e6f3ff !important;
        border: 1px solid rgba(0, 120, 215, 0.2) !important;
        transform: translateY(-2px);
        color: #202124 !important;
    }
    
    /* COLOR FILTERS (ODD is Greenish) */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) div[data-testid="column"]:nth-of-type(odd) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) div[data-testid="stColumn"]:nth-of-type(odd) button[kind="secondary"] {
        filter: hue-rotate(80deg) !important; 
    }
    
    /* COLOR FILTERS (EVEN is Purple) */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)):not(:has(> div[data-testid="column"]:nth-child(4))) div[data-testid="column"]:nth-of-type(even) button[kind="secondary"],
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"]:nth-child(3)):not(:has(> div[data-testid="stColumn"]:nth-child(4))) div[data-testid="stColumn"]:nth-of-type(even) button[kind="secondary"] {
        filter: hue-rotate(240deg) !important; 
    }
    </style>
    """, unsafe_allow_html=True)

    current_course_id = st.session_state.get('current_course_id')
    
    if not current_course_id:
        st.info("👈 Selecciona un Diplomado en la barra lateral para ver su Biblioteca.")
        return

    # --- LIBRARY LOGIC START ---


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
    
    # V328: BATCH ANALYSIS TRIGGER
    if st.session_state.get('trigger_batch_analysis'):
        st.session_state['trigger_batch_analysis'] = False
        
        selected_ids = list(st.session_state.get('selected_files_for_chat', set()))
        if selected_ids:
            with st.spinner(f"Analizando {len(selected_ids)} archivos..."):
                from db_handler import create_chat_session, save_chat_message, get_file_content
                
                # Get user
                user = st.session_state.get('user')
                if user:
                    try:
                        # Fetch all selected files
                        file_contents = []
                        file_names = []
                        
                        for file_id in selected_ids:
                            content = get_file_content(file_id)
                            if content:
                                # Get file name from files list
                                current_unit_id = st.session_state.get('lib_current_unit_id')
                                if current_unit_id:
                                    files = get_files(current_unit_id)
                                    file_obj = next((f for f in files if f['id'] == file_id), None)
                                    if file_obj:
                                        file_names.append(file_obj['name'])
                                        file_contents.append(f"--- ARCHIVO: {file_obj['name']} ---\n{content}")
                        
                        if file_contents:
                            # Create combined prompt
                            combined_content = "\n\n".join(file_contents)
                            
                            # Create session title
                            if len(file_names) == 1:
                                session_title = f"📄 {file_names[0]}"
                            elif len(file_names) <= 3:
                                session_title = f"📚 {', '.join(file_names)}"
                            else:
                                session_title = f"📚 {', '.join(file_names[:2])} (+{len(file_names)-2} más)"
                            
                            # Create chat session
                            session_id = create_chat_session(user.id, session_title)
                            
                            if session_id:
                                # Save user message
                                user_message = f"Por favor, analiza estos {len(file_names)} archivos relacionados y proporciona:\n1. Un resumen individual de cada archivo\n2. Las conexiones y relaciones entre los contenidos\n3. Un análisis integrado del tema completo\n\n{combined_content}"
                                save_chat_message(session_id, "user", user_message)
                                
                                # Generate AI response
                                try:
                                    prompt = f"Eres un tutor académico experto. Analiza los siguientes {len(file_names)} archivos relacionados y proporciona:\n1. Un resumen claro de cada archivo\n2. Las conexiones y relaciones entre los contenidos\n3. Un análisis integrado y conclusiones\n\n{combined_content}"
                                    ai_response = assistant.model.generate_content(prompt)
                                    ai_text = ai_response.text
                                    save_chat_message(session_id, "assistant", ai_text)
                                    
                                    st.success(f"✅ Chat creado exitosamente: **{session_title}**")
                                    st.info("💬 Ve al **Historial de Chats** para ver el análisis completo")
                                    
                                    # Clear selection
                                    st.session_state['selected_files_for_chat'] = set()
                                except Exception as e:
                                    st.error(f"❌ Error al generar análisis: {str(e)}")
                                    st.info("💬 El chat fue creado. Ve al **Historial de Chats** para continuar")
                            else:
                                st.error("❌ Error al crear sesión de chat")
                        else:
                            st.warning("⚠️ No se pudo cargar el contenido de los archivos seleccionados")
                    except Exception as e:
                        st.error(f"❌ Error crítico: {str(e)}")
                else:
                    st.error("❌ Error: Usuario no autenticado")


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
    st.caption("--- Menú de Biblioteca ---")
    t_c1, t_c2, t_c3, t_c4, t_c5, t_c6, t_c7 = st.columns(7)
    
    # Define button styles based on active state
    def get_type(tool_name):
        return "primary" if st.session_state['lib_active_tool'] == tool_name else "secondary"

    with t_c1:
        if st.button("Raiz", use_container_width=True, help="Ir a la carpeta principal"):
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
         if st.button("🧹 Duplicados", type=get_type('duplicates'), use_container_width=True, help="Buscar archivos duplicados"):
            set_tool('duplicates')
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

            # --- DUPLICATES TOOL ---
            elif tool == 'duplicates':
                st.markdown("#### 🧹 Detección de Duplicados")
                st.caption("Encuentra y gestiona archivos con el mismo nombre en diferentes carpetas.")
                
                if st.button("🔍 Escanear toda la biblioteca", type="primary", help="Busca en TODAS las carpetas del diplomado actual"):
                     from db_handler import get_duplicate_files
                     
                     st.toast("🔵 Iniciando escaneo...", icon="🔄")
                     
                     if not current_course_id:
                         st.error("❌ No se pudo obtener el ID del curso. Por favor recarga la página.")
                     else:
                         try:
                             # Clear previous state
                             if 'dupes_results' in st.session_state: 
                                 del st.session_state['dupes_results']
                             if 'batch_delete_ready' in st.session_state:
                                 del st.session_state['batch_delete_ready']
                             
                             with st.spinner("Analizando..."):
                                 dupes = get_duplicate_files(current_course_id)
                                 st.session_state['dupes_results'] = dupes
                                 st.toast(f"✅ Escaneo completado. Encontrados: {len(dupes)}", icon="✅")
                                 # Don't rerun here - let Streamlit naturally refresh
                         except Exception as e:
                             st.error(f"Error al escanear duplicados: {e}")
                
                # Render Results from Session State (to persist after delete actions re-run)
                if 'dupes_results' in st.session_state:
                     from db_handler import get_file_content # Delayed import
                     dupes = st.session_state['dupes_results']
                     if dupes:
                         st.warning(f"⚠️ Se encontraron {len(dupes)} grupos de archivos duplicados:")
                         
                         for d in dupes:
                             with st.container(border=True):
                                 st.write(f"**📄 {d['name']}**")
                                 st.caption(f"Archivos idénticos detectados: {d['count']}")
                                 
                                 for entry in d['entries']:
                                     # Format date nicely
                                     created_date = entry.get('created_at', '')
                                     date_str = ""
                                     if created_date:
                                         if len(created_date) > 16:
                                             date_str = f" <span style='color:grey; font-size:0.8em'>({created_date[:10]} {created_date[11:16]})</span>"
                                         else:
                                             date_str = f" <span style='color:grey; font-size:0.8em'>({created_date})</span>"
                                     
                                     # Row Layout: Folder + Delete Button aligned
                                     d_c1, d_c2 = st.columns([0.85, 0.15], vertical_alignment="center")
                                     with d_c1:
                                         st.markdown(f"📂 **{entry['unit']}**{date_str}", unsafe_allow_html=True)
                                     with d_c2:
                                         if st.button("🗑️", key=f"del_dupe_{entry['id']}", help="Eliminar esta copia", use_container_width=True):
                                             delete_file(entry['id'])
                                             st.success("Eliminado")
                                             time.sleep(0.5)
                                             d['entries'].remove(entry)
                                             d['count'] -= 1
                                             if d['count'] <= 1: dupes.remove(d) 
                                             st.rerun()

                                     # File Content Preview (Full Width below)
                                     with st.expander("👁️ Ver contenido"):
                                         with st.container(height=200):
                                             c_prev = get_file_content(entry['id'])
                                             if c_prev is not None:
                                                 if len(str(c_prev).strip()) == 0:
                                                      st.warning("⚠️ El archivo está vacío (0 bytes de texto).")
                                                 else:
                                                      st.markdown(str(c_prev).lstrip()[:5000], unsafe_allow_html=True) 
                                             else:
                                                 st.info("ℹ️ Vista previa no disponible para este tipo de archivo.")
                         
                         # --- BATCH ACTIONS ---
                         st.divider()
                         st. subheader("⚡ Acciones Masivas")
                         
                         if st.button("🧹 Preparar Limpieza Automática", help="Selecciona automáticamente los duplicados para borrar, manteniendo solo la versión más reciente."):
                             st.session_state['batch_delete_ready'] = True
                         
                         if st.session_state.get('batch_delete_ready'):
                             to_delete = []
                             for d in dupes:
                                 # Sort by created_at DESCENDING (newest first)
                                 # We keep the one with the 'largest' date (newest)
                                 sorted_entries = sorted(d['entries'], key=lambda x: x.get('created_at', '0000'), reverse=True)
                                 if len(sorted_entries) > 1:
                                     # Keep index 0 (newest), delete 1..N (older ones)
                                     to_delete.extend(sorted_entries[1:])
                             
                             if to_delete:
                                 st.error(f"⚠️ **¿Estás seguro?** Se eliminarán **{len(to_delete)}** archivos duplicados.")
                                 st.markdown("Se conservará únicamente la versión **más reciente** de cada grupo.")
                                 
                                 col_confirm, col_cancel = st.columns(2)
                                 with col_confirm:
                                     if st.button("🚨 SÍ, ELIMINAR TODOS", type="primary"):
                                         try:
                                             progress_bar = st.progress(0)
                                             status_text = st.empty()
                                             deleted_count = 0
                                             
                                             for i, f in enumerate(to_delete):
                                                 status_text.text(f"Eliminando {i+1}/{len(to_delete)}: {f.get('unit', 'archivo')}...")
                                                 try:
                                                     delete_file(f['id'])
                                                     deleted_count += 1
                                                 except Exception as e:
                                                     st.error(f"Error eliminando archivo: {e}")
                                                 progress_bar.progress((i + 1) / len(to_delete))
                                             
                                             status_text.empty()
                                             st.success(f"¡Limpieza completada! {deleted_count} archivos eliminados.")
                                             time.sleep(1)
                                             
                                             # Reset state and re-scan
                                             if 'batch_delete_ready' in st.session_state:
                                                 del st.session_state['batch_delete_ready']
                                             if 'dupes_results' in st.session_state:
                                                 del st.session_state['dupes_results']
                                             st.rerun()
                                         except Exception as e:
                                             st.error(f"Error en limpieza masiva: {e}")
                                             if 'batch_delete_ready' in st.session_state:
                                                 del st.session_state['batch_delete_ready']
                                 with col_cancel:
                                     if st.button("Cancelar"):
                                         del st.session_state['batch_delete_ready']
                                         st.rerun()
                             else:
                                 st.info("No hay candidatos seguros para borrar (quizás las fechas son idénticas o ya están limpios).")
                         st.success("✅ ¡Excelente! No se encontraron duplicados en ninguna carpeta del curso.")

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
                # Folder Card (Massive Icon Style via CSS Injection)
                count = unit_counts.get(unit['id'], 0)
                # SEPARATION: Handled by CSS ::before margin-bottom now.
                # Label is just the name and count.
                # Cleaner, safer, guaranteed size.
                # V326: Truncate long names for aesthetics
                folder_name = unit['name']
                max_length = 35
                if len(folder_name) > max_length:
                    display_name = folder_name[:max_length] + "..."
                else:
                    display_name = folder_name
                
                label = f"**{display_name}** ({count})"
                
                # Use type='secondary' to hook into our new scoped CSS (Avoids Primary conflict)
                if st.button(label, key=f"fdir_{unit['id']}", use_container_width=True, type="secondary"):
                    st.session_state['lib_current_unit_id'] = unit['id']
                    st.session_state['lib_current_unit_name'] = unit['name']
                    st.session_state['lib_breadcrumbs'].append(unit)
                    st.rerun()

    # B. Files
    if current_unit_id:
        files = get_files(current_unit_id)
        if files:
            # V328: Multi-File Selection State
            if 'selected_files_for_chat' not in st.session_state:
                st.session_state['selected_files_for_chat'] = set()
            
            # Header with file count and batch actions
            col_header, col_actions = st.columns([0.7, 0.3])
            with col_header:
                st.markdown(f"##### 📄 Archivos ({len(files)})")
            
            with col_actions:
                selected_count = len(st.session_state['selected_files_for_chat'])
                if selected_count > 0:
                    if st.button(f"🤖 Analizar {selected_count} archivo{'s' if selected_count > 1 else ''}", 
                                key="batch_analyze", use_container_width=True, type="primary"):
                        # Batch analysis logic (implemented below)
                        st.session_state['trigger_batch_analysis'] = True
                        st.rerun()
            
            
            
            for f in files:
                # V328: File Row Layout: Checkbox | Icon | Name | Actions | Spacer
                r_check, r_c1, r_c2, r_c3, r_spacer = st.columns([0.05, 0.05, 0.70, 0.15, 0.05], vertical_alignment="bottom")
                
                with r_check:
                    # Checkbox for multi-file selection
                    is_selected = f['id'] in st.session_state['selected_files_for_chat']
                    if st.checkbox("", value=is_selected, key=f"select_{f['id']}", label_visibility="collapsed"):
                        st.session_state['selected_files_for_chat'].add(f['id'])
                    else:
                        st.session_state['selected_files_for_chat'].discard(f['id'])
                
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
                    with st.popover("⚡"):
                        st.markdown(f"**{f['name']}**")
                        if st.button("🤖 Analizar con IA", key=f"ai_{f['id']}"):
                             # V327: Direct Chat Creation with Auto-Summary
                             try:
                                 from db_handler import create_chat_session, save_chat_message
                                 
                                 # Get file content
                                 file_content = f.get('content') or f.get('content_text') or "Sin contenido"
                                 file_name = f['name']
                                 
                                 # Get user ID from authenticated session
                                 user = st.session_state.get('user')
                                 if not user:
                                     st.error("❌ Error: Usuario no autenticado")
                                 else:
                                     with st.spinner("Creando chat con el tutor..."):
                                         user_id = user.id
                                         session_title = f"📄 {file_name}"
                                         
                                         # Create chat session
                                         session_id = create_chat_session(user_id, session_title)
                                         
                                         if session_id:
                                             # Save user's request for summary
                                             user_message = f"Por favor, dame un resumen detallado de este archivo:\n\n{file_content}"
                                             save_chat_message(session_id, "user", user_message)
                                             
                                             # Generate AI response
                                             try:
                                                 prompt = f"Eres un tutor académico experto. Analiza el siguiente contenido y proporciona un resumen claro y estructurado:\n\n{file_content}"
                                                 ai_response = assistant.model.generate_content(prompt)
                                                 ai_text = ai_response.text
                                                 save_chat_message(session_id, "assistant", ai_text)
                                                 
                                                 st.success(f"✅ Chat creado exitosamente: **{session_title}**")
                                                 st.info("💬 Ve al **Historial de Chats** para ver el resumen completo")
                                             except Exception as e:
                                                 st.error(f"❌ Error al generar resumen: {str(e)}")
                                                 st.info("💬 El chat fue creado. Ve al **Historial de Chats** para continuar")
                                         else:
                                             st.error("❌ Error al crear sesión de chat")
                             except Exception as e:
                                 st.error(f"❌ Error crítico: {str(e)}")
                                 import traceback
                                 st.code(traceback.format_exc())
                             
                             
                        if st.button("🗑️ Eliminar", key=f"del_{f['id']}"):
                            delete_file(f['id'])
                            st.rerun()
                            
                        st.divider()
                        
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

