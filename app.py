
import streamlit as st
import os
import glob
from transcriber import Transcriber
from study_assistant import StudyAssistant
from PIL import Image, ImageGrab
import shutil
import time

# --- PAGE CONFIG MUST BE FIRST ---
st.set_page_config(page_title="Estudian2", page_icon="🎓", layout="wide")

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
/* HIDE STREAMLIT STATUS WIDGET (Running man) */
div[data-testid="stStatusWidget"] {
    visibility: hidden;
}
div[data-testid="stDecoration"] {
    visibility: hidden;
}
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

    /* --- GLOBAL VARIABLES & BODY --- */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1a202c;
        background-color: #f3e8ff; /* Fallback */
    }

    /* 1. LILAC APP BACKGROUND (The Bottom Layer) */
    .stApp {
        background-color: #f3e8ff;
        background-image: radial-gradient(#d8b4fe 1.5px, transparent 1.5px);
        background-size: 24px 24px;
        /* Padding to allow the card to 'float' inside */
        padding: 20px;
    }
    
    /* 2. THE FLOATING WHITE CARD (The Top Layer) */
    /* We target the main block container */
    .block-container {
        background-color: #ffffff;
        padding: 3rem 5rem !important; /* Spacious padding */
        border-radius: 40px;
        box-shadow: 0 20px 60px -10px rgba(109, 40, 217, 0.15); /* Deep purple shadow */
        margin-top: 40px;
        max-width: 1200px;
    }

    /* --- TYPOGRAPHY --- */
    /* --- TYPOGRAPHY --- */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Outfit', sans-serif;
        color: #5b21b6 !important; /* General Purple */
        letter-spacing: -0.5px;
    }
    
    h1, .stMarkdown h1 {
        color: #7c3aed !important; /* Vibrant Violet for Logo/Main Title */
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    h2, .stMarkdown h2 {
        color: #6d28d9 !important; /* Deep Purple for Section Headers */
        font-weight: 700;
    }

    /* --- BUTTONS --- */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        color: white !important;
        border: none;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        padding: 0.75rem 2.5rem;
        border-radius: 50px;
        box-shadow: 0 10px 25px -5px rgba(124, 58, 237, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px -5px rgba(124, 58, 237, 0.5);
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f5f3ff;
        padding: 10px;
        border-radius: 50px;
        gap: 10px;
        margin-bottom: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #7c3aed;
        border-radius: 40px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        padding: 8px 24px;
        height: auto;
    }

    .stTabs [aria-selected="true"] {
        background-color: #8b5cf6 !important; /* VIOLET ACTIVE */
        color: #ffffff !important; /* WHITE TEXT */
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
    }
    
    /* Remove default underline */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    /* --- INPUTS & SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #f3e8ff;
    }
    
    .stTextInput > div > div > input {
        border-radius: 15px;
        background-color: #faf5ff;
        border: 1px solid #e9d5ff;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] section {
        background-color: #fbf7ff;
        border: 2px dashed #d8b4fe;
        border-radius: 20px;
    }
    
    /* Remove individual card backgrounds since we are in a main card */
    .card-text { 
        padding: 10px 0; 
    }
    
    img {
        border-radius: 20px;
    }
    
    /* Custom Button Styling (Transparent Icon Button) */
    div.stButton > button.copy-btn {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #7c3aed !important;
        font-size: 1.5rem !important;
        padding: 0 !important;
    }
    
    /* SIDEBAR BUTTONS - SUBTLE STYLE */
    [data-testid="stSidebar"] .stButton > button {
        background: #ffffff !important;
        border: 1px solid #d8b4fe !important;
        color: #7c3aed !important;
        box-shadow: none !important;
        padding: 0.5rem 1.5rem !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #faf5ff !important;
        border-color: #8b5cf6 !important;
        transform: translateY(-1px);
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # --- USER PROFILE ---
    if st.session_state.get('user'):
        st.markdown(f"👤 **{st.session_state['user'].email}**")
        if st.button("Cerrar Sesión", key="logout_btn", use_container_width=True):
            st.session_state['user'] = None
            if 'supabase_session' in st.session_state:
                del st.session_state['supabase_session']
            st.rerun()
        st.divider()

    # --- SPOTLIGHT SEARCH (Universal) ---
    st.markdown("### 🔍 Spotlight Académico")
    search_query = st.text_input("¿Qué buscas hoy?", placeholder="Ej: 'Concepto de Lead' o 'Relación entre X y Y'")
    search_mode = st.radio("Modo:", ["⚡ Concepto Rápido", "🕵️ Análisis Profundo"], horizontal=True, label_visibility="collapsed")
    
    if st.button("Buscar 🔍", key="btn_spotlight"):
        if search_query:
            st.session_state['spotlight_query'] = search_query
            st.session_state['spotlight_mode'] = search_mode
            st.rerun()
        else:
            st.warning("Escribe algo para buscar.")
    
    st.divider()

    st.header("⚙️ Configuración Personal")
    
    # Check if system key exists (for info only, do not show it)
    has_system_key = False
    try:
        if "GOOGLE_API_KEY" in st.secrets: has_system_key = True
    except: pass
    
    if has_system_key:
        st.info("✅ Clave del Sistema Activa")
    else:
        st.warning("⚠️ Sin Clave del Sistema")
        
    user_key_input = st.text_input("Tu Clave API (Opcional)", type="password", help="Sobrescribe la clave del sistema para esta sesión.")
    
    if user_key_input:
        st.session_state['custom_api_key'] = user_key_input
        st.success("✅ Usando tu Clave Personal")
    else:
        # If user clears input, revert to system
        if 'custom_api_key' in st.session_state:
            del st.session_state['custom_api_key']
        
    st.divider()
    
    # --- COURSE SELECTOR (WORKSPACES) ---
    # --- COURSE SELECTOR (WORKSPACES) ---
    st.header("📂 Espacio de Trabajo")
    
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
    options = course_names + ["➕ Crear Nuevo..."]
    index = course_names.index(st.session_state['current_course']) if st.session_state['current_course'] in course_names else 0
    
    selected_option = st.selectbox("Diplomado Actual:", options, index=index)
    
    if selected_option == "➕ Crear Nuevo...":
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
    if st.session_state['current_course'] != "➕ Crear Nuevo...":
        with st.expander("✏️ Renombrar Diplomado"):
            rename_input = st.text_input("Nuevo nombre:", value=st.session_state['current_course'], key="rename_input")
            if st.button("Confirmar Cambio"):
                if rename_input and rename_input != st.session_state['current_course']:
                    safe_rename = "".join([c for c in rename_input if c.isalnum() or c in (' ', '-', '_')]).strip()
                    src = os.path.join(CORE_OUTPUT_ROOT, st.session_state['current_course'])
                    dst = os.path.join(CORE_OUTPUT_ROOT, safe_rename)
                    
                    if os.path.exists(dst):
                        st.error("¡Ese nombre ya existe!")
                    else:
                        try:
                            # Close any potentially open handles by relying on OS, simply rename
                            os.rename(src, dst)
                            st.session_state['current_course'] = safe_rename
                            st.success("¡Renombrado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al renombrar: {e}")

    # DELETE OPTION
    with st.expander("🗑️ Borrar Diplomados"):
        # Filter out "Crear Nuevo" if present or just use db_courses list
        del_options = [c['name'] for c in db_courses]
        courses_to_del = st.multiselect("Selecciona para borrar:", del_options, key="del_courses_sel")
        
        if st.button("Eliminar Seleccionados", key="btn_del_courses"):
            if courses_to_del:
                from database import delete_course
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
                    st.success(f"¡{deleted_count} diplomados eliminados!")
                    # Clear session if current was deleted
                    if st.session_state.get('current_course') in courses_to_del:
                         st.session_state['current_course'] = None
                         st.session_state['current_course_id'] = None
                    time.sleep(1)
                    st.rerun()

    st.caption(f"Guardando en: `output/{st.session_state['current_course']}/...`")
    st.divider()
    
    # Custom Lilac Info Box
    sidebar_html = '''
    <div style="background-color: #f3e8ff; padding: 15px; border-radius: 12px; border: 1px solid #d8b4fe; color: #6d28d9; font-size: 0.9rem;">
        <strong style="display: block; margin-bottom: 8px; display: flex; align-items: center; gap: 5px;">
            📂 Carpetas de Salida:
        </strong>
        <ul style="margin: 0; padding-left: 20px; list-style-type: circle;">
            <li style="margin-bottom: 3px;">transcripts</li>
            <li style="margin-bottom: 3px;">notes</li>
            <li>guides</li>
        </ul>
    </div>
    '''
    st.markdown(sidebar_html, unsafe_allow_html=True)
    
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📹 Transcriptor", 
    "📝 Apuntes Simples", 
    "🗺️ Guía de Estudio", 
    "🧠 Ayudante Quiz",
    "👩‍🏫 Ayudante de Tareas",
    "📚 Tutoría 1 a 1"
])

# --- Helper for ECharts Visualization ---


# --- Helper for styled image container ---
def render_image_card(img_path):
    import base64
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode()
        
        card_html = f'''
        <div style="
            background-color: #f3e8ff;
            border-radius: 20px;
            padding: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        ">
            <img src="data:image/png;base64,{b64_img}" style="
                width: 100%; 
                max-width: 400px;
                height: auto; 
                filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
            ">
        </div>
        '''
        st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.error(f"Image not found: {img_path}")

# --- TAB 1: Transcriptor ---
with tab1:
    # LAYOUT: Image Left (1) | Text Right (1.5)
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
        render_image_card("illustration_transcriber_1765052797646.png")

    with col_text:
        tab1_html = '''
        <div class="card-text">
            <h2 style="margin-top:0;">1. Transcriptor de Videos</h2>
            <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 20px;">
                Sube los videos de tu unidad para procesarlos automáticamente.
            </p>
        </div>
        '''
        st.markdown(tab1_html, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("Arrastra tus archivos aquí", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True, key="up1")
        
        if uploaded_files:
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
                                
                                st.success(f"✅ {file.name} guardado en Nube (Carpeta Transcripts)")
                                
                                # Store in session state for immediate display
                                st.session_state['transcript_history'].append({"name": file.name, "text": trans_text})
                                
                                # Cleanup local temp files
                                if os.path.exists(txt_path): os.remove(txt_path)
                                
                            except Exception as e:
                                st.error(f"Error: {e}")
                            finally:
                                if os.path.exists(temp_path): os.remove(temp_path)
                            
                            progress_bar.progress(1.0)
                        
                        status_text.success("¡Todo listo! (100%)")
                    else:
                        st.error("No se pudo crear carpeta de transcripts.")

        # --- PERSISTENT RESULTS DISPLAY (Outside button block) ---
        if st.session_state['transcript_history']:
            for i, item in enumerate(st.session_state['transcript_history']):
                st.divider()
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown(f"### 📄 Transcripción: {item['name']}")
                with c_copy:
                    if st.button("📄", key=f"cp_t_{i}", help="Copiar Texto Limpio"):
                        clean_txt = clean_markdown(item['text'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("¡Copiado!", icon='📋')
                st.markdown(item['text'])

# --- TAB 2: Apuntes Simples ---
with tab2:
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
         render_image_card("illustration_notes_1765052810428.png")
         
    with col_text:
        tab2_html = '''
        <div class="card-text">
            <h2 style="margin-top:0;">2. Generador de Apuntes</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Convierte transcripciones en apuntes claros y concisos.</p>
        </div>
        '''
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
        tab3_html = '''
        <div class="card-text">
            <h2 style="margin-top:0;">3. Guía de Estudio Estratégica</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Crea mapas, resúmenes y preguntas de examen.</p>
        </div>
        '''
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
        tab4_html = '''
        <div class="card-text">
            <h2 style="margin-top:0;">4. Ayudante de Pruebas</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Modo Ráfaga: Sube múltiples preguntas y obtén las respuestas.</p>
        </div>
        '''
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
    tab5_html = '''
    <div class="card-text">
        <h2 style="margin-top:0;">5. Ayudante de Tareas & Biblioteca</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Tu "Segundo Cerebro": Guarda conocimientos y úsalos para resolver tareas.</p>
    </div>
    '''
    st.markdown(tab5_html, unsafe_allow_html=True)
    
    col_lib, col_task = st.columns([1, 1], gap="large")
    
    # --- LEFT COLUMN: LIBRARY MANAGER ---
    with col_lib:
        st.markdown("### 📚 Biblioteca del Diplomado")
        st.caption("Organiza aquí la 'Verdad Absoluta' del curso.")
        
        with st.expander("➕ Alimentar Memoria (Subir Contenido)", expanded=True):
            st.markdown("##### 1. Destino")
            is_global = st.checkbox("📌 Es Información Global (Temario, Reglas, Formatos)", help="Si marcas esto, estos archivos se usarán SIEMPRE en todas las tareas, sin que tengas que seleccionarlos.", value=False)
            
            unit_name = ""
            topic_name = ""
        # --- BULK IMPORT (CHAT RESCUE) ---
        with st.expander("📥 Importar Historial de Chat (Rescatar Datos)", expanded=False):
            st.caption("Sube un archivo .txt con todo tu historial de ChatGPT desordenado. La IA lo organizará por temas.")
            chat_file = st.file_uploader("Subir Log de Chat (.txt)", type=['txt'], key="bulk_chat_upl")
            
            if chat_file and st.button("🧩 Procesar y Organizar", key="proc_bulk"):
                raw_text = chat_file.getvalue().decode("utf-8", errors='ignore')
                with st.spinner("⏳ Leyendo tu historial masivo y organizando temas... (Esto puede tardar un poco)"):
                    structured_data = assistant.process_bulk_chat(raw_text)
                    st.session_state['bulk_import_data'] = structured_data
            
            # Review and Save
            if 'bulk_import_data' in st.session_state and st.session_state['bulk_import_data']:
                st.divider()
                st.markdown("#### 🧐 Vista Previa de Temas Detectados")
                
                # Fetch available units from DB
                from database import get_units, create_unit, upload_file_to_db
                
                current_course_id = st.session_state.get('current_course_id')
                db_units = get_units(current_course_id) if current_course_id else []
                existing_folders = [u['name'] for u in db_units]
                
                # Default "Rescate" if exists, otherwise first one
                default_idx = 0
                if "01_Rescate_Importado" in existing_folders:
                     default_idx = existing_folders.index("01_Rescate_Importado")
                
                target_option = st.selectbox(
                    "¿Dónde guardamos estos archivos?", 
                    options=existing_folders + ["✨ Nueva Carpeta..."],
                    index=default_idx if existing_folders else 0
                )
                
                new_folder_name = "01_Rescate_Importado"
                if target_option == "✨ Nueva Carpeta...":
                    new_folder_name = st.text_input("Nombre de la Nueva Carpeta:", value="01_Rescate_Importado")
                else:
                    new_folder_name = target_option
                
                valid_items = [item for item in st.session_state['bulk_import_data'] if 'title' in item and 'content' in item]
                
                for idx, item in enumerate(valid_items):
                    with st.expander(f"📄 {item['title']}"):
                        st.markdown(item['content'][:500] + "...")
                
                if st.button(f"💾 Guardar {len(valid_items)} Archivos en Biblioteca", key="save_bulk_all"):
                    if not current_course_id:
                        st.error("Selecciona un curso primero.")
                    else:
                        # Create Unit if needed
                        target_unit_id = None
                        if target_option == "✨ Nueva Carpeta...":
                             u_res = create_unit(current_course_id, new_folder_name)
                             if u_res: target_unit_id = u_res['id']
                        else:
                             # Find ID
                             found = next((u for u in db_units if u['name'] == target_option), None)
                             if found: target_unit_id = found['id']
                        
                        if target_unit_id:
                            saved_count = 0
                            progress_bar = st.progress(0)
                            for idx, item in enumerate(valid_items):
                                # Sanitize filename
                                safe_title = "".join([c if c.isalnum() else "_" for c in item['title']])
                                fname = f"{safe_title}.md"
                                upload_file_to_db(target_unit_id, fname, item['content'], "text")
                                saved_count += 1
                                progress_bar.progress((idx + 1) / len(valid_items))
                            
                            st.success(f"✅ ¡{saved_count} temas rescatados y guardados en '{new_folder_name}'!")
                            st.session_state['bulk_import_data'] = None # Clear after save
                            import time
                            time.sleep(1)
                            st.rerun()
                        else:
                             st.error("No se pudo obtener la carpeta destino.")

        # Show existing library
        st.markdown(f"##### 📂 Contenido Guardado ({st.session_state.get('current_course', 'Sin Curso')}):")
        
        current_course_id = st.session_state.get('current_course_id')
        if current_course_id:
            from database import get_units, delete_unit, rename_unit, get_files, delete_file, rename_file, get_file_content
            
            db_units = get_units(current_course_id)
            
            if not db_units:
                st.info("📭 La biblioteca está vacía. Sube archivos arriba.")
                
                # DEBUG: Help user troubleshoot why it's empty
                with st.expander("🕵️ Debug: ¿Por qué no veo mis archivos?"):
                    user = st.session_state.get('user')
                    uid = user.id if user else "No User"
                    st.write(f"User ID: `{uid}`")
                    st.write(f"Course ID: `{current_course_id}`")
                    if st.button("🔄 Forzar Recarga"):
                        st.rerun()
            
            for unit in db_units:
                u_id = unit['id']
                u_name = unit['name']
                
                # Icon logic
                icon = "🧠" if u_name == "00_Memoria_Global" else "📁"
                label = "Memoria GLOBAL (Siempre activa)" if u_name == "00_Memoria_Global" else u_name
                
                with st.expander(f"{icon} {label}"):
                    # --- UNIT MANAGEMENT ---
                    if u_name != "00_Memoria_Global":
                        col_u_ren, col_u_act = st.columns([0.8, 0.2])
                        with col_u_ren:
                            # Rename Unit Interface
                            if f"ren_u_{u_id}" in st.session_state:
                                new_u_name = st.text_input("Nuevo nombre carpeta:", value=u_name, key=f"in_u_{u_id}")
                                if st.button("Guardar Nombre", key=f"save_u_{u_id}"):
                                    if new_u_name and new_u_name != u_name:
                                        if rename_unit(u_id, new_u_name):
                                            del st.session_state[f"ren_u_{u_id}"]
                                            st.success("Carpeta renombrada!")
                                            time.sleep(0.5)
                                            st.rerun()
                                        else:
                                            st.error("Error al renombrar.")
                            else:
                                st.caption(f"Carpeta: {u_name}")
                        with col_u_act:
                            if f"ren_u_{u_id}" not in st.session_state:
                                c_u_ren, c_u_del = st.columns([1, 1])
                                with c_u_ren:
                                    if st.button("✏️", key=f"btn_ren_u_{u_id}", help="Renombrar Carpeta"):
                                        st.session_state[f"ren_u_{u_id}"] = True
                                        st.rerun()
                                with c_u_del:
                                    # Confirm Delete Logic
                                    if f"conf_del_u_{u_id}" not in st.session_state:
                                        if st.button("🗑️", key=f"btn_del_u_{u_id}", help="Borrar Carpeta Completa"):
                                            st.session_state[f"conf_del_u_{u_id}"] = True
                                            st.rerun()
                                    else:
                                        if st.button("🔥", key=f"confirm_del_u_{u_id}", help="¿Seguro? ¡Se borrará todo!"):
                                            if delete_unit(u_id):
                                                del st.session_state[f"conf_del_u_{u_id}"]
                                                st.rerun()
                                            else:
                                                st.error("Error borrando unidad.")
                                        st.caption("¿Confirmar?")

                    # --- FILE MANAGEMENT ---
                    files = get_files(u_id)
                    if not files: st.caption("Vacío")
                    
                    for f in files:
                        f_id = f['id']
                        f_name = f['name']
                        
                        # Single Row Layout: [Icon(5%) Name(65%) View(10%) Edit(10%) Del(10%)]
                        c_icon, c_name, c_view, c_edit, c_del = st.columns([0.05, 0.65, 0.1, 0.1, 0.1], vertical_alignment="center")
                        
                        with c_icon:
                            st.markdown("📄")
                            
                        with c_name:
                            # Rename File Interface
                            if f"ren_f_{f_id}" in st.session_state:
                                new_f_name = st.text_input("Renombrar:", value=f_name, key=f"in_f_{f_id}", label_visibility="collapsed")
                                if st.button("💾", key=f"save_f_{f_id}", help="Guardar nombre"):
                                    if new_f_name and new_f_name != f_name:
                                        if rename_file(f_id, new_f_name):
                                            del st.session_state[f"ren_f_{f_id}"]
                                            st.rerun()
                                        else:
                                            st.error("Error renovando archivo.")
                            else:
                                st.markdown(f"{f_name}")
                        
                        if f"ren_f_{f_id}" not in st.session_state:
                            with c_view:
                                # Toggle View
                                view_key = f"view_f_{f_id}"
                                icon_view = "👁️" if not st.session_state.get(view_key, False) else "🙈"
                                if st.button(icon_view, key=f"btn_view_{f_id}", help="Ver/Ocultar contenido"):
                                    st.session_state[view_key] = not st.session_state.get(view_key, False)
                                    st.rerun()
                                    
                            with c_edit:
                                if st.button("✏️", key=f"edit_{f_id}", help="Renombrar archivo"):
                                    st.session_state[f"ren_f_{f_id}"] = True
                                    st.rerun()
                            with c_del:
                                if st.button("🗑️", key=f"del_{f_id}", help="Borrar archivo permanente"):
                                    if delete_file(f_id):
                                        st.rerun()
                                    else:
                                        st.error("Error borrando archivo.")
                        else:
                            # Cancel button when renaming
                            with c_view:
                                if st.button("❌", key=f"cancel_{f_id}", help="Cancelar"):
                                    del st.session_state[f"ren_f_{f_id}"]
                                    st.rerun()
                        
                        # CONTENT VIEWER
                        if st.session_state.get(f"view_f_{f_id}", False):
                            content_view = get_file_content(f_id)
                            st.info(f"📜 Contenido de: {f_name}")
                            st.code(content_view, language="markdown")
                            if st.button("Cerrar Visualización", key=f"close_{f_id}"):
                                st.session_state[f"view_f_{f_id}"] = False
                                st.rerun()
    
    # --- RIGHT COLUMN: HOMEWORK SOLVER ---
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
                
                bridge_msg = f'''
                Hola Profe IA. Acabo de generar una respuesta para esta tarea:
                
                **CONSIGNA:**
                _{task_prompt}_
                
                **MI BORRADOR (Generado por Asistente):**
                {full_text_response}
                
                Quiero que analicemos esto. Qué opinas? Podemos mejorarlo?
                '''
                
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
    tutor_html = '''
    <div class="card-text">
        <h2 style="margin-top:0;">6. Tutoría Personalizada (Profesor IA)</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Tu profesor particular. Pregunta, sube tareas para corregir y dialoga en tiempo real.</p>
    </div>
    '''
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
