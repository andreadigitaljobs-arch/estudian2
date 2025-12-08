
import streamlit as st
import os
import glob
from transcriber import Transcriber
from study_assistant import StudyAssistant
from PIL import Image, ImageGrab
import shutil
import time
import datetime
import extra_streamlit_components as stx  # --- PERSISTENCE ---
from library_ui import render_library # --- LIBRARY UI ---
from library_ui import render_library # --- LIBRARY UI ---
from database import delete_course, rename_course # Force import availability

# --- PAGE CONFIG MUST BE FIRST ---
st.set_page_config(page_title="Estudian2", page_icon="app_icon.png", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []
if 'notes_result' not in st.session_state: st.session_state['notes_result'] = ""
if 'guide_result' not in st.session_state: st.session_state['guide_result'] = ""
if 'quiz_results' not in st.session_state: st.session_state['quiz_results'] = []
if 'pasted_images' not in st.session_state: st.session_state['pasted_images'] = []
if 'quiz_key' not in st.session_state: st.session_state['quiz_key'] = 0
if 'tutor_chat_history' not in st.session_state: st.session_state['tutor_chat_history'] = []
if 'current_course' not in st.session_state: st.session_state['current_course'] = None
if 'homework_result' not in st.session_state: st.session_state['homework_result'] = ""
if 'spotlight_query' not in st.session_state: st.session_state['spotlight_query'] = ""
if 'spotlight_mode' not in st.session_state: st.session_state['spotlight_mode'] = "âš¡ Concepto RÃ¡pido"
if 'custom_api_key' not in st.session_state: st.session_state['custom_api_key'] = None

# --- AUTHENTICATION CHECK ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- COOKIE MANAGER (PERSISTENCE) ---
cookie_manager = stx.CookieManager()

# --- AUTO-LOGIN CHECK ---
if not st.session_state['user']:
    # Try to get token from cookie
    # We use REFERSH TOKEN for long-term persistence (simpler than session reconstruction)
    try:
        time.sleep(0.1)
        refresh_token = cookie_manager.get("supabase_refresh_token")
        if refresh_token:
             from database import init_supabase
             client = init_supabase()
             res = client.auth.refresh_session(refresh_token)
             if res.session:
                 st.session_state['user'] = res.user
                 st.session_state['supabase_session'] = res.session
                 st.rerun()
                 
    except Exception as e:
        print(f"Auto-login failed: {e}")


# If not logged in, show Login Screen and STOP
if not st.session_state['user']:
    st.markdown("## ðŸ” Iniciar SesiÃ³n en Estudian2")
    st.caption("Modo Nube Multi-Usuario (Supabase)")
    
    # Simple formatting for Login
    tab_login, tab_signup = st.tabs(["Ingresar", "Registrarse"])
    
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("ContraseÃ±a", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            from database import sign_in
            user = sign_in(email, password)
            if user:
                st.session_state['user'] = user
                # SET COOKIE
                if 'supabase_session' in st.session_state:
                    sess = st.session_state['supabase_session']
                    # Expire in 30 days
                    cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.success(f"Â¡Bienvenido!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciales incorrectas o error de conexiÃ³n.")

    with tab_signup:
        new_email = st.text_input("Email", key="reg_email")
        new_pass = st.text_input("ContraseÃ±a", type="password", key="reg_pass")
        if st.button("Crear Cuenta", key="btn_reg"):
            from database import sign_up
            user = sign_up(new_email, new_pass)
            if user:
                if 'supabase_session' in st.session_state:
                     sess = st.session_state['supabase_session']
                     cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.success("Cuenta creada. Por favor inicia sesiÃ³n.")
            else:
                st.error("Error al crear cuenta.")
    
    st.stop() # Stop execution here if not logged in

# --- CONFIGURATION & MIGRATION ---
CORE_OUTPUT_ROOT = "output"

def run_migration_check():
    """Moves legacy 'output' folders into a default course folder."""
    default_course = "Diplomado_Marketing_Inicial"
    search_paths = ["transcripts", "notes", "guides", "library"]
    
    # Check if any legacy folder exists directly in root 'output'
    needs_migration = False
    for p in search_paths:
        if os.path.exists(os.path.join(CORE_OUTPUT_ROOT, p)):
            needs_migration = True
            break
            
    if needs_migration:
        target_root = os.path.join(CORE_OUTPUT_ROOT, default_course)
        os.makedirs(target_root, exist_ok=True)
        
        for p in search_paths:
            src = os.path.join(CORE_OUTPUT_ROOT, p)
            dst = os.path.join(target_root, p)
            if os.path.exists(src):
                # Move content 
                try:
                    shutil.move(src, dst)
                except Exception as e:
                    print(f"Migration error for {p}: {e}")
                    
run_migration_check() # Run once on startup

# Helper for dynamic paths
def get_out_dir(sub_folder=""):
    course = st.session_state.get('current_course', 'Diplomado_Marketing_Inicial')
    # Sanitize
    safe_course = "".join([c for c in course if c.isalnum() or c in (' ', '-', '_')]).strip()
    if not safe_course: safe_course = "General"
    
    path = os.path.join(CORE_OUTPUT_ROOT, safe_course, sub_folder)
    os.makedirs(path, exist_ok=True)
    return path

# --- HELPER FUNCTIONS (MOVED TO TOP FOR SCOPE) ---
def clean_markdown(text):
    """Removes basic markdown syntax for clean copying."""
    import re
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE) # Headers
    text = re.sub(r'\*\*|__', '', text) # Bold
    text = re.sub(r'\*|_', '', text) # Italics
    text = re.sub(r'^[\*\-]\s+', '', text, flags=re.MULTILINE) # Bullets
    return text.strip()

def copy_to_clipboard(text):
    """Copies text to Windows clipboard using clip command."""
    import subprocess
    try:
        # Use UTF-16LE for Windows clipboard to handle special chars/emojis correctly
        subprocess.run(['clip'], input=text.encode('utf-16le'), check=True)
        return True
    except Exception as e:
        print(f"Clipboard error: {e}")
        return False

def get_global_context():
    """
    Fetches all text content from the current course's files in DB.
    Returns: (full_text_context, file_count)
    """
    from database import get_course_full_context
    c_id = st.session_state.get('current_course_id')
    if not c_id: return "", 0
    
    full_text = get_course_full_context(c_id)
    # Count how many files are in there (approx based on our separator)
    file_count = full_text.count("--- ARCHIVO:")
    return full_text, file_count

# --- API KEY MANAGEMENT ---
def load_api_key():
    # 1. User Custom Key (Session) - Highest Priority
    if 'custom_api_key' in st.session_state and st.session_state['custom_api_key']:
        return st.session_state['custom_api_key']

    # 2. Try Streamlit Secrets (Best for Cloud)
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except:
        pass

    # 3. Try Local File (Best for Local)
    if os.path.exists("api_key.txt"):
        with open("api_key.txt", "r") as f:
            return f.read().strip()
    return ""

def save_api_key(key):
    with open("api_key.txt", "w") as f:
        f.write(key)

# --- INITIALIZATION & API CHECK ---
saved_key = load_api_key()

if not saved_key and 'api_key_input' not in st.session_state:
     # We can't init assistants yet if no key.
     # But Spotlight code runs immediately.
     # We handle this by checking if 'assistant' exists in Spotlight block.
     pass

# To avoid complexity, we'll initialize with empty key if needed, or handle it gracefully.
# Better: Load key, if exists init.
api_key = saved_key
transcriber = None
assistant = None

if api_key:
    try:
        transcriber = Transcriber(api_key)
        assistant = StudyAssistant(api_key)
    except: pass

# --- SPOTLIGHT RESULT DISPLAY ---
if 'spotlight_query' in st.session_state and st.session_state['spotlight_query']:
    query = st.session_state['spotlight_query']
    mode = st.session_state.get('spotlight_mode', "âš¡ Concepto RÃ¡pido")
    
    # Visual Container
    st.markdown(f"#### ðŸ” Resultados de Spotlight: *{query}*")
    
    with st.spinner(f"Investigando en tu bibliografÃ­a ({mode})..."):
        if not assistant:
             st.error("âš ï¸ Configura tu API Key en la barra lateral primero.")
        else:
            # 1. Get Context (Efficiency: Only load if we search)
            gl_ctx, gl_count = get_global_context()
            
            if gl_count == 0:
                st.warning("âš ï¸ Tu cerebro digital estÃ¡ vacÃ­o. Sube videos o archivos a la Biblioteca primero.")
            else:
                # 2. Search
                try:
                    # Check if we already have this result cached to avoid re-run on every interaction? 
                    # For simplicity, we run fresh or user can rely on session state if we move it there.
                    # Let's simple-cache to session state to prevent refresh loops.
                    search_key = f"search_{query}_{mode}"
                    if search_key not in st.session_state:
                        search_res = assistant.search_knowledge_base(query, gl_ctx, mode=mode)
                        st.session_state[search_key] = search_res
                    
                    final_res = st.session_state[search_key]
                    
                    # Display
                    if "RÃ¡pido" in mode:
                        st.info(final_res, icon="âš¡")
                    else:
                        st.success(final_res, icon="ðŸ•µï¸")
                        
                except Exception as e:
                    st.error(f"Error en Spotlight: {e}")
            
    if st.button("Cerrar BÃºsqueda", key="close_spot"):
        st.session_state['spotlight_query'] = ""
        st.rerun()

    st.divider()

# --- Custom CSS for "Estudian2" Elegant Theme ---
# --- GLOBAL CSS ---
CSS_STYLE = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* HIDE STREAMLIT STATUS WIDGET */
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    div[data-testid="stDecoration"] { visibility: hidden; }

    /* --- GLOBAL VARIABLES & BODY --- */
    :root {
        --primary-purple: #4B22DD;
        --accent-green: #6CC04A;
        --bg-color: #F5F6FA;
        --text-color: #1A1A1A;
        --border-color: #E3E4EA;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--bg-color);
    }

    /* APP BACKGROUND */
    .stApp {
        background-color: var(--bg-color);
        /* Clean background, no dots */
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border-color);
    }
    
    /* HEADERS */
    h1, h2, h3, h4 {
        color: var(--primary-purple);
        font-weight: 700;
        font-family: 'Inter', sans-serif;
    }

    /* BUTTONS - PRIMARY (Purple) */
    div.stButton > button {
        background-color: var(--primary-purple);
        color: white;
        border-radius: 8px; /* Professional Rounded Rect */
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s;
        box-shadow: 0 4px 6px -1px rgba(75, 34, 221, 0.2);
    }
    div.stButton > button:hover {
        background-color: #3a1ab9; /* Darker Purple */
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 10px 15px -3px rgba(75, 34, 221, 0.3);
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #FFFFFF;
        padding: 10px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        color: #64748b;
        font-weight: 500;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-purple) !important;
        color: white !important;
    }

    /* INPUTS & CARDS */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid var(--border-color);
        background-color: #FFFFFF;
    }
    
    /* CUSTOM IMAGE CARD */
    .img-card {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* SIDEBAR BUTTONS OVERRIDE */
    [data-testid="stSidebar"] .stButton > button {
        background: #FFFFFF !important;
        border: 1px solid var(--border-color) !important;
        color: #475569 !important;
        width: 100%;
        text-align: left;
        justify-content: flex-start;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: var(--primary-purple) !important;
        color: var(--primary-purple) !important;
        background-color: #f5f3ff !important;
    }
</style>
"""

st.markdown(CSS_STYLE, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # --- USER PROFILE ---
    if st.session_state.get('user'):
        st.markdown(f"ðŸ‘¤ **{st.session_state['user'].email}**")
        if st.button("Cerrar SesiÃ³n", key="logout_btn", use_container_width=True):
            st.session_state['user'] = None
            if 'supabase_session' in st.session_state:
                del st.session_state['supabase_session']
            # DELETE COOKIE
            try:
                cookie_manager.delete("supabase_refresh_token")
            except: pass
            st.rerun()
        st.divider()

    # --- VISUAL IDENTITY (Sidebar) ---
    if os.path.exists("assets/logo_main.png"):
        st.image("assets/logo_main.png", use_container_width=True)
    else:
        st.markdown("## ðŸŽ“ e-education")
    
    st.divider()

    # --- SPOTLIGHT SEARCH (Universal) ---
    st.markdown("### ðŸ” Spotlight AcadÃ©mico")
    search_query = st.text_input("Â¿QuÃ© buscas hoy?", placeholder="Ej: 'Concepto de Lead' o 'RelaciÃ³n entre X y Y'")
    search_mode = st.radio("Modo:", ["âš¡ Concepto RÃ¡pido", "ðŸ•µï¸ AnÃ¡lisis Profundo"], horizontal=True, label_visibility="collapsed")
    
    if st.button("Buscar ðŸ”", key="btn_spotlight"):
        if search_query:
            st.session_state['spotlight_query'] = search_query
            st.session_state['spotlight_mode'] = search_mode
            st.rerun()
        else:
            st.warning("Escribe algo para buscar.")
    
    st.divider()

    st.header("âš™ï¸ ConfiguraciÃ³n Personal")
    
    # Check if system key exists (for info only, do not show it)
    has_system_key = False
    try:
        if "GOOGLE_API_KEY" in st.secrets: has_system_key = True
    except: pass
    
    if has_system_key:
        st.info("âœ… Clave del Sistema Activa")
    else:
        st.warning("âš ï¸ Sin Clave del Sistema")
        
    user_key_input = st.text_input("Tu Clave API (Opcional)", type="password", help="Sobrescribe la clave del sistema para esta sesiÃ³n.")
    
    if user_key_input:
        st.session_state['custom_api_key'] = user_key_input
        st.success("âœ… Usando tu Clave Personal")
    else:
        # If user clears input, revert to system
        if 'custom_api_key' in st.session_state:
            del st.session_state['custom_api_key']
        
    st.divider()
    
    # --- COURSE SELECTOR (WORKSPACES) ---
    # --- COURSE SELECTOR (WORKSPACES) ---
    st.header("ðŸ“‚ Espacio de Trabajo")
    
    # 1. Fetch Courses from DB
    from database import get_user_courses, create_course
    
    current_user_id = st.session_state['user'].id
    db_courses = get_user_courses(current_user_id) # Returns list of dicts
    
    # Map to names for Selectbox
    course_names = [c['name'] for c in db_courses]
    course_map = {c['name']: c['id'] for c in db_courses}
    
    # Setup default if nothing exists
    if not course_names:
        course_names = [] # Empty list initially
    
    # Ensure current selection is valid
    if 'current_course' not in st.session_state or st.session_state['current_course'] not in course_names:
        if course_names:
            st.session_state['current_course'] = course_names[0]
        else:
            st.session_state['current_course'] = None
            
    # Selectbox logic
    options = course_names + ["âž• Crear Nuevo..."]
    index = course_names.index(st.session_state['current_course']) if st.session_state['current_course'] in course_names else 0
    
    selected_option = st.selectbox("Diplomado Actual:", options, index=index)
    
    if selected_option == "âž• Crear Nuevo...":
        new_course_name = st.text_input("Nombre del Nuevo Diplomado:", placeholder="Ej: Curso IA Contenido")
        if st.button("Crear Espacio"):
            if new_course_name:
                # Create in DB
                new_c = create_course(current_user_id, new_course_name)
                if new_c:
                    st.session_state['current_course'] = new_c['name']
                    st.success(f"Creado: {new_c['name']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error al crear curso.")
    else:
        # Standard Selection
        st.session_state['current_course'] = selected_option
        st.session_state['current_course_id'] = course_map[selected_option] # Store ID for DB Ops
        st.caption(f"ID: {st.session_state['current_course_id']}")

    # RENAME OPTION
    if st.session_state['current_course'] != "âž• Crear Nuevo...":
        with st.expander("âœï¸ Renombrar Diplomado"):
            rename_input = st.text_input("Nuevo nombre:", value=st.session_state['current_course'], key="rename_input")
            if st.button("Confirmar Cambio"):
                    if rename_input and rename_input != st.session_state['current_course']:
                        safe_rename = "".join([c for c in rename_input if c.isalnum() or c in (' ', '-', '_')]).strip()
                        src = os.path.join(CORE_OUTPUT_ROOT, st.session_state['current_course'])
                        dst = os.path.join(CORE_OUTPUT_ROOT, safe_rename)
                        
                        # 1. DB Update (Primary)
                        c_id = st.session_state.get('current_course_id')
                        success = False
                        if c_id:
                             success = rename_course(c_id, safe_rename)
                        
                        if success:
                             # 2. Local Update (Secondary - Best Effort)
                             if os.path.exists(dst):
                                 st.warning("El nombre se actualizÃ³ en la base de datos, pero la carpeta local ya existÃ­a (se omitiÃ³ renombre local).")
                             else:
                                 try:
                                     if os.path.exists(src):
                                         os.rename(src, dst)
                                     else:
                                         # Create new folder if it doesn't exist (ensure sync)
                                         os.makedirs(dst, exist_ok=True)
                                 except Exception as e:
                                     st.warning(f"Nombre actualizado en DB, pero error local: {e}")

                             st.session_state['current_course'] = safe_rename
                             st.success("Â¡Renombrado!")
                             st.rerun()
                        else:
                             st.error("Error actualizando base de datos.")

    # DELETE OPTION
    with st.expander("ðŸ—‘ï¸ Borrar Diplomados"):
        # Filter out "Crear Nuevo" if present or just use db_courses list
        del_options = [c['name'] for c in db_courses]
        courses_to_del = st.multiselect("Selecciona para borrar:", del_options, key="del_courses_sel")
        
        if st.button("Eliminar Seleccionados", key="btn_del_courses"):
            if courses_to_del:
                deleted_count = 0
                for c_name in courses_to_del:
                    # Find ID
                    c_id_to_del = course_map.get(c_name)
                    if c_id_to_del:
                        if delete_course(c_id_to_del):
                             deleted_count += 1
                        else:
                             st.error(f"Error borrando {c_name}")
                
                if deleted_count > 0:
                    st.success(f"Â¡{deleted_count} diplomados eliminados!")
                    # Clear session if current was deleted
                    if st.session_state.get('current_course') in courses_to_del:
                         st.session_state['current_course'] = None
                         st.session_state['current_course_id'] = None
                    time.sleep(1)
                    st.rerun()

    st.caption(f"Guardando en: `output/{st.session_state['current_course']}/...`")
    st.divider()
    
    # (Removed Carpetas de Salida Info Box as per user request)

    # --- INJECT CUSTOM TAB SCROLL BUTTONS (JS) ---
    st.components.v1.html("""
    <script>
    function addTabScrollButtons() {
        const doc = window.parent.document;
        const tabList = doc.querySelector('div[role="tablist"]');
        
        if (tabList && !doc.getElementById('tab-scroll-left')) {
            // Style the tabList for scroll
            tabList.style.overflowX = 'auto';
            tabList.style.scrollBehavior = 'smooth';
            tabList.style.scrollbarWidth = 'none'; // Hide scrollbar
            
            // Create Left Button
            const btnLeft = doc.createElement('button');
            btnLeft.id = 'tab-scroll-left';
            btnLeft.innerHTML = 'â—€';
            btnLeft.onclick = () => tabList.scrollBy({left: -200, behavior: 'smooth'});
            
            // Create Right Button
            const btnRight = doc.createElement('button');
            btnRight.id = 'tab-scroll-right';
            btnRight.innerHTML = 'â–¶';
            btnRight.onclick = () => tabList.scrollBy({left: 200, behavior: 'smooth'});
            
            // Shared Styles
            const btnStyle = `
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                cursor: pointer;
                z-index: 100;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            `;
            
            btnLeft.style.cssText = btnStyle + 'left: 0px;';
            btnRight.style.cssText = btnStyle + 'right: 0px;';
            
            // Find container to attach relative positioning
            const parent = tabList.parentElement;
            parent.style.position = 'relative';
            parent.style.padding = '0 35px'; // Make space for buttons
            
            parent.appendChild(btnLeft);
            parent.appendChild(btnRight);
        }
    }
    // Run after a slight delay to ensure DOM is ready
    setTimeout(addTabScrollButtons, 500);
    setTimeout(addTabScrollButtons, 1500); // Retry
    </script>
    """, height=0)

    # --- TABS DEFINITION ---
tab1, tab2, tab3, tab4, tab_lib, tab5, tab6 = st.tabs([
    "ðŸ“¹ Transcriptor", 
    "ðŸ“ Apuntes Simples", 
    "ðŸ—ºï¸ GuÃ­a de Estudio", 
    "ðŸ§  Ayudante Quiz",
    "ðŸ“‚ Biblioteca",
    "ðŸ‘©â€ðŸ« Ayudante de Tareas",
    "ðŸ“š TutorÃ­a 1 a 1"
])

# --- Helper for ECharts Visualization ---


# --- Helper for styled image container ---
# --- Helper for styled image container ---
def render_image_card(img_path):
    import base64
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode()
        
        card_html = (
            f'<div style="'
            f'    background-color: #f3e8ff;'
            f'    border-radius: 20px;'
            f'    padding: 40px;'
            f'    display: flex;'
            f'    align-items: center;'
            f'    justify-content: center;'
            f'    height: 100%;'
            f'">'
            f'    <img src="data:image/png;base64,{b64_img}" style="'
            f'        width: 100%; '
            f'        max-width: 400px;'
            f'        height: auto; '
            f'        filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));'
            f'    ">'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error(f"Image not found: {img_path}")

# --- TAB LIBRARY ---
with tab_lib:
    if 'assistant' in locals() and assistant:
         render_library(assistant)
    else:
         st.info("âš ï¸ Configura tu API Key en la barra lateral para activar la Biblioteca IA.")

# --- TAB 1: Transcriptor ---
with tab1:
    # LAYOUT: Image Left (1) | Text Right (1.5)
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
        render_image_card("illustration_transcriber_1765052797646.png")

    with col_text:
        tab1_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">1. Transcriptor de Videos</h2>'
            '<p style="color: #64748b; font-size: 1.1rem; margin-bottom: 20px;">'
            'Sube los videos de tu unidad para procesarlos automÃ¡ticamente.'
            '</p>'
            '</div>'
        )
        st.markdown(tab1_html, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("Arrastra tus archivos aquÃ­", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True, key="up1")
        
        if uploaded_files:
            if st.button("Iniciar TranscripciÃ³n", key="btn1", use_container_width=True):
                # Validation
                c_id = st.session_state.get('current_course_id')
                if not c_id:
                    st.error("âš ï¸ Selecciona un Espacio de Trabajo en la barra lateral primero.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    from database import get_units, create_unit, upload_file_to_db, get_files
                    
                    # Get/Create "Transcripts" Unit
                    units = get_units(c_id)
                    t_unit = next((u for u in units if u['name'] == "Transcripts"), None)
                    if not t_unit:
                         status_text.write("Creando carpeta 'Transcripts'...")
                         t_unit = create_unit(c_id, "Transcripts")
                    
                    if t_unit:
                        t_unit_id = t_unit['id']
                        
                        for i, file in enumerate(uploaded_files):
                            status_text.markdown(f"**Iniciando {file.name}... (0%)**")
                            temp_path = file.name
                            with open(temp_path, "wb") as f: f.write(file.getbuffer())
                            
                            try:
                                # Define callback
                                def update_ui(msg, prog):
                                    pct = int(prog * 100)
                                    progress_bar.progress(prog)
                                    status_text.markdown(f"**{msg} ({pct}%)**")

                                # Process
                                txt_path = transcriber.process_video(temp_path, progress_callback=update_ui, chunk_length_sec=600)
                                
                                # Read and Upload to DB
                                with open(txt_path, "r", encoding="utf-8") as f: 
                                    trans_text = f.read()
                                    
                                upload_file_to_db(t_unit_id, os.path.basename(txt_path), trans_text, "transcript")
                                
                                st.success(f"âœ… {file.name} guardado en Nube (Carpeta Transcripts)")
                                
                                # Store in session state for immediate display
                                st.session_state['transcript_history'].append({"name": file.name, "text": trans_text})
                                
                                # Cleanup local temp files
                                if os.path.exists(txt_path): os.remove(txt_path)
                                
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                if os.path.exists(temp_path): os.remove(temp_path)
                            
                            progress_bar.progress(1.0)
                        
                        status_text.success("Â¡Todo listo! (100%)")
                    else:
                        st.error("No se pudo crear carpeta de transcripts.")

        # --- PERSISTENT RESULTS DISPLAY (Outside button block) ---
        if st.session_state['transcript_history']:
            for i, item in enumerate(st.session_state['transcript_history']):
                st.divider()
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown(f"### ðŸ“„ TranscripciÃ³n: {item['name']}")
                with c_copy:
                    if st.button("ðŸ“„", key=f"cp_t_{i}", help="Copiar Texto Limpio"):
                        clean_txt = clean_markdown(item['text'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("Â¡Copiado!", icon='ðŸ“‹')
                st.markdown(item['text'])

# --- TAB 2: Apuntes Simples ---
with tab2:
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
         render_image_card("illustration_notes_1765052810428.png")
         
    with col_text:
        tab2_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">2. Generador de Apuntes</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">Convierte transcripciones en apuntes claros y concisos.</p>'
            '</div>'
        )
        st.markdown(tab2_html, unsafe_allow_html=True)
        
        c_id = st.session_state.get('current_course_id')
        if not c_id:
             st.info("Selecciona Espacio de Trabajo.")
        else:
             # Fetch Transcripts from DB
             from database import get_units, get_files, get_file_content, upload_file_to_db
             
             units = get_units(c_id)
             t_unit = next((u for u in units if u['name'] == "Transcripts"), None)
             
             transcript_files = []
             if t_unit:
                 transcript_files = get_files(t_unit['id'])
             
             # Check Global Memory
             gl_ctx, gl_count = get_global_context()
             if gl_count > 0:
                st.success(f"âœ… **Memoria Global Activa:** {gl_count} archivos base detectados.")
            
             if not transcript_files:
                st.info("No hay transcripciones. Sube videos en la PestaÃ±a 1 (se crearÃ¡ carpeta 'Transcripts').")
             else:
                options = [f['name'] for f in transcript_files]
                file_map = {f['name']: f['id'] for f in transcript_files}
                
                selected_file = st.selectbox("Selecciona una transcripciÃ³n:", options, key="sel2")
                
                if selected_file and st.button("Generar Apuntes", key="btn2"):
                    # Get content from DB
                    f_id = file_map[selected_file]
                    text = get_file_content(f_id)
                    
                    with st.spinner("Creando apuntes progresivos (3 Niveles)..."):
                        # Now returns a JSON dict
                        notes_data = assistant.generate_notes(text, global_context=gl_ctx)
                        
                        # Save to "Notes" Unit in DB
                        n_unit = next((u for u in units if u['name'] == "Notes"), None)
                        if not n_unit:
                             # Create Notes unit if not exists
                             from database import create_unit
                             n_unit = create_unit(c_id, "Notes")
                        
                        if n_unit:
                             import json
                             json_content = json.dumps(notes_data, ensure_ascii=False, indent=2)
                             base_name = selected_file.replace("_transcripcion.txt", "")
                             fname = f"Apuntes_{base_name}.json"
                             
                             upload_file_to_db(n_unit['id'], fname, json_content, "note")
                             st.success(f"Apuntes guardados en 'Notes'/{fname}")
                        
                        st.session_state['notes_result'] = notes_data
                        st.success("Â¡Apuntes generados en 3 capas!")

                # --- DISPLAY RESULTS ---
                if st.session_state['notes_result']:
                    res = st.session_state['notes_result']
                    
                    # Check if it's new dict format (Progressive) or old string (Legacy)
                    if isinstance(res, dict):
                        st.markdown("### ðŸ“ Apuntes Progresivos")
                        
                        # LEVEL 1: Ultracorto
                        with st.expander("ðŸŸ¢ Nivel 1: Ultracorto (5 Puntos)", expanded=True):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('ultracorto', ''))
                            with c2:
                                if st.button("ðŸ“„", key="copy_l1", help="Copiar Nivel 1"):
                                    copy_to_clipboard(res.get('ultracorto', ''))
                                    st.toast("Copiado Nivel 1")

                        # LEVEL 2: Intermedio
                        with st.expander("ðŸŸ¡ Nivel 2: Intermedio (Conceptos Clave)", expanded=False):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('intermedio', ''))
                            with c2:
                                if st.button("ðŸ“„", key="copy_l2", help="Copiar Nivel 2"):
                                    copy_to_clipboard(res.get('intermedio', ''))
                                    st.toast("Copiado Nivel 2")

                        # LEVEL 3: Profundo
                        with st.expander("ðŸ”´ Nivel 3: Profundidad (ExplicaciÃ³n Completa)", expanded=False):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('profundo', ''))
                            with c2:
                                 if st.button("ðŸ“„", key="copy_l3", help="Copiar Nivel 3"):
                                    copy_to_clipboard(res.get('profundo', ''))
                                    st.toast("Copiado Nivel 3")
                                    
                    else:
                        # Legacy String Display
                        st.markdown(res)
                        if st.button("Copiar Apuntes", key="copy_notes_btn"):
                             copy_to_clipboard(res)
                             st.toast("Copiado")

# --- TAB 3: GuÃ­a de Estudio ---
with tab3:
    col_img, col_text = st.columns([1, 1.5], gap="large") # Swapped to Image Left
    
    with col_img:
        render_image_card("illustration_guide_1765052821852.png")
    
    with col_text:
        tab3_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">3. GuÃ­a de Estudio EstratÃ©gica</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">Crea mapas, resÃºmenes y preguntas de examen.</p>'
            '</div>'
        )
        st.markdown(tab3_html, unsafe_allow_html=True)
        
        c_id = st.session_state.get('current_course_id')
        if not c_id:
             st.info("Selecciona Espacio de Trabajo.")
        else:
            from database import get_units, get_files, get_file_content, upload_file_to_db, create_unit
            
            # Fetch Transcripts
            units = get_units(c_id)
            t_unit = next((u for u in units if u['name'] == "Transcripts"), None)
            
            transcript_files = []
            if t_unit:
                transcript_files = get_files(t_unit['id'])
            
            # Check Global Memory
            gl_ctx, gl_count = get_global_context()
            if gl_count > 0:
                st.success(f"âœ… **Memoria Global Activa:** {gl_count} archivos base detectados.")

            if not transcript_files:
                 st.info("Primero sube videos en la PestaÃ±a 1.")
            else:
                options_guide = [f['name'] for f in transcript_files]
                file_map_guide = {f['name']: f['id'] for f in transcript_files}
                
                selected_guide_file = st.selectbox("Archivo base:", options_guide, key="sel3")
                
                if selected_guide_file and st.button("Generar GuÃ­a", key="btn3"):
                    # Get content from DB
                    f_id = file_map_guide[selected_guide_file]
                    text = get_file_content(f_id)
                        
                    with st.spinner("DiseÃ±ando estrategia de estudio..."):
                        guide = assistant.generate_study_guide(text, global_context=gl_ctx)
                        
                        # Save to "Guides" Unit in DB
                        g_unit = next((u for u in units if u['name'] == "Guides"), None)
                        if not g_unit:
                             g_unit = create_unit(c_id, "Guides")
                        
                        if g_unit:
                             base_name = selected_guide_file.replace("_transcripcion.txt", "")
                             fname = f"Guia_{base_name}.txt"
                             upload_file_to_db(g_unit['id'], fname, guide, "guide")
                             st.success(f"GuÃ­a guardada en 'Guides'/{fname}")

                        st.success("Â¡GuÃ­a lista!")
                        st.session_state['guide_result'] = guide # Save to session
            
            # --- PERSISTENT RESULTS DISPLAY ---
            if st.session_state['guide_result']:
                st.divider()
                
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown("### ðŸ—ºï¸ Tu GuÃ­a de Estudio")
                with c_copy:
                    if st.button("ðŸ“„", key="cp_guide", help="Copiar GuÃ­a Limpia"):
                        clean_txt = clean_markdown(st.session_state['guide_result'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("Â¡Copiado!", icon='ðŸ“‹')
                
                # Visual Display
                st.markdown(st.session_state['guide_result'])

# --- TAB 4: Quiz ---
with tab4:
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
        render_image_card("illustration_quiz_1765052844536.png")
        
    with col_text:
        tab4_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">4. Ayudante de Pruebas</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">Modo RÃ¡faga: Sube mÃºltiples preguntas y obtÃ©n las respuestas.</p>'
            '</div>'
        )
        st.markdown(tab4_html, unsafe_allow_html=True)
        
        # Check Global Memory
        gl_ctx, gl_count = get_global_context()
        if gl_count > 0:
            st.success(f"âœ… **Memoria Global Activa:** Usando {gl_count} archivos para mayor precisiÃ³n.")
        
        # RESET BUTTON
        col_up, col_reset = st.columns([0.9, 0.1])
        with col_reset:
             # Use the same 'copy-btn' style or just a clean emoji button
             if st.button("ðŸ—‘ï¸", key="reset_quiz", help="Borrar todo para empezar de cero"):
                 st.session_state['quiz_results'] = []
                 st.session_state['pasted_images'] = []
                 st.session_state['quiz_key'] += 1
                 st.rerun()
                 
        with col_up:
            # Clipboard Paste Button
            if st.button("ðŸ“‹ Pegar Imagen (Portapapeles)", key="paste_btn", help="Haz Ctrl+V en tu PC, luego click aquÃ­ para cargar la imagen."):
                try:
                    img = ImageGrab.grabclipboard()
                    if isinstance(img, Image.Image):
                        # Convert to RGB to avoid alpha issues
                        if img.mode == 'RGBA': img = img.convert('RGB')
                        st.session_state['pasted_images'].append(img)
                        st.toast("Imagen pegada con Ã©xito!", icon='ðŸ“¸')
                    else:
                        st.warning("No hay imagen en el portapapeles. (Haz PrtScrn o Copiar Imagen primero)")
                except Exception as e:
                    st.error(f"Error pegando: {e}")

            # Show Pasted Thumbnails
            if st.session_state['pasted_images']:
                st.caption(f"ðŸ“¸ {len(st.session_state['pasted_images'])} capturas pegadas:")
                cols_past = st.columns(len(st.session_state['pasted_images']))
                for idx, p_img in enumerate(st.session_state['pasted_images']):
                    with cols_past[idx]:
                        st.image(p_img, width=50)

            img_files = st.file_uploader("O sube archivos manualmente:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"up4_{st.session_state['quiz_key']}")
        
        # COMBINE INPUTS
        total_images_len = len(img_files) + len(st.session_state['pasted_images']) if img_files else len(st.session_state['pasted_images'])

        if total_images_len > 0 and st.button("Resolver Preguntas", key="btn4"):
            progress_bar = st.progress(0)
            status = st.empty()
            results = [] 
            
            # 1. Process Files
            all_imgs_to_process = []
            
            # Adapt UploadedFiles to be processable
            if img_files:
                for f in img_files:
                    all_imgs_to_process.append({"type": "upload", "obj": f, "name": f.name})
            
            # Adapt Pasted Images
            for i, p_img in enumerate(st.session_state['pasted_images']):
                 all_imgs_to_process.append({"type": "paste", "obj": p_img, "name": f"Captura_Pegada_{i+1}.png"})

            for i, item in enumerate(all_imgs_to_process):
                # Calculate percentages
                current_percent = int((i / len(all_imgs_to_process)) * 100)
                status.markdown(f"**Analizando foto {i+1} de {len(all_imgs_to_process)}... ({current_percent}%)**")
                progress_bar.progress(i / len(all_imgs_to_process))
                
                temp_img_path = f"temp_quiz_{i}.png"
                
                # Save Temp
                # Save Temp (force PNG for quality)
                if item["type"] == "upload":
                    with open(temp_img_path, "wb") as f: f.write(item["obj"].getbuffer())
                else:
                    item["obj"].save(temp_img_path, format="PNG")
                
                try:
                    # Load image for display before deleting temp
                    disp_img = Image.open(temp_img_path).copy()
                    
                    full_answer = assistant.solve_quiz(temp_img_path, global_context=gl_ctx)
                    
                    # Robust Regex Parsing for Short Answer
                    import re
                    short_answer = "Respuesta no detectada (Ver detalle)"
                    match = re.search(r"\*\*Respuesta Correcta:?\*\*?\s*(.*)", full_answer, re.IGNORECASE)
                    if match:
                         short_answer = match.group(1).strip()
                    
                    results.append({"name": item["name"], "full": full_answer, "short": short_answer, "img_obj": disp_img})
                except Exception as e:
                    results.append({"name": item["name"], "full": str(e), "short": "Error", "img_obj": None})
                finally:
                    # Windows file lock fix: Try to remove, if fails wait and try again
                    if os.path.exists(temp_img_path):
                        import time
                        for _ in range(3):
                            try:
                                os.remove(temp_img_path)
                                break
                            except PermissionError:
                                time.sleep(0.5)
                        # If still failing, ignore it (will be cleaned up later or overwritten)
                
            progress_bar.progress(1.0)
            status.success("Â¡AnÃ¡lisis Terminado! (100%)")
            st.session_state['quiz_results'] = results # Save results

        # --- PERSISTENT RESULTS DISPLAY ---
        if st.session_state['quiz_results']:
            st.divider()
            
            # HEADER + COPY ICON
            c_head, c_copy = st.columns([0.9, 0.1])
            with c_head:
                st.markdown("### ðŸ“‹ Resultados de Quiz")
            with c_copy:
                # Compile text for copying inside the button action
                full_report_copy = "--- HOJA DE RESPUESTAS ---\n\n"
                for i, res in enumerate(st.session_state['quiz_results']):
                     full_report_copy += f"FOTO {i+1}: {res['short']}\n"
                full_report_copy += "\n--- DETALLES ---\n"
                for i, res in enumerate(st.session_state['quiz_results']):
                     full_report_copy += f"\n[FOTO {i+1}]\n{res['full']}\n"
                     
                if st.button("ðŸ“„", key="cp_quiz", help="Copiar Resultados Limpios"):
                    clean_txt = clean_markdown(full_report_copy)
                    if copy_to_clipboard(clean_txt):
                        st.toast("Â¡Copiado!", icon='ðŸ“‹')
            
            # --- RESULTS DISPLAY ---
            # Visual Display (Markdown instead of Code Block)
            st.markdown("#### ðŸ“ Hoja de Respuestas RÃ¡pida")
            
            # Build a nice markdown list for visual display
            md_list = ""
            for i, res in enumerate(st.session_state['quiz_results']):
                md_list += f"- **Foto {i+1}:** {res['short']}\n"
            st.markdown(md_list)
            
            st.divider()
            st.markdown("#### ðŸ” Detalles por Pregunta")
            
            for i, res in enumerate(st.session_state['quiz_results']):
                with st.expander(f"Ver detalle de Foto {i+1}"):
                    if 'img_obj' in res:
                        try:
                            st.image(res['img_obj'], width=300)
                        except:
                            st.warning("Imagen no disponible tras recarga")
                    st.markdown(res['full'])

# --- TAB 5: Ayudante de Tareas ---
with tab5:
    tab5_html = (
        '<div class="card-text">'
        '<h2 style="margin-top:0;">5. Ayudante de Tareas & Biblioteca</h2>'
        '<p style="color: #64748b; font-size: 1.1rem;">Tu "Segundo Cerebro": Guarda conocimientos y Ãºsalos para resolver tareas.</p>'
        '</div>'
    )
    st.markdown(tab5_html, unsafe_allow_html=True)
    
    # --- LAYOUT REFOCUSED ON TASK SOLVER ---
    col_task = st.container()
    
    st.info("ðŸ’¡ Gestiona tus archivos, sube documentos y organiza carpetas en la nueva pestaÃ±a 'ðŸ“‚ Biblioteca'.")

    # --- RIGHT COLUMN: HOMEWORK SOLVER (Now Main) ---
    with col_task:
        c_title, c_trash = st.columns([0.85, 0.15])
        with c_title:
            st.markdown("### ðŸ§  Ayudante Inteligente")
            st.caption("Resuelve tareas usando SOLO la informaciÃ³n de tu biblioteca.")
        with c_trash:
            if st.button("ðŸ—‘ï¸", key="clear_hw_btn", help="Borrar tarea y empezar de cero"):
                st.session_state['homework_result'] = None
                st.rerun()
        
        # MODE TOGGLE
        arg_mode = st.toggle("ðŸ§  Activar Modo Argumentador (Abogado del Diablo)", key="arg_mode_toggle", help="Activa un anÃ¡lisis profundo con 4 dimensiones: Respuesta, Fuentes, Paso a Paso y Contra-argumento.")
        
        # 1. Select Context
        st.markdown("**1. Â¿QuÃ© conocimientos uso?** (SelecciÃ³n por Unidad)")
        
        # DB Logic for Context Selection
        from database import get_units, get_unit_context
        
        current_course_id = st.session_state.get('current_course_id')
        db_units = get_units(current_course_id) if current_course_id else []
        
        # Find Global Unit
        global_unit = next((u for u in db_units if u['name'] == "00_Memoria_Global"), None)
        has_global = global_unit is not None
        
        if has_global:
            st.success(f"âœ… **Memoria Global Activa** (Temarios/Reglas).")
            
        st.caption("â„¹ï¸ AdemÃ¡s de la Memoria Global, selecciona las unidades especÃ­ficas para esta tarea:")
        
        # Filter available units (excluding Global)
        available_units_objs = [u for u in db_units if u['name'] != "00_Memoria_Global"]
        available_unit_names = [u['name'] for u in available_units_objs]
        unit_map = {u['name']: u['id'] for u in available_units_objs}
        
        selected_units = st.multiselect("Unidades EspecÃ­ficas:", available_unit_names, placeholder="Ej: Unidad 1...")
        
        # 2. Input Task
        st.markdown("**2. Tu Tarea:**")
        task_prompt = st.text_area("Describe la tarea o pega la consigna:", height=100, placeholder="Ej: Crea un perfil de cliente ideal usando el mÃ©todo de la Unidad 1...")
        
        # ATTACHMENT UPLOADER
        task_file = st.file_uploader("Adjuntar consigna (PDF, Imagen, TXT)", type=['pdf', 'png', 'jpg', 'jpeg', 'txt'])
        
        btn_label = "âš”ï¸ Debatir y Solucionar" if arg_mode else "ðŸš€ Resolver Tarea"
        
        if st.button(btn_label, key="solve_task", use_container_width=True):
            if not task_prompt and not task_file:
                st.warning("âš ï¸ Escribe la tarea o sube un archivo.")
            else:
                # Gather context
                gathered_texts = []
                
                # CHECK IF RUNNING ON EMPTY LIBRARY
                using_general_knowledge = False
                if not selected_units and not has_global:
                    using_general_knowledge = True
                    st.toast("âš ï¸ Sin biblioteca seleccionada. Usando Conocimiento General de Gemini.", icon="ðŸŒ")
                
                # 1. Add Global Context
                if has_global:
                    g_text = get_unit_context(global_unit['id'])
                    if g_text:
                        gathered_texts.append(f"--- [MEMORIA GLOBAL / OBLIGATORIO] ---\n{g_text}\n")

                # 2. Add Selected Units
                for u_name in selected_units:
                    u_id = unit_map[u_name]
                    u_text = get_unit_context(u_id)
                    if u_text:
                        gathered_texts.append(u_text)
                
                # Prepare Attachment
                attachment_data = None
                if task_file:
                    attachment_data = {
                        "mime_type": task_file.type,
                        "data": task_file.getvalue()
                    }
                
                with st.spinner("Analizando caso... (Modo Experto)" if arg_mode else "Consultando biblioteca..."):
                    try:
                        if arg_mode:
                            full_context_str = "\n".join(gathered_texts)
                            solution = assistant.solve_argumentative_task(task_prompt, context_files=[], global_context=full_context_str)
                        else:
                            solution = assistant.solve_homework(task_prompt, gathered_texts, task_attachment=attachment_data)
                            
                        st.session_state['homework_result'] = solution
                    except Exception as e:
                         # Detailed error logging
                        st.error(f"Error resolviendo tarea: {e}")
        
        # --- RESULT DISPLAY ---
        if st.session_state['homework_result']:
            st.divider()
            res = st.session_state['homework_result']
            
            # ARGUMENTATOR MODE DISPLAY (Dict/JSON)
            if isinstance(res, dict):
                 st.markdown("### ðŸ›¡ï¸ AnÃ¡lisis del Consultor (Modo Argumentador)")
                 
                 # Tabs for Output
                 t_resp, t_src, t_steps = st.tabs(["ðŸ’¡ Respuesta", "ðŸ“š Fuentes", "ðŸ‘£ Paso a Paso"])
                 
                 with t_resp:
                     st.markdown(res.get('direct_response', ''))
                     if st.button("ðŸ“„ Copiar Respuesta", key="cp_arg_resp"):
                         copy_to_clipboard(res.get('direct_response', ''))
                         st.toast("Copiada Respuesta")
                         
                 with t_src:
                     st.markdown(res.get('sources', 'No se citaron fuentes especÃ­ficas.'))
                     
                 with t_steps:
                     st.markdown(res.get('step_by_step', ''))
                     
                 # Counter Argument (Hidden)
                 with st.expander("ðŸ§¨ Ver Contra-Argumento (Abogado del Diablo)"):
                     st.warning("âš ï¸ Estas son las objeciones que un profesor estricto te harÃ­a:")
                     st.markdown(res.get('counter_argument', ''))
                     
            else:
                # LEGACY DISPLAY (String)
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown("### âœ… Respuesta")
                with c_copy:
                     if st.button("ðŸ“„", key="cp_hw", help="Copiar Respuesta"):
                        clean_txt = clean_markdown(res)
                        if copy_to_clipboard(clean_txt):
                            st.toast("Â¡Copiado!", icon='ðŸ“‹')
                
                st.markdown(res)

            # --- BRIDGE TO TUTOR ---
            st.divider()
            if st.button("ðŸ—£ï¸ Debatir esta respuesta con el Profesor (Ir a TutorÃ­a)", key="btn_bridge_tutor", help="EnvÃ­a esta tarea y respuesta al chat de TutorÃ­a para discutirla."):
                # Format the context for the tutor
                full_text_response = ""
                if isinstance(res, dict):
                    full_text_response = f"**Respuesta:**\n{res.get('direct_response','')}\n\n**Contra-argumento:**\n{res.get('counter_argument','')}"
                else:
                    full_text_response = str(res)
                
                bridge_msg = (
                    f"Hola Profe IA. Acabo de generar una respuesta para esta tarea:\n\n"
                    f"**CONSIGNA:**\n_{task_prompt}_\n\n"
                    f"**MI BORRADOR (Generado por Asistente):**\n{full_text_response}\n\n"
                    f"Quiero que analicemos esto. QuÃ© opinas? Podemos mejorarlo?"
                )
                
                # Check if history exists
                if 'tutor_chat_history' not in st.session_state:
                    st.session_state['tutor_chat_history'] = []
                
                # Append Bridge Message as USER
                st.session_state['tutor_chat_history'].append({"role": "user", "content": bridge_msg})
                
                # AUTO-REPLY LOGIC: Trigger response immediately so it's ready when user switches tabs
                # Prepare Context (Global)
                gl_ctx_bridge, _ = get_global_context()
                
                with st.spinner("El profesor estÃ¡ analizando tu respuesta..."):
                    try:
                        # We use the same chat_tutor method
                        response_bridge = assistant.chat_tutor(
                            bridge_msg, 
                            chat_history=st.session_state['tutor_chat_history'], 
                            context_files=[], # No new files attached in this bridge action logic yet
                            global_context=gl_ctx_bridge
                        )
                        # Append Assistant Response
                        st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response_bridge})
                        
                        st.success("âœ… Â¡InformaciÃ³n enviada y el Profesor YA TE RESPONDIÃ“!")
                        st.info("ðŸ‘ˆ Ve ahora a la pestaÃ±a 'ðŸ“š TutorÃ­a 1 a 1' para ver su correcciÃ³n.")
                        
                    except Exception as e:
                        st.error(f"Error generando respuesta automÃ¡tica del tutor: {e}")

# --- TAB 6: TutorÃ­a 1 a 1 (Docente Artificial) ---
if 'tutor_chat_history' not in st.session_state: st.session_state['tutor_chat_history'] = []

with tab6:
    tutor_html = (
        '<div class="card-text">'
        '<h2 style="margin-top:0;">6. TutorÃ­a Personalizada (Profesor IA)</h2>'
        '<p style="color: #64748b; font-size: 1.1rem;">Tu profesor particular. Pregunta, sube tareas para corregir y dialoga en tiempo real.</p>'
        '</div>'
    )
    st.markdown(tutor_html, unsafe_allow_html=True)
    
    col_chat, col_info = st.columns([2, 1], gap="large")
    
    with col_info:
        st.info("â„¹ï¸ **Memoria Activa:** El profesor recuerda vuestra conversaciÃ³n y tiene acceso total a la Biblioteca Global.")
        st.divider()
        st.markdown("### ðŸ“Ž Adjunto RÃ¡pido")
        tutor_file = st.file_uploader("Subir archivo al chat", type=['pdf', 'txt', 'png', 'jpg'], key="tutor_up")
        
        if st.button("ðŸ—‘ï¸ Borrar Historial", key="clear_chat"):
            st.session_state['tutor_chat_history'] = []
            st.rerun()

    with col_chat:
        # Display Chat History
        for msg in st.session_state['tutor_chat_history']:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])
        
        # User Input
        if prompt := st.chat_input("Â¿En quÃ© puedo ayudarte hoy, alumno?"):
            # 1. Add User Message
            st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            # 2. Prepare Context (Global + Upload)
            gl_ctx, _ = get_global_context()
            
            # Helper to read uploaded file just for this turn
            chat_files = []
            if tutor_file:
                # Basic reading based on type
                try:
                    content = ""
                    if tutor_file.type == "application/pdf":
                        content = assistant.extract_text_from_pdf(tutor_file.getvalue(), tutor_file.type)
                    else:
                        # Assuming text/image logic
                        # For text files
                        try:
                           content = tutor_file.getvalue().decode("utf-8", errors='ignore')
                        except:
                           content = "Archivo binario/imagen no procesado en texto crudo."
                    
                    chat_files.append({"name": tutor_file.name, "content": content})
                    st.toast(f"ðŸ“Ž Archivo {tutor_file.name} enviado al profesor.")
                except Exception as e:
                    st.error(f"Error leyendo archivo: {e}")

            # 3. Generate Response
            with st.chat_message("assistant"):
                with st.spinner("El profesor estÃ¡ escribiendo..."):
                    response = assistant.chat_tutor(
                        prompt, 
                        chat_history=st.session_state['tutor_chat_history'], 
                        context_files=chat_files, 
                        global_context=gl_ctx
                    )
                    st.markdown(response)
            
            # 4. Save Response
            st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response})

