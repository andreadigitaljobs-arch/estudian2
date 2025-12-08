
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
if 'spotlight_mode' not in st.session_state: st.session_state['spotlight_mode'] = "⚡ Concepto Rápido"
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
    st.markdown("## 🔐 Iniciar Sesión en Estudian2")
    st.caption("Modo Nube Multi-Usuario (Supabase)")
    
    # Simple formatting for Login
    tab_login, tab_signup = st.tabs(["Ingresar", "Registrarse"])
    
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_pass")
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
                st.success(f"¡Bienvenido!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciales incorrectas o error de conexión.")

    with tab_signup:
        new_email = st.text_input("Email", key="reg_email")
        new_pass = st.text_input("Contraseña", type="password", key="reg_pass")
        if st.button("Crear Cuenta", key="btn_reg"):
            from database import sign_up
            user = sign_up(new_email, new_pass)
            if user:
                if 'supabase_session' in st.session_state:
                     sess = st.session_state['supabase_session']
                     cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                st.success("Cuenta creada. Por favor inicia sesión.")
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
    mode = st.session_state.get('spotlight_mode', "⚡ Concepto Rápido")
    
    # Visual Container
    st.markdown(f"#### 🔍 Resultados de Spotlight: *{query}*")
    
    with st.spinner(f"Investigando en tu bibliografía ({mode})..."):
        if not assistant:
             st.error("⚠️ Configura tu API Key en la barra lateral primero.")
        else:
            # 1. Get Context (Efficiency: Only load if we search)
            gl_ctx, gl_count = get_global_context()
            
            if gl_count == 0:
                st.warning("⚠️ Tu cerebro digital está vacío. Sube videos o archivos a la Biblioteca primero.")
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
                    if "Rápido" in mode:
                        st.info(final_res, icon="⚡")
                    else:
                        st.success(final_res, icon="🕵️")
                        
                except Exception as e:
                    st.error(f"Error en Spotlight: {e}")
            
    if st.button("Cerrar Búsqueda", key="close_spot"):
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

    /* --- GLOBAL VARIABLES --- */
    :root {
        --primary-purple: #4B22DD;
        --accent-green: #6CC04A;
        --bg-color: #F8F9FE;
        --card-bg: #FFFFFF;
        --text-color: #1A1A1A;
        --border-color: #E3E4EA;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text-color);
        background-color: var(--bg-color);
    }

    /* 1. APP BACKGROUND (Light) */
    .stApp {
        background-color: var(--bg-color);
        background-image: none;
    }
    
    /* 2. TOP HEADER BAR - PURPLE */
    header[data-testid="stHeader"] {
        background-color: var(--primary-purple);
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* 3. THE CENTER CARD (Content) */
    .main .block-container {
        background-color: #ffffff;
        border-radius: 30px;
        padding: 3rem 4rem !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        margin-top: 20px;
        max-width: 95%;
    }
    div[data-testid="block-container"] {
        background-color: #ffffff;
        border-radius: 30px;
        padding: 3rem !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08);
        margin: 20px auto;
        max-width: 95%;
    }

    /* SIDEBAR CONTAINER */
    section[data-testid="stSidebar"], div[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border-color);
    }
    
    /* HEADERS */
    h1, h2, h3, h4 {
        color: var(--primary-purple);
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h1 { font-size: 2.5rem; }

    /* --- SIDEBAR SPECIFIC STYLES (MATCH REF IMAGE) --- */
    
    /* Custom "Logout" Button -> Purple Block */
    div[data-testid="stSidebar"] div.stButton button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border-radius: 30px !important; /* Pill shape like reference */
        text-align: center !important;
        justify-content: center !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        margin-top: 10px;
    }
    div[data-testid="stSidebar"] div.stButton button:hover {
        background-color: #3b1aa3 !important;
        color: white !important;
    }

    /* Sidebar Inputs -> Light Lilac BG */
    [data-testid="stSidebar"] div.stTextInput input, 
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #F4F1FF !important; /* Very light purple */
        border: 1px solid #E0D4FC !important;
        border-radius: 12px !important;
        color: #4B22DD !important;
    }

    /* "Clave del Sistema Activa" Box */
    .system-key-box {
        background-color: #E6F4EA;
        color: #1E4620;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #CEEAD6;
    }

    /* TABS */


    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
        padding: 0px;
        margin-bottom: 20px;
        border-bottom: 2px solid #F0F0F0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F5F6FA;
        border-radius: 8px 8px 0 0;
        color: #64748b;
        font-weight: 600;
        padding: 10px 20px;
        border: none;
    }
    
    /* UPDATED TAB STYLES: GREEN BOTTOM LINE */
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border-radius: 8px 8px 0 0 !important;
        border-bottom: 4px solid #6CC04A !important; /* THE GREEN LINE */
    }
    
    /* Remove default Streamlit tab highlight if present */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #6CC04A !important;
    }

    

    /* REMOVE SIDEBAR TOP PADDING */
    /* Target the container inside the sidebar */
    section[data-testid="stSidebar"] > div > div:first-child {
        padding-top: 1rem !important; /* Reduce specific top padding */
    }
    
    /* Also target the image explicitly if needed, but usually it's the container */
    [data-testid="stSidebar"] img {
        margin-top: -20px; /* Pull up slightly if Streamlit forces gap */
    }

    /* --- SIDEBAR FINE TUNING (REF IMAGE MATCH) --- */
    
    /* 1. Sidebar Headers (h4) -> Deep Purple */
    [data-testid="stSidebar"] h4 {
        color: #4B22DD !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 2. Sidebar Inputs (Text & Select) -> Light Lilac Background */
    /* Target the inner input element */
    [data-testid="stSidebar"] input {
        background-color: #F4F1FF !important;
        color: #4B22DD !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        border: 1px solid #D8CCF6 !important;
    }
    /* Target the container background for Selectbox */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #F4F1FF !important;
        border-color: #D8CCF6 !important;
        color: #4B22DD !important;
    }
    
    /* 3. Sidebar Buttons (Pill Shape, Purple) */
    /* We target the button element specifically inside sidebar */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #4B22DD !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important; /* Pill */
        margin-top: 10px !important;
        box-shadow: 0 4px 6px rgba(75, 34, 221, 0.2) !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #3b1aa3 !important;
        transform: translateY(-1px);
    }
    
    /* 4. "System Key" Box Tweaks */
    .system-key-box {
        background-color: #E6F4EA !important;
        border: 1px solid #CEEAD6 !important;
        color: #1E4620 !important;
        font-weight: 600 !important;
    }
    
    /* 5. Radio Buttons -> Custom Coloring if possible (Streamlit limits this) */
    [data-testid="stSidebar"] [role="radiogroup"] label {
        color: #1A1A1A !important;
        font-weight: 500 !important;
    }

    /* FORCE ALL SIDEBAR BUTTONS TO BE ROUNDED */
    [data-testid="stSidebar"] button {
        border-radius: 25px !important; /* High value for Pill shape */
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: transform 0.1s, box-shadow 0.1s !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Ensure Multiselect tags are also rounded if possible (Optional polish) */
    [data-testid="stSidebar"] span[data-baseweb="tag"] {
        border-radius: 15px !important;
    }

    /* --- TAB 1 REBRAND CSS --- */
    
    /* File Uploader Container */
    div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #F8F9FE;
        border: 2px dashed #B8B9E0 !important;
        border-radius: 20px !important;
        padding: 30px !important;
    }
    
    /* "Browse files" Button -> Bright Green */
    div[data-testid="stFileUploader"] button[kind="secondary"] {
        background-color: #6CC04A !important;
        color: white !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.8rem !important;
        text-transform: none !important;
        box-shadow: 0 4px 10px rgba(108, 192, 74, 0.4) !important;
    }
    div[data-testid="stFileUploader"] button[kind="secondary"]:hover {
        background-color: #5ab03a !important;
        color: white !important;
        transform: translateY(-1px);
    }
    
    /* Titles */
    h2.transcriptor-title {
        color: #4B22DD !important; /* Authentic Ref Purple */
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -1px !important;
        margin-bottom: 0.5rem !important;
    }
    
    p.transcriptor-subtitle {
        color: #4A4A4A !important;
        font-size: 1.05rem !important;
        margin-bottom: 30px !important;
        line-height: 1.6;
    }
    
    /* Green Placeholder Frame */
    .green-frame {
        background-color: #6CC04A;
        border-radius: 30px;
        padding: 20px;
        box-shadow: 0 15px 30px rgba(108, 192, 74, 0.25);
        height: 100%;
        min-height: 400px; /* Taller as per ref */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .green-frame-inner {
        background-color: #E2E8F0;
        border-radius: 20px;
        width: 100%;
        height: 100%;
        min-height: 360px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: #64748b;
        font-weight: 600;
    }

    /* --- GLOBAL BUTTON STYLING (Universal Consistency) --- */
    
    /* Target ALL standard buttons in the main app area */
    div.stButton > button {
        background-color: #4B22DD !important; /* Brand Purple */
        color: white !important;
        border-radius: 30px !important; /* Full Pill Shape */
        border: none !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(75, 34, 221, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    div.stButton > button:hover {
        background-color: #3b1aa3 !important; /* Darker Purple */
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(75, 34, 221, 0.3) !important;
    }
    
    /* Target Primary Buttons (if any are used, e.g. Delete, ensuring they are also round) */
    div.stButton > button[kind="primary"] {
        border-radius: 30px !important;
        /* Optionally keep them Red if they are destructive, or make them Green if positive. 
           User said "Morados en su mayoría y si no verdes". 
           Let's double check if we want to force EVERYTHING purple. 
           For "primary", Streamlit usually uses Red (User's ref). 
           I will enforce the SHAPE primarily. 
        */
    }
    
    div.stButton > button:active {
        background-color: #2a1275 !important;
        transform: translateY(0);
    }
    
    /* Specific overrides for "Green" actions can be handled via key-specific CSS if needed, 
       but for now "Iniciar Transcripción" will become Purple, which fits "Morados en su mayoría". */


    /* TAB SCROLL ARROWS (Corrected) */
    /* Target buttons in the tab list that are NOT tabs */
    .stTabs [data-baseweb="tab-list"] button:not([role="tab"]) {
        background-color: #4B22DD !important; /* Brand Purple */
        color: white !important;
        border-radius: 50% !important; /* Round */
        width: 30px !important;
        height: 30px !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    /* Ensure Icon is White */
    .stTabs [data-baseweb="tab-list"] button:not([role="tab"]) svg {
        fill: white !important;
        color: white !important;
    }

    /* Hover State */
    .stTabs [data-baseweb="tab-list"] button:not([role="tab"]):hover {
        background-color: #3b1aa3 !important;
    }

</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    # --- 1. LOGO & USER ---
    st.image("assets/logo_sidebar.png", use_container_width=True)
    
    if st.session_state.get('user'):
        st.markdown(f"👤 **{st.session_state['user'].email}**")
        if st.button("Cerrar Sesión", key="logout_btn", use_container_width=True):
            st.session_state['user'] = None
            if 'supabase_session' in st.session_state: del st.session_state['supabase_session']
            try: cookie_manager.delete("supabase_refresh_token")
            except: pass
            st.rerun()
    
    st.divider()

    # --- 2. SPOTLIGHT ACADÉMICO ---
    st.markdown("#### 🔍 Spotlight Académico")
    st.caption("¿Qué buscas hoy?")
    
    # Styled Input defined in CSS
    search_query = st.text_input("Busqueda", placeholder="Ej: 'Concepto de Lead'...", label_visibility="collapsed")
    
    # Radio with custom icons workaround via emoji
    search_mode = st.radio("Modo:", ["⚡ Concepto Rápido", "🕵️ Análisis Profundo"], horizontal=False, label_visibility="collapsed")
    
    # Search Button (Purple Pill via CSS)
    if st.button("Buscar 🔍", key="btn_spotlight", use_container_width=True):
        if search_query:
            st.session_state['spotlight_query'] = search_query
            st.session_state['spotlight_mode'] = search_mode
            st.rerun()
    
    st.divider()

    # --- 3. CONFIGURACIÓN PERSONAL ---
    st.markdown("#### ⚙️ Configuración Personal")
    
    # Check system key
    has_system_key = False
    try:
        if "GOOGLE_API_KEY" in st.secrets: has_system_key = True
    except: pass
    
    if has_system_key:
        st.markdown('<div class="system-key-box">✅ Clave del Sistema Activa</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Sin Clave del Sistema")
        
    st.write("") # Spacer
    user_key_input = st.text_input("Tu Clave API (Opcional)", type="password", help="Sobrescribe la clave del sistema.")
    if user_key_input:
        st.session_state['custom_api_key'] = user_key_input

    st.divider()
    
    # --- 4. ESPACIO DE TRABAJO ---
    st.markdown("#### 📂 Espacio de Trabajo")
    st.caption("Diplomado Actual:")
    
    # DB Ops
    from database import get_user_courses, create_course
    current_user_id = st.session_state['user'].id
    db_courses = get_user_courses(current_user_id)
    course_names = [c['name'] for c in db_courses]
    course_map = {c['name']: c['id'] for c in db_courses}
    
    if not course_names: course_names = []
    if 'current_course' not in st.session_state or st.session_state['current_course'] not in course_names:
        st.session_state['current_course'] = course_names[0] if course_names else None

    options = course_names + ["➕ Crear Nuevo..."]
    idx = 0
    if st.session_state['current_course'] in course_names: idx = course_names.index(st.session_state['current_course'])
    
    selected_option = st.selectbox("Diplomado", options, index=idx, label_visibility="collapsed")

    if selected_option == "➕ Crear Nuevo...":
        new_name = st.text_input("Nombre Nuevo:", placeholder="Ej: Curso IA")
        if st.button("Crear"):
            if new_name:
                nc = create_course(current_user_id, new_name)
                if nc: 
                    st.session_state['current_course'] = nc['name']
                    st.rerun()

    else:
        st.session_state['current_course'] = selected_option
        st.session_state['current_course_id'] = course_map[selected_option]
        
        # --- RESTORED ACTIONS (RENAME / DELETE) ---
        st.write("") # Micro spacer
        
        # RENAME
        with st.expander("✏️ Renombrar"):
            rename_input = st.text_input("Nuevo nombre:", value=st.session_state['current_course'], key="rename_input_sb")
            if st.button("Guardar Nombre"):
                if rename_input and rename_input != st.session_state['current_course']:
                    # Simple sanitize
                    safe_rename = "".join([c for c in rename_input if c.isalnum() or c in (' ', '-', '_')]).strip()
                    
                    # DB Update
                    from database import rename_course
                    c_id = st.session_state.get('current_course_id')
                    if c_id and rename_course(c_id, safe_rename):
                        st.session_state['current_course'] = safe_rename
                        st.success("Renombrado!")
                        st.rerun()
                    else:
                        st.error("Error al renombrar.")

        # DELETE
        
        # DELETE (Safe & Multi)
        with st.expander("🗑️ Borrar"):
            st.caption("Selecciona uno o varios diplomados para borrar.")
            
            # 1. Multi-Select (Exclude 'Crear Nuevo' logic implies just listing course names)
            # We already have course_names and course_map available from above scope
            
            courses_to_delete = st.multiselect(
                "Seleccionar Diplomados:", 
                options=course_names,
                format_func=lambda x: f"🗑️ {x}",
                key="multi_delete_select"
            )
            
            if courses_to_delete:
                st.write("")
                # 2. First Trigger Button
                if st.button("Solicitar Eliminación", type="primary", key="btn_req_del"):
                    st.session_state['delete_confirmation_pending'] = True
                
                # 3. Safety Confirmation (Only if requested)
                if st.session_state.get('delete_confirmation_pending'):
                    st.warning(f"⚠️ ¿Estás seguro? Vas a eliminar {len(courses_to_delete)} diplomado(s). Esta acción NO se puede deshacer.")
                    
                    col_confirm_a, col_confirm_b = st.columns(2)
                    with col_confirm_a:
                        if st.button("❌ Cancelar", key="btn_cancel_del"):
                            st.session_state['delete_confirmation_pending'] = False
                            st.rerun()
                    
                    with col_confirm_b:
                        if st.button("✅ SÍ, CONFIRMAR", type="primary", key="btn_confirm_del"):
                            from database import delete_course
                            success_count = 0
                            
                            for c_name in courses_to_delete:
                                c_id_del = course_map.get(c_name)
                                if c_id_del:
                                    if delete_course(c_id_del):
                                        success_count += 1
                            
                            if success_count > 0:
                                st.success(f"Se eliminaron {success_count} diplomados.")
                                st.session_state['delete_confirmation_pending'] = False
                                # Reset current course if it was deleted
                                if st.session_state.get('current_course') in courses_to_delete:
                                    st.session_state['current_course'] = None
                                st.rerun()
                            else:
                                st.error("No se pudo completar la eliminación.")
            else:
                # Reset confirmation if selection is cleared
                if st.session_state.get('delete_confirmation_pending'):
                    st.session_state['delete_confirmation_pending'] = False


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
            btnLeft.innerHTML = '◀';
            btnLeft.onclick = () => tabList.scrollBy({left: -200, behavior: 'smooth'});
            
            // Create Right Button
            const btnRight = doc.createElement('button');
            btnRight.id = 'tab-scroll-right';
            btnRight.innerHTML = '▶';
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
    "📹 Transcriptor", 
    "📝 Apuntes Simples", 
    "🗺️ Guía de Estudio", 
    "🧠 Ayudante Quiz",
    "📂 Biblioteca",
    "👩‍🏫 Ayudante de Tareas",
    "📚 Tutoría 1 a 1"
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
         st.info("⚠️ Configura tu API Key en la barra lateral para activar la Biblioteca IA.")

# --- TAB 1: Transcriptor ---
with tab1:
    # LAYOUT: Image Left (1) | Text Right (1.4)
    col_img, col_text = st.columns([1, 1.4], gap="large")
    
    with col_img:
        # Green Frame Placeholder
        # Image Display
        st.markdown('''
            <div class="green-frame" style="padding: 0; overflow: hidden;">
                <img src="data:image/jpeg;base64,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" style="
                    width: 100%; 
                    height: 100%; 
                    object-fit: cover; 
                    border-radius: 20px;
                ">
            </div>
        ''', unsafe_allow_html=True)

    with col_text:
        # Styled Title & Subtitle via HTML
        st.markdown('''
            <h2 class="transcriptor-title">1. Transcriptor de Videos</h2>
            <p class="transcriptor-subtitle">
                Sube los videos de tu unidad para procesarlos automáticamente.<br>
                <span style="font-size: 0.9rem; color: #888; font-weight: 500;">Arrastra tus archivos aquí</span>
            </p>
        ''', unsafe_allow_html=True)
        
        # File Uploader
        uploaded_files = st.file_uploader("Upload", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True, key="up1", label_visibility="collapsed")
        
        if uploaded_files:
            st.write("")
            if st.button("Iniciar Transcripción", key="btn1", use_container_width=True):
                # Validation
                c_id = st.session_state.get('current_course_id')
                if not c_id:
                    st.error("⚠️ Selecciona un Espacio de Trabajo en la barra lateral primero.")
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
                                def update_ui(msg, prog):
                                    pct = int(prog * 100)
                                    progress_bar.progress(prog)
                                    status_text.markdown(f"**{msg} ({pct}%)**")

                                txt_path = transcriber.process_video(temp_path, progress_callback=update_ui, chunk_length_sec=600)
                                
                                with open(txt_path, "r", encoding="utf-8") as f: 
                                    trans_text = f.read()
                                    
                                upload_file_to_db(t_unit_id, os.path.basename(txt_path), trans_text, "transcript")
                                st.success(f"✅ {file.name} guardado en Nube (Carpeta Transcripts)")
                                st.session_state['transcript_history'].append({"name": file.name, "text": trans_text})
                                
                                if os.path.exists(txt_path): os.remove(txt_path)
                                
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                if os.path.exists(temp_path): os.remove(temp_path)
                            
                            progress_bar.progress(1.0)
                        
                        status_text.success("¡Todo listo! (100%)")
                    else:
                        st.error("No se pudo crear carpeta de transcripts.")

        # History
        if st.session_state['transcript_history']:
            for i, item in enumerate(st.session_state['transcript_history']):
                st.divider()
                st.markdown(f"### 📄 Transcripción: {item['name']}")
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
                st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")
            
             if not transcript_files:
                st.info("No hay transcripciones. Sube videos en la Pestaña 1 (se creará carpeta 'Transcripts').")
             else:
                options = [f['name'] for f in transcript_files]
                file_map = {f['name']: f['id'] for f in transcript_files}
                
                selected_file = st.selectbox("Selecciona una transcripción:", options, key="sel2")
                
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
                        st.success("¡Apuntes generados en 3 capas!")

                # --- DISPLAY RESULTS ---
                if st.session_state['notes_result']:
                    res = st.session_state['notes_result']
                    
                    # Check if it's new dict format (Progressive) or old string (Legacy)
                    if isinstance(res, dict):
                        st.markdown("### 📝 Apuntes Progresivos")
                        
                        # LEVEL 1: Ultracorto
                        with st.expander("🟢 Nivel 1: Ultracorto (5 Puntos)", expanded=True):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('ultracorto', ''))
                            with c2:
                                if st.button("📄", key="copy_l1", help="Copiar Nivel 1"):
                                    copy_to_clipboard(res.get('ultracorto', ''))
                                    st.toast("Copiado Nivel 1")

                        # LEVEL 2: Intermedio
                        with st.expander("🟡 Nivel 2: Intermedio (Conceptos Clave)", expanded=False):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('intermedio', ''))
                            with c2:
                                if st.button("📄", key="copy_l2", help="Copiar Nivel 2"):
                                    copy_to_clipboard(res.get('intermedio', ''))
                                    st.toast("Copiado Nivel 2")

                        # LEVEL 3: Profundo
                        with st.expander("🔴 Nivel 3: Profundidad (Explicación Completa)", expanded=False):
                            c1, c2 = st.columns([0.9, 0.1])
                            with c1: st.markdown(res.get('profundo', ''))
                            with c2:
                                 if st.button("📄", key="copy_l3", help="Copiar Nivel 3"):
                                    copy_to_clipboard(res.get('profundo', ''))
                                    st.toast("Copiado Nivel 3")
                                    
                    else:
                        # Legacy String Display
                        st.markdown(res)
                        if st.button("Copiar Apuntes", key="copy_notes_btn"):
                             copy_to_clipboard(res)
                             st.toast("Copiado")

# --- TAB 3: Guía de Estudio ---
with tab3:
    col_img, col_text = st.columns([1, 1.5], gap="large") # Swapped to Image Left
    
    with col_img:
        render_image_card("illustration_guide_1765052821852.png")
    
    with col_text:
        tab3_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">3. Guía de Estudio Estratégica</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">Crea mapas, resúmenes y preguntas de examen.</p>'
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
                st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")

            if not transcript_files:
                 st.info("Primero sube videos en la Pestaña 1.")
            else:
                options_guide = [f['name'] for f in transcript_files]
                file_map_guide = {f['name']: f['id'] for f in transcript_files}
                
                selected_guide_file = st.selectbox("Archivo base:", options_guide, key="sel3")
                
                if selected_guide_file and st.button("Generar Guía", key="btn3"):
                    # Get content from DB
                    f_id = file_map_guide[selected_guide_file]
                    text = get_file_content(f_id)
                        
                    with st.spinner("Diseñando estrategia de estudio..."):
                        guide = assistant.generate_study_guide(text, global_context=gl_ctx)
                        
                        # Save to "Guides" Unit in DB
                        g_unit = next((u for u in units if u['name'] == "Guides"), None)
                        if not g_unit:
                             g_unit = create_unit(c_id, "Guides")
                        
                        if g_unit:
                             base_name = selected_guide_file.replace("_transcripcion.txt", "")
                             fname = f"Guia_{base_name}.txt"
                             upload_file_to_db(g_unit['id'], fname, guide, "guide")
                             st.success(f"Guía guardada en 'Guides'/{fname}")

                        st.success("¡Guía lista!")
                        st.session_state['guide_result'] = guide # Save to session
            
            # --- PERSISTENT RESULTS DISPLAY ---
            if st.session_state['guide_result']:
                st.divider()
                
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown("### 🗺️ Tu Guía de Estudio")
                with c_copy:
                    if st.button("📄", key="cp_guide", help="Copiar Guía Limpia"):
                        clean_txt = clean_markdown(st.session_state['guide_result'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("¡Copiado!", icon='📋')
                
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
            '<p style="color: #64748b; font-size: 1.1rem;">Modo Ráfaga: Sube múltiples preguntas y obtén las respuestas.</p>'
            '</div>'
        )
        st.markdown(tab4_html, unsafe_allow_html=True)
        
        # Check Global Memory
        gl_ctx, gl_count = get_global_context()
        if gl_count > 0:
            st.success(f"✅ **Memoria Global Activa:** Usando {gl_count} archivos para mayor precisión.")
        
        # RESET BUTTON
        col_up, col_reset = st.columns([0.9, 0.1])
        with col_reset:
             # Use the same 'copy-btn' style or just a clean emoji button
             if st.button("🗑️", key="reset_quiz", help="Borrar todo para empezar de cero"):
                 st.session_state['quiz_results'] = []
                 st.session_state['pasted_images'] = []
                 st.session_state['quiz_key'] += 1
                 st.rerun()
                 
        with col_up:
            # Clipboard Paste Button
            if st.button("📋 Pegar Imagen (Portapapeles)", key="paste_btn", help="Haz Ctrl+V en tu PC, luego click aquí para cargar la imagen."):
                try:
                    img = ImageGrab.grabclipboard()
                    if isinstance(img, Image.Image):
                        # Convert to RGB to avoid alpha issues
                        if img.mode == 'RGBA': img = img.convert('RGB')
                        st.session_state['pasted_images'].append(img)
                        st.toast("Imagen pegada con éxito!", icon='📸')
                    else:
                        st.warning("No hay imagen en el portapapeles. (Haz PrtScrn o Copiar Imagen primero)")
                except Exception as e:
                    st.error(f"Error pegando: {e}")

            # Show Pasted Thumbnails
            if st.session_state['pasted_images']:
                st.caption(f"📸 {len(st.session_state['pasted_images'])} capturas pegadas:")
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
            status.success("¡Análisis Terminado! (100%)")
            st.session_state['quiz_results'] = results # Save results

        # --- PERSISTENT RESULTS DISPLAY ---
        if st.session_state['quiz_results']:
            st.divider()
            
            # HEADER + COPY ICON
            c_head, c_copy = st.columns([0.9, 0.1])
            with c_head:
                st.markdown("### 📋 Resultados de Quiz")
            with c_copy:
                # Compile text for copying inside the button action
                full_report_copy = "--- HOJA DE RESPUESTAS ---\n\n"
                for i, res in enumerate(st.session_state['quiz_results']):
                     full_report_copy += f"FOTO {i+1}: {res['short']}\n"
                full_report_copy += "\n--- DETALLES ---\n"
                for i, res in enumerate(st.session_state['quiz_results']):
                     full_report_copy += f"\n[FOTO {i+1}]\n{res['full']}\n"
                     
                if st.button("📄", key="cp_quiz", help="Copiar Resultados Limpios"):
                    clean_txt = clean_markdown(full_report_copy)
                    if copy_to_clipboard(clean_txt):
                        st.toast("¡Copiado!", icon='📋')
            
            # --- RESULTS DISPLAY ---
            # Visual Display (Markdown instead of Code Block)
            st.markdown("#### 📝 Hoja de Respuestas Rápida")
            
            # Build a nice markdown list for visual display
            md_list = ""
            for i, res in enumerate(st.session_state['quiz_results']):
                md_list += f"- **Foto {i+1}:** {res['short']}\n"
            st.markdown(md_list)
            
            st.divider()
            st.markdown("#### 🔍 Detalles por Pregunta")
            
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
        '<p style="color: #64748b; font-size: 1.1rem;">Tu "Segundo Cerebro": Guarda conocimientos y úsalos para resolver tareas.</p>'
        '</div>'
    )
    st.markdown(tab5_html, unsafe_allow_html=True)
    
    # --- LAYOUT REFOCUSED ON TASK SOLVER ---
    col_task = st.container()
    
    st.info("💡 Gestiona tus archivos, sube documentos y organiza carpetas en la nueva pestaña '📂 Biblioteca'.")

    # --- RIGHT COLUMN: HOMEWORK SOLVER (Now Main) ---
    with col_task:
        c_title, c_trash = st.columns([0.85, 0.15])
        with c_title:
            st.markdown("### 🧠 Ayudante Inteligente")
            st.caption("Resuelve tareas usando SOLO la información de tu biblioteca.")
        with c_trash:
            if st.button("🗑️", key="clear_hw_btn", help="Borrar tarea y empezar de cero"):
                st.session_state['homework_result'] = None
                st.rerun()
        
        # MODE TOGGLE
        arg_mode = st.toggle("🧠 Activar Modo Argumentador (Abogado del Diablo)", key="arg_mode_toggle", help="Activa un análisis profundo con 4 dimensiones: Respuesta, Fuentes, Paso a Paso y Contra-argumento.")
        
        # 1. Select Context
        st.markdown("**1. ¿Qué conocimientos uso?** (Selección por Unidad)")
        
        # DB Logic for Context Selection
        from database import get_units, get_unit_context
        
        current_course_id = st.session_state.get('current_course_id')
        db_units = get_units(current_course_id) if current_course_id else []
        
        # Find Global Unit
        global_unit = next((u for u in db_units if u['name'] == "00_Memoria_Global"), None)
        has_global = global_unit is not None
        
        if has_global:
            st.success(f"✅ **Memoria Global Activa** (Temarios/Reglas).")
            
        st.caption("ℹ️ Además de la Memoria Global, selecciona las unidades específicas para esta tarea:")
        
        # Filter available units (excluding Global)
        available_units_objs = [u for u in db_units if u['name'] != "00_Memoria_Global"]
        available_unit_names = [u['name'] for u in available_units_objs]
        unit_map = {u['name']: u['id'] for u in available_units_objs}
        
        selected_units = st.multiselect("Unidades Específicas:", available_unit_names, placeholder="Ej: Unidad 1...")
        
        # 2. Input Task
        st.markdown("**2. Tu Tarea:**")
        task_prompt = st.text_area("Describe la tarea o pega la consigna:", height=100, placeholder="Ej: Crea un perfil de cliente ideal usando el método de la Unidad 1...")
        
        # ATTACHMENT UPLOADER
        task_file = st.file_uploader("Adjuntar consigna (PDF, Imagen, TXT)", type=['pdf', 'png', 'jpg', 'jpeg', 'txt'])
        
        btn_label = "⚔️ Debatir y Solucionar" if arg_mode else "🚀 Resolver Tarea"
        
        if st.button(btn_label, key="solve_task", use_container_width=True):
            if not task_prompt and not task_file:
                st.warning("⚠️ Escribe la tarea o sube un archivo.")
            else:
                # Gather context
                gathered_texts = []
                
                # CHECK IF RUNNING ON EMPTY LIBRARY
                using_general_knowledge = False
                if not selected_units and not has_global:
                    using_general_knowledge = True
                    st.toast("⚠️ Sin biblioteca seleccionada. Usando Conocimiento General de Gemini.", icon="🌐")
                
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
                 st.markdown("### 🛡️ Análisis del Consultor (Modo Argumentador)")
                 
                 # Tabs for Output
                 t_resp, t_src, t_steps = st.tabs(["💡 Respuesta", "📚 Fuentes", "👣 Paso a Paso"])
                 
                 with t_resp:
                     st.markdown(res.get('direct_response', ''))
                     if st.button("📄 Copiar Respuesta", key="cp_arg_resp"):
                         copy_to_clipboard(res.get('direct_response', ''))
                         st.toast("Copiada Respuesta")
                         
                 with t_src:
                     st.markdown(res.get('sources', 'No se citaron fuentes específicas.'))
                     
                 with t_steps:
                     st.markdown(res.get('step_by_step', ''))
                     
                 # Counter Argument (Hidden)
                 with st.expander("🧨 Ver Contra-Argumento (Abogado del Diablo)"):
                     st.warning("⚠️ Estas son las objeciones que un profesor estricto te haría:")
                     st.markdown(res.get('counter_argument', ''))
                     
            else:
                # LEGACY DISPLAY (String)
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown("### ✅ Respuesta")
                with c_copy:
                     if st.button("📄", key="cp_hw", help="Copiar Respuesta"):
                        clean_txt = clean_markdown(res)
                        if copy_to_clipboard(clean_txt):
                            st.toast("¡Copiado!", icon='📋')
                
                st.markdown(res)

            # --- BRIDGE TO TUTOR ---
            st.divider()
            if st.button("🗣️ Debatir esta respuesta con el Profesor (Ir a Tutoría)", key="btn_bridge_tutor", help="Envía esta tarea y respuesta al chat de Tutoría para discutirla."):
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
                    f"Quiero que analicemos esto. Qué opinas? Podemos mejorarlo?"
                )
                
                # Check if history exists
                if 'tutor_chat_history' not in st.session_state:
                    st.session_state['tutor_chat_history'] = []
                
                # Append Bridge Message as USER
                st.session_state['tutor_chat_history'].append({"role": "user", "content": bridge_msg})
                
                # AUTO-REPLY LOGIC: Trigger response immediately so it's ready when user switches tabs
                # Prepare Context (Global)
                gl_ctx_bridge, _ = get_global_context()
                
                with st.spinner("El profesor está analizando tu respuesta..."):
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
                        
                        st.success("✅ ¡Información enviada y el Profesor YA TE RESPONDIÓ!")
                        st.info("👈 Ve ahora a la pestaña '📚 Tutoría 1 a 1' para ver su corrección.")
                        
                    except Exception as e:
                        st.error(f"Error generando respuesta automática del tutor: {e}")

# --- TAB 6: Tutoría 1 a 1 (Docente Artificial) ---
if 'tutor_chat_history' not in st.session_state: st.session_state['tutor_chat_history'] = []

with tab6:
    tutor_html = (
        '<div class="card-text">'
        '<h2 style="margin-top:0;">6. Tutoría Personalizada (Profesor IA)</h2>'
        '<p style="color: #64748b; font-size: 1.1rem;">Tu profesor particular. Pregunta, sube tareas para corregir y dialoga en tiempo real.</p>'
        '</div>'
    )
    st.markdown(tutor_html, unsafe_allow_html=True)
    
    col_chat, col_info = st.columns([2, 1], gap="large")
    
    with col_info:
        st.info("ℹ️ **Memoria Activa:** El profesor recuerda vuestra conversación y tiene acceso total a la Biblioteca Global.")
        st.divider()
        st.markdown("### 📎 Adjunto Rápido")
        tutor_file = st.file_uploader("Subir archivo al chat", type=['pdf', 'txt', 'png', 'jpg'], key="tutor_up")
        
        if st.button("🗑️ Borrar Historial", key="clear_chat"):
            st.session_state['tutor_chat_history'] = []
            st.rerun()

    with col_chat:
        # Display Chat History
        for msg in st.session_state['tutor_chat_history']:
            with st.chat_message(msg['role']):
                st.markdown(msg['content'])
        
        # User Input
        if prompt := st.chat_input("¿En qué puedo ayudarte hoy, alumno?"):
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
                    st.toast(f"📎 Archivo {tutor_file.name} enviado al profesor.")
                except Exception as e:
                    st.error(f"Error leyendo archivo: {e}")

            # 3. Generate Response
            with st.chat_message("assistant"):
                with st.spinner("El profesor está escribiendo..."):
                    response = assistant.chat_tutor(
                        prompt, 
                        chat_history=st.session_state['tutor_chat_history'], 
                        context_files=chat_files, 
                        global_context=gl_ctx
                    )
                    st.markdown(response)
            
            # 4. Save Response
            st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response})
