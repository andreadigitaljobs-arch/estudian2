
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

def delete_files_ui(folder_path, key_prefix):
    """Render a multi-select UI to delete files from a folder."""
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    if not files:
        st.caption("No hay archivos para borrar.")
        return

    with st.expander("🗑️ Gestionar / Borrar Archivos"):
        to_delete = st.multiselect("Selecciona archivos para ELIMINAR permanentemente:", files, key=f"del_{key_prefix}")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if to_delete:
                if st.button(f"🗑️ Eliminar Selección ({len(to_delete)})", key=f"btn_del_{key_prefix}"):
                    for file in to_delete:
                        try:
                            os.remove(os.path.join(folder_path, file))
                        except Exception as e:
                            st.error(f"Error borrando {file}: {e}")
                    st.success("Archivos eliminados.")
                    st.rerun()
        with c2:
            if st.button("🔥 Borrar TODO", key=f"btn_del_all_{key_prefix}", help="Borra TODOS los archivos de la lista"):
                 for file in files:
                    try:
                        os.remove(os.path.join(folder_path, file))
                    except Exception as e:
                        st.error(f"Error borrando {file}: {e}")
                 st.success("¡Todo limpio!")
                 st.rerun()

# --- Helper to list transcripts ---
def get_transcripts():
    directory = get_out_dir("transcripts")
    return glob.glob(os.path.join(directory, "*.txt"))

# --- Helper for Global Memory (All Course Content) ---
def get_global_context():
    """Reads ALL text context: Global Memory (Library) + All Transcripts."""
    
    context_str = ""
    file_count = 0
    
    # 1. READ EVERYTHING IN LIBRARY (Recursive)
    lib_path = get_out_dir("library") 
    
    if os.path.exists(lib_path):
        for root, dirs, files in os.walk(lib_path):
            for f in files:
                if f.lower().endswith((".txt", ".md")):
                    file_count += 1
                    full_path = os.path.join(root, f)
                    try:
                        # Get folder name for context
                        folder_name = os.path.basename(root)
                        with open(full_path, "r", encoding="utf-8") as file:
                            context_str += f"\n--- BIBLIOTECA / {folder_name} ({f}) ---\n{file.read()}\n"
                    except: pass

    # 2. Bulk/Knowledge: All Transcripts
    transcripts_path = get_out_dir("transcripts")
    if os.path.exists(transcripts_path):
        for f in os.listdir(transcripts_path):
             if f.lower().endswith((".txt", ".md")):
                file_count += 1
                try:
                     with open(os.path.join(transcripts_path, f), "r", encoding="utf-8") as file:
                         context_str += f"\n--- TRANSCRIPCIÓN DE CLASE ({f}) ---\n{file.read()}\n"
                except: pass
                
    return context_str, file_count

# --- API KEY MANAGEMENT ---
def load_api_key():
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
st.markdown("""
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
""
    
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
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
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

    st.header("⚙️ Configuración")
    saved_key = load_api_key()
    api_key = st.text_input("Clave API de Gemini", value=saved_key, type="password")
    
    if st.button("Guardar Clave"):
        save_api_key(api_key)
        st.success("Guardada")
        
    st.divider()
    
    # --- COURSE SELECTOR (WORKSPACES) ---
    st.header("📂 Espacio de Trabajo")
    
    # scan for existing courses
    if os.path.exists(CORE_OUTPUT_ROOT):
        existing_courses = [d for d in os.listdir(CORE_OUTPUT_ROOT) if os.path.isdir(os.path.join(CORE_OUTPUT_ROOT, d))]
    
    # Setup default if absolutely nothing exists
    if not existing_courses:
        existing_courses = ["Diplomado_Marketing_Inicial"]
        
    # Ensure current selection is valid
    if 'current_course' not in st.session_state or st.session_state['current_course'] not in existing_courses:
        st.session_state['current_course'] = existing_courses[0]
        
    selected_course = st.selectbox("Diplomado Actual:", existing_courses + ["➕ Crear Nuevo..."], index=existing_courses.index(st.session_state['current_course']) if st.session_state['current_course'] in existing_courses else 0)
    
    if selected_course == "➕ Crear Nuevo...":
        new_course_name = st.text_input("Nombre del Nuevo Diplomado:", placeholder="Ej: Curso IA Contenido")
        if st.button("Crear Espacio"):
            if new_course_name:
                safe_name = "".join([c for c in new_course_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                st.session_state['current_course'] = safe_name
                st.rerun()
    else:
        st.session_state['current_course'] = selected_course

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
        courses_to_del = st.multiselect("Selecciona para borrar:", existing_courses, key="del_courses_sel")
        if st.button("Eliminar Seleccionados", key="btn_del_courses"):
            if courses_to_del:
                for c_del in courses_to_del:
                    path_del = os.path.join(CORE_OUTPUT_ROOT, c_del)
                    try:
                        shutil.rmtree(path_del) # Recursive delete
                    except Exception as e:
                        st.error(f"Error {c_del}: {e}")
                
                st.success("Eliminados correchamente.")
                # Reset selection logic will handle the missing course on rerun
                st.rerun()

    st.caption(f"Guardando en: `output/{st.session_state['current_course']}/...`")
    st.divider()
    
    # Custom Lilac Info Box
    st.markdown("""
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
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []

# --- Session State Initialization ---
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []
if 'notes_result' not in st.session_state: st.session_state['notes_result'] = None
if 'guide_result' not in st.session_state: st.session_state['guide_result'] = None
if 'quiz_results' not in st.session_state: st.session_state['quiz_results'] = []
if 'quiz_key' not in st.session_state: st.session_state['quiz_key'] = 0
if 'pasted_images' not in st.session_state: st.session_state['pasted_images'] = []
if 'homework_result' not in st.session_state: st.session_state['homework_result'] = None

# --- MAIN TITLE & HEADER ---
st.title("🎓 Estudian2")
st.markdown("Tu compañero integral para estudiar diplomados: Transcribe, Resume, Guía y Practica.")

# --- Tabs ---
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
        
        st.markdown(f"""
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
        """, unsafe_allow_html=True)
    else:
        st.error(f"Image not found: {img_path}")

# --- TAB 1: Transcriptor ---
with tab1:
    # LAYOUT: Image Left (1) | Text Right (1.5)
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
        render_image_card("illustration_transcriber_1765052797646.png")

    with col_text:
        st.markdown("""
        <div class="card-text">
            <h2 style="margin-top:0;">1. Transcriptor de Videos</h2>
            <p style="color: #64748b; font-size: 1.1rem; margin-bottom: 20px;">
                Sube los videos de tu unidad para procesarlos automáticamente.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("Arrastra tus archivos aquí", type=['mp4', 'mov', 'avi', 'mkv'], accept_multiple_files=True, key="up1")
        
        if uploaded_files:
            if st.button("Iniciar Transcripción", key="btn1", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                out_dir = get_out_dir("transcripts") # Dynamic Path
                
                for i, file in enumerate(uploaded_files):
                    status_text.markdown(f"**Iniciando {file.name}... (0%)**")
                    temp_path = file.name
                    with open(temp_path, "wb") as f: f.write(file.getbuffer())
                    
                    try:
                        # Define callback to update UI with percentage
                        def update_ui(msg, prog):
                            pct = int(prog * 100)
                            progress_bar.progress(prog)
                            status_text.markdown(f"**{msg} ({pct}%)**")

                        # Process with callback
                        txt_path = transcriber.process_video(temp_path, progress_callback=update_ui, chunk_length_sec=600)
                        
                        final_path = os.path.join(out_dir, os.path.basename(txt_path))
                        if os.path.exists(final_path): os.remove(final_path)
                        os.rename(txt_path, final_path)
                        
                        st.success(f"✅ {file.name} procesado (100%)")
                        
                        with open(final_path, "r", encoding="utf-8") as f: trans_text = f.read()
                        
                        # Store in session state for persistence
                        st.session_state['transcript_history'].append({"name": file.name, "text": trans_text})
                        
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        if os.path.exists(temp_path): os.remove(temp_path)
                    
                    progress_bar.progress(1.0)
                
                status_text.success("¡Todo listo! (100%)")

        # --- PERSISTENT RESULTS DISPLAY (Outside button block) ---
        if st.session_state['transcript_history']:
            for i, item in enumerate(st.session_state['transcript_history']):
                st.divider()
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown(f"### 📄 Transcripción: {item['name']}")
                with c_copy:
                    if st.button("📄", key=f"cp_t_{i}", help="Copiar Texto Limpio"):
                        clean_txt = clean_markdown(item['text'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("¡Copiado!", icon='📋')
                
                # Visual Display
                st.markdown(item['text'])

# --- TAB 2: Apuntes Simples ---
with tab2:
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
         render_image_card("illustration_notes_1765052810428.png")
         
    with col_text:
        st.markdown("""
        <div class="card-text">
            <h2 style="margin-top:0;">2. Generador de Apuntes</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Convierte transcripciones en apuntes claros y concisos.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File Manager
        delete_files_ui(get_out_dir("transcripts"), "tab2")
        
        transcript_files = get_transcripts()
        
        # Check Global Memory
        gl_ctx, gl_count = get_global_context()
        if gl_count > 0:
            st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")
        
        if not transcript_files:
            st.info("Primero sube videos en la Pestaña 1.")
        else:
            options = [os.path.basename(f) for f in transcript_files]
            selected_file = st.selectbox("Selecciona una transcripción:", options, key="sel2")
            if selected_file and st.button("Generar Apuntes", key="btn2"):
                full_path = os.path.join(get_out_dir("transcripts"), selected_file)
                with open(full_path, "r", encoding="utf-8") as f: text = f.read()
                
                with st.spinner("Creando apuntes progresivos (3 Niveles)..."):
                    # Now returns a JSON dict
                    notes_data = assistant.generate_notes(text, global_context=gl_ctx)
                    
                    # Save as JSON for structure preservation
                    base_name = selected_file.replace("_transcripcion.txt", "")
                    save_path = os.path.join(get_out_dir("notes"), f"Apuntes_{base_name}.json")
                    
                    import json
                    with open(save_path, "w", encoding="utf-8") as f: 
                        json.dump(notes_data, f, ensure_ascii=False, indent=2)
                    
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
        st.markdown("""
        <div class="card-text">
            <h2 style="margin-top:0;">3. Guía de Estudio Estratégica</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Crea mapas, resúmenes y preguntas de examen.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # File Manager
        delete_files_ui(get_out_dir("transcripts"), "tab3")
        
        transcript_files = get_transcripts()
        
        # Check Global Memory
        gl_ctx, gl_count = get_global_context()
        if gl_count > 0:
            st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")

        if not transcript_files:
             st.info("Primero sube videos en la Pestaña 1.")
        else:
            options_guide = [os.path.basename(f) for f in transcript_files]
            selected_guide_file = st.selectbox("Archivo base:", options_guide, key="sel3")
            
            if selected_guide_file and st.button("Generar Guía", key="btn3"):
                full_path = os.path.join(get_out_dir("transcripts"), selected_guide_file)
                with open(full_path, "r", encoding="utf-8") as f: text = f.read()
                    
                with st.spinner("Diseñando estrategia de estudio..."):
                    guide = assistant.generate_study_guide(text, global_context=gl_ctx)
                    base_name = selected_guide_file.replace("_transcripcion.txt", "")
                    save_path = os.path.join(get_out_dir("guides"), f"Guia_{base_name}.txt")
                    with open(save_path, "w", encoding="utf-8") as f: f.write(guide)
                    
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
        st.markdown("""
        <div class="card-text">
            <h2 style="margin-top:0;">4. Ayudante de Pruebas</h2>
            <p style="color: #64748b; font-size: 1.1rem;">Modo Ráfaga: Sube múltiples preguntas y obtén las respuestas.</p>
        </div>
        """, unsafe_allow_html=True)
        
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
    st.markdown("""
    <div class="card-text">
        <h2 style="margin-top:0;">5. Ayudante de Tareas & Biblioteca</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Tu "Segundo Cerebro": Guarda conocimientos y úsalos para resolver tareas.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
            
            # Key management for auto-clear
            if 'upl_counter' not in st.session_state: st.session_state['upl_counter'] = 0
            
            if not is_global:
                 # Smart Folder Selection logic for Main Upload
                 existing_folders_main = []
                 lib_root_main = get_out_dir("library")
                 if os.path.exists(lib_root_main):
                     existing_folders_main = [d for d in os.listdir(lib_root_main) if os.path.isdir(os.path.join(lib_root_main, d)) and d != "00_Memoria_Global"]
                 
                 # Dropdown
                 sel_option = st.selectbox("Selecciona Unidad (Carpeta):", options=["✨ Nueva Carpeta..."] + existing_folders_main)
                 
                 if sel_option == "✨ Nueva Carpeta...":
                     unit_name = st.text_input("Nombre de la Nueva Carpeta", placeholder="Ej: Unidad 1 - Fundamentos", key=f"in_unit_name_{st.session_state['upl_counter']}").strip()
                 else:
                     unit_name = sel_option
                 topic_name = st.text_input("Tema / Título del Archivo", placeholder="Ej: Publico_Objetivo", key=f"in_topic_name_{st.session_state['upl_counter']}").strip()
            else:
                st.info("ℹ️ Se guardará en **00_Memoria_Global** y se usará automáticamente en todo.")
            
            st.markdown("##### 2. Contenido")
            content_source = st.radio("Fuente:", ["Subir PDFs (Temarios/Lecturas)", "Subir Archivos TXT/MD", "Pegar Texto"], horizontal=True)
            
            uploaded_pdfs = []
            uploaded_txts = []
            text_content = ""
            
            # Use dynamic keys for uploaders to allow clearing
            upl_key = f"upl_{st.session_state['upl_counter']}"
            
            if content_source == "Subir PDFs (Temarios/Lecturas)":
                 uploaded_pdfs = st.file_uploader("Sube uno o más PDFs", type=['pdf'], accept_multiple_files=True, key=f"pdf_{upl_key}")
            elif content_source == "Subir Archivos TXT/MD":
                uploaded_txts = st.file_uploader("Sube archivos de texto", type=['txt', 'md'], accept_multiple_files=True, key=f"txt_{upl_key}")
            elif content_source == "Pegar Texto":
                text_content = st.text_area("Pega aquí el contenido:", height=150, key=f"in_text_content_{st.session_state['upl_counter']}")
            
            if st.button("💾 Guardar en Memoria", key="save_lib"):
                # Determine Destination
                dest_unit = "00_Memoria_Global" if is_global else "".join([c for c in unit_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                
                # Validation
                if not is_global and not dest_unit:
                    st.warning("⚠️ Escribe un nombre de Unidad.")
                elif content_source == "Pegar Texto" and (not text_content or (not is_global and not topic_name)):
                     st.warning("⚠️ Completa el texto y el título.")
                elif content_source != "Pegar Texto" and not uploaded_pdfs and not uploaded_txts:
                     st.warning("⚠️ Sube al menos un archivo.")
                else:
                    # Proceed to Save
                    lib_base = get_out_dir("library")
                    final_dir = os.path.join(lib_base, dest_unit)
                    os.makedirs(final_dir, exist_ok=True)
                    
                    saved_count = 0
                    
                    # 1. Handle PDFs
                    if uploaded_pdfs:
                        with st.spinner(f"Procesando {len(uploaded_pdfs)} PDFs..."):
                            for pdf in uploaded_pdfs:
                                txt = assistant.extract_text_from_pdf(pdf.getvalue(), pdf.type)
                                fname = f"{os.path.splitext(pdf.name)[0]}.txt"
                                with open(os.path.join(final_dir, fname), "w", encoding="utf-8") as f: f.write(txt)
                                saved_count += 1
                                
                    # 2. Handle TXTs
                    if uploaded_txts:
                        for txt_file in uploaded_txts:
                             content = txt_file.read().decode("utf-8")
                             with open(os.path.join(final_dir, txt_file.name), "w", encoding="utf-8") as f: f.write(content)
                             saved_count += 1
                             
                    # 3. Handle Pasted Text
                    if text_content:
                        safe_topic = "".join([c for c in topic_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                        if not safe_topic: safe_topic = "Nota_Rapida"
                        with open(os.path.join(final_dir, f"{safe_topic}.txt"), "w", encoding="utf-8") as f: f.write(text_content)
                        saved_count += 1
                        
                    st.success(f"✅ ¡{saved_count} archivos guardados en '{dest_unit}'!")
                    
                    # Increment counter to reset ALL widgets
                    st.session_state['upl_counter'] += 1
                    
                    import time
                    time.sleep(1.0)
                    st.rerun()
        
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
                
                st.markdown("#### 🧐 Vista Previa de Temas Detectados")
                
                # Smart Folder Selection
                existing_folders = []
                lib_root = get_out_dir("library")
                if os.path.exists(lib_root):
                    existing_folders = [d for d in os.listdir(lib_root) if os.path.isdir(os.path.join(lib_root, d))]
                
                # Default "Rescate" if exists, otherwise first one
                default_idx = 0
                if "01_Rescate_Importado" in existing_folders:
                     default_idx = existing_folders.index("01_Rescate_Importado")
                
                target_option = st.selectbox(
                    "¿Dónde guardamos estos archivos?", 
                    options=existing_folders + ["✨ Nueva Carpeta..."],
                    index=default_idx if existing_folders else 0
                )
                
                if target_option == "✨ Nueva Carpeta...":
                    target_unit_import = st.text_input("Nombre de la Nueva Carpeta:", value="01_Rescate_Importado")
                else:
                    target_unit_import = target_option
                
                valid_items = [item for item in st.session_state['bulk_import_data'] if 'title' in item and 'content' in item]
                
                for idx, item in enumerate(valid_items):
                    with st.expander(f"📄 {item['title']}"):
                        st.markdown(item['content'][:500] + "...")
                
                if st.button(f"💾 Guardar {len(valid_items)} Archivos en Biblioteca", key="save_bulk_all"):
                    lib_root = get_out_dir("library") # Ensure explicit definition here
                    import_path = os.path.join(lib_root, target_unit_import)
                    os.makedirs(import_path, exist_ok=True)
                    
                    saved_count = 0
                    for item in valid_items:
                        # Sanitize filename
                        safe_title = "".join([c if c.isalnum() else "_" for c in item['title']])
                        f_path = os.path.join(import_path, f"{safe_title}.md")
                        with open(f_path, "w", encoding="utf-8") as f:
                            f.write(item['content'])
                        saved_count += 1
                    
                    st.success(f"✅ ¡{saved_count} temas rescatados y guardados en '{target_unit_import}'!")
                    st.session_state['bulk_import_data'] = None # Clear after save
                    import time
                    time.sleep(1)
                    st.rerun()

        # Show existing library
        st.markdown(f"##### 📂 Contenido Guardado ({st.session_state['current_course']}):")
        lib_root = get_out_dir("library")
        if os.path.exists(lib_root):
             # Sort so 00_Memoria_Global is always first
            units = sorted(os.listdir(lib_root))
            for unit in units:
                unit_path = os.path.join(lib_root, unit)
                if not os.path.exists(unit_path): continue # Skip if renamed/deleted
                if os.path.isdir(unit_path):
                    # Icon logic
                    icon = "🧠" if unit == "00_Memoria_Global" else "📁"
                    label = "Memoria GLOBAL (Siempre activa)" if unit == "00_Memoria_Global" else unit
                    
                    with st.expander(f"{icon} {label}"):
                        # --- UNIT MANAGEMENT ---
                        if unit != "00_Memoria_Global":
                            col_u_ren, col_u_act = st.columns([0.8, 0.2])
                            with col_u_ren:
                                # Rename Unit Interface
                                if f"ren_u_{unit}" in st.session_state:
                                    new_u_name = st.text_input("Nuevo nombre carpeta:", value=unit, key=f"in_u_{unit}")
                                    if st.button("Guardar Nombre", key=f"save_u_{unit}"):
                                        if new_u_name and new_u_name != unit:
                                            try:
                                                os.rename(unit_path, os.path.join(lib_root, new_u_name))
                                                del st.session_state[f"ren_u_{unit}"]
                                                st.success("Carpeta renombrada!")
                                                time.sleep(0.5)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                else:
                                    st.caption(f"Carpeta: {unit}")
                            with col_u_act:
                                if f"ren_u_{unit}" not in st.session_state:
                                    c_u_ren, c_u_del = st.columns([1, 1])
                                    with c_u_ren:
                                        if st.button("✏️", key=f"btn_ren_u_{unit}", help="Renombrar Carpeta"):
                                            st.session_state[f"ren_u_{unit}"] = True
                                            st.rerun()
                                    with c_u_del:
                                        # Confirm Delete Logic
                                        if f"conf_del_u_{unit}" not in st.session_state:
                                            if st.button("🗑️", key=f"btn_del_u_{unit}", help="Borrar Carpeta Completa"):
                                                st.session_state[f"conf_del_u_{unit}"] = True
                                                st.rerun()
                                        else:
                                            if st.button("🔥", key=f"confirm_del_u_{unit}", help="¿Seguro? ¡Se borrará todo!"):
                                                import shutil
                                                shutil.rmtree(unit_path)
                                                del st.session_state[f"conf_del_u_{unit}"]
                                                st.rerun()
                                            st.caption("¿Confirmar?")

                        # --- FILE MANAGEMENT ---
                        files = os.listdir(unit_path)
                        if not files: st.caption("Vacío")
                        
                        for f in files:
                            f_path = os.path.join(unit_path, f)
                            
                            # Single Row Layout: [Icon(5%) Name(65%) View(10%) Edit(10%) Del(10%)]
                            # vertical_alignment="center" ensures buttons align with text
                            c_icon, c_name, c_view, c_edit, c_del = st.columns([0.05, 0.65, 0.1, 0.1, 0.1], vertical_alignment="center")
                            
                            with c_icon:
                                st.markdown("📄")
                                
                            with c_name:
                                # Rename File Interface
                                if f"ren_f_{f_path}" in st.session_state:
                                    new_f_name = st.text_input("Renombrar:", value=f, key=f"in_f_{f_path}", label_visibility="collapsed")
                                    if st.button("💾", key=f"save_f_{f_path}", help="Guardar nombre"):
                                        if new_f_name and new_f_name != f:
                                            try:
                                                os.rename(f_path, os.path.join(unit_path, new_f_name))
                                                del st.session_state[f"ren_f_{f_path}"]
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                else:
                                    # Use caption or markdown to make it standard text size but aligned
                                    st.markdown(f"{f}")
                            
                            if f"ren_f_{f_path}" not in st.session_state:
                                with c_view:
                                    # Toggle View
                                    view_key = f"view_f_{f_path}"
                                    icon_view = "👁️" if not st.session_state.get(view_key, False) else "🙈"
                                    if st.button(icon_view, key=f"btn_view_{f_path}", help="Ver/Ocultar contenido"):
                                        st.session_state[view_key] = not st.session_state.get(view_key, False)
                                        st.rerun()
                                        
                                with c_edit:
                                    if st.button("✏️", key=f"edit_{f_path}", help="Renombrar archivo"):
                                        st.session_state[f"ren_f_{f_path}"] = True
                                        st.rerun()
                                with c_del:
                                    if st.button("🗑️", key=f"del_{f_path}", help="Borrar archivo permanente"):
                                        try:
                                            os.remove(f_path)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                            else:
                                # Cancel button when renaming
                                with c_view:
                                    if st.button("❌", key=f"cancel_{f_path}", help="Cancelar"):
                                        del st.session_state[f"ren_f_{f_path}"]
                                        st.rerun()
                            
                            # CONTENT VIEWER
                            if st.session_state.get(f"view_f_{f_path}", False):
                                try:
                                    with open(f_path, "r", encoding="utf-8") as f_read:
                                        content_view = f_read.read()
                                    st.info(f"📜 Contenido de: {f}")
                                    st.code(content_view, language="markdown")
                                    if st.button("Cerrar Visualización", key=f"close_{f_path}"):
                                        st.session_state[f"view_f_{f_path}"] = False
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"No se pudo leer el archivo: {e}")
    
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
        
        # Check for Global Memory
        global_path = os.path.join(lib_root, "00_Memoria_Global")
        has_global = os.path.exists(global_path) and os.listdir(global_path)
        
        if has_global:
            global_files = [f for f in os.listdir(global_path) if f.endswith(".txt")]
            st.success(f"✅ **Memoria Global Activa:** Usando {len(global_files)} archivos base (Temarios/Reglas).")
            
        st.caption("ℹ️ Además de la Memoria Global, selecciona las unidades específicas para esta tarea:")
        
        available_units = []
        if os.path.exists(lib_root):
            # Exclude Global from selection list to avoid redundancy
            available_units = [d for d in os.listdir(lib_root) if os.path.isdir(os.path.join(lib_root, d)) and d != "00_Memoria_Global"]
        
        selected_units = st.multiselect("Unidades Específicas:", available_units, placeholder="Ej: Unidad 1...")
        
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
                    for f_name in os.listdir(global_path):
                         with open(os.path.join(global_path, f_name), "r", encoding="utf-8") as f:
                                gathered_texts.append(f"--- [MEMORIA GLOBAL / OBLIGATORIO]: {f_name} ---\n{f.read()}\n")

                # 2. Add Selected Units
                for unit in selected_units:
                    unit_path = os.path.join(lib_root, unit)
                    for f_name in os.listdir(unit_path):
                        if f_name.endswith(".txt") or f_name.endswith(".md"):
                            with open(os.path.join(unit_path, f_name), "r", encoding="utf-8") as f:
                                gathered_texts.append(f"--- ARCHIVO: {unit}/{f_name} ---\n{f.read()}\n")
                
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
                            # Context files structure for arg mode is list of dicts?
                            # Current gathered_texts is list of strings.
                            # Changing study_assistant to accept list of strings as usual or list of dicts.
                            # Wait, solve_argumentative_task expects context_files=[], global_context=""
                            # gather_texts currently merges everything.
                            # Let's just pass the merged text as global_context for simplicity, 
                            # or re-parse gathered_texts into the list format if highly needed.
                            # Simpler: Pass merged text as "global_context" strings.
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
                
                bridge_msg = f"""
                Hola Profe IA. Acabo de generar una respuesta para esta tarea:
                
                **CONSIGNA:**
                _{task_prompt}_
                
                **MI BORRADOR (Generado por Asistente):**
                {full_text_response}
                
                Quiero que analicemos esto. ¿Qué opinas? ¿Podemos mejorarlo?
                """
                
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
    st.markdown("""
    <div class="card-text">
        <h2 style="margin-top:0;">6. Tutoría Personalizada (Profesor IA)</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Tu profesor particular. Pregunta, sube tareas para corregir y dialoga en tiempo real.</p>
    </div>
    """, unsafe_allow_html=True)
    
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
