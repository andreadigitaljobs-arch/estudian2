
import streamlit as st
import os
import glob
from transcriber import Transcriber
from study_assistant import StudyAssistant
import shutil

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

st.set_page_config(page_title="Estudian2", page_icon="🎓", layout="wide")

st.title("🎓 Estudian2")
st.markdown("Tu compañero integral para estudiar diplomados: Transcribe, Resume, Guía y Practica.")

# --- Custom CSS for "Estudian2" Elegant Theme ---
st.markdown("""
<style>
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

# --- HELPER FUNCTIONS ---
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


# --- Shared Configuration ---
def load_api_key():
    if os.path.exists("api_key.txt"):
        with open("api_key.txt", "r") as f:
            return f.read().strip()
    return ""

def save_api_key(key):
    with open("api_key.txt", "w") as f:
        f.write(key)

# Sidebar
with st.sidebar:
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

if not api_key:
    st.warning("⚠️ Por favor ingresa tu API Key en la barra lateral para comenzar.")
    st.stop()

# Initialize Assistants
transcriber = Transcriber(api_key)
assistant = StudyAssistant(api_key)

# --- Session State Initialization ---
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []
if 'notes_result' not in st.session_state: st.session_state['notes_result'] = None
if 'guide_result' not in st.session_state: st.session_state['guide_result'] = None
if 'quiz_results' not in st.session_state: st.session_state['quiz_results'] = []
if 'quiz_key' not in st.session_state: st.session_state['quiz_key'] = 0
if 'homework_result' not in st.session_state: st.session_state['homework_result'] = None

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📹 Transcriptor", 
    "📝 Apuntes Simples", 
    "🗺️ Guía de Estudio", 
    "🧠 Ayudante Quiz",
    "👩‍🏫 Ayudante de Tareas"
])

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

# --- Helper to list transcripts ---
def get_transcripts():
    directory = get_out_dir("transcripts")
    return glob.glob(os.path.join(directory, "*.txt"))

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
        
        if not transcript_files:
            st.info("Primero sube videos en la Pestaña 1.")
        else:
            options = [os.path.basename(f) for f in transcript_files]
            selected_file = st.selectbox("Selecciona una transcripción:", options, key="sel2")
            
            if selected_file and st.button("Generar Apuntes", key="btn2"):
                full_path = os.path.join(get_out_dir("transcripts"), selected_file)
                with open(full_path, "r", encoding="utf-8") as f: text = f.read()
                
                with st.spinner("Creando apuntes mágicos..."):
                    notes = assistant.generate_notes(text)
                    base_name = selected_file.replace("_transcripcion.txt", "")
                    save_path = os.path.join(get_out_dir("notes"), f"Apuntes_{base_name}.txt")
                    with open(save_path, "w", encoding="utf-8") as f: f.write(notes)
                    
                    st.success("¡Apuntes generados!")
                    st.session_state['notes_result'] = notes # Save to session

            # --- PERSISTENT RESULTS DISPLAY ---
            if st.session_state['notes_result']:
                st.divider()
                
                # HEADER + COPY ICON
                c_head, c_copy = st.columns([0.9, 0.1])
                with c_head:
                    st.markdown("### 📝 Tus Apuntes")
                with c_copy:
                    if st.button("📄", key="cp_notes", help="Copiar Apuntes Limpios"):
                        clean_txt = clean_markdown(st.session_state['notes_result'])
                        if copy_to_clipboard(clean_txt):
                            st.toast("¡Copiado!", icon='📋')
                # Visual Display
                st.markdown(st.session_state['notes_result'])

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
        if not transcript_files:
             st.info("Primero sube videos en la Pestaña 1.")
        else:
            options_guide = [os.path.basename(f) for f in transcript_files]
            selected_guide_file = st.selectbox("Archivo base:", options_guide, key="sel3")
            
            if selected_guide_file and st.button("Generar Guía", key="btn3"):
                full_path = os.path.join(get_out_dir("transcripts"), selected_guide_file)
                with open(full_path, "r", encoding="utf-8") as f: text = f.read()
                    
                with st.spinner("Diseñando estrategia de estudio..."):
                    guide = assistant.generate_study_guide(text)
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
        
        # RESET BUTTON
        col_up, col_reset = st.columns([0.9, 0.1])
        with col_reset:
             # Use the same 'copy-btn' style or just a clean emoji button
             if st.button("🗑️", key="reset_quiz", help="Borrar todo para empezar de cero"):
                 st.session_state['quiz_results'] = []
                 st.session_state['quiz_key'] += 1
                 st.rerun()
                 
        with col_up:
            img_files = st.file_uploader("Sube capturas de preguntas", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"up4_{st.session_state['quiz_key']}")
        
        if img_files and st.button("Resolver Preguntas", key="btn4"):
            progress_bar = st.progress(0)
            status = st.empty()
            results = [] 
            
            for i, img_file in enumerate(img_files):
                # Calculate percentages
                current_percent = int((i / len(img_files)) * 100)
                status.markdown(f"**Analizando foto {i+1} de {len(img_files)}... ({current_percent}%)**")
                progress_bar.progress(i / len(img_files))
                
                temp_img_path = f"temp_quiz_{i}.png"
                with open(temp_img_path, "wb") as f: f.write(img_file.getbuffer())
                
                try:
                    full_answer = assistant.solve_quiz(temp_img_path)
                    short_answer = "Respuesta no detectada"
                    for line in full_answer.split('\n'):
                        if "**Respuesta Correcta:**" in line:
                            short_answer = line.replace("**Respuesta Correcta:**", "").strip()
                            break
                    results.append({"name": img_file.name, "full": full_answer, "short": short_answer, "img_obj": img_file})
                except Exception as e:
                    results.append({"name": img_file.name, "full": str(e), "short": "Error", "img_obj": img_file})
                finally:
                    if os.path.exists(temp_img_path): os.remove(temp_img_path)
                
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
            
            if not is_global:
                 unit_name = st.text_input("Nombre de la Unidad (Carpeta)", placeholder="Ej: Unidad 1 - Fundamentos").strip()
                 topic_name = st.text_input("Tema / Título del Archivo", placeholder="Ej: Publico_Objetivo").strip()
            else:
                st.info("ℹ️ Se guardará en **00_Memoria_Global** y se usará automáticamente en todo.")
            
            st.markdown("##### 2. Contenido")
            content_source = st.radio("Fuente:", ["Subir PDFs (Temarios/Lecturas)", "Subir Archivos TXT/MD", "Pegar Texto"], horizontal=True)
            
            uploaded_pdfs = []
            uploaded_txts = []
            text_content = ""
            
            if content_source == "Subir PDFs (Temarios/Lecturas)":
                 uploaded_pdfs = st.file_uploader("Sube uno o más PDFs", type=['pdf'], accept_multiple_files=True)
            elif content_source == "Subir Archivos TXT/MD":
                uploaded_txts = st.file_uploader("Sube archivos de texto", type=['txt', 'md'], accept_multiple_files=True)
            elif content_source == "Pegar Texto":
                text_content = st.text_area("Pega aquí el contenido:", height=150)
            
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

        # Show existing library
        st.markdown(f"##### 📂 Contenido Guardado ({st.session_state['current_course']}):")
        lib_root = get_out_dir("library")
        if os.path.exists(lib_root):
             # Sort so 00_Memoria_Global is always first
            units = sorted(os.listdir(lib_root))
            for unit in units:
                unit_path = os.path.join(lib_root, unit)
                if os.path.isdir(unit_path):
                    # Icon logic
                    icon = "🧠" if unit == "00_Memoria_Global" else "📁"
                    label = "Memoria GLOBAL (Siempre activa)" if unit == "00_Memoria_Global" else unit
                    
                    with st.expander(f"{icon} {label}"):
                        files = os.listdir(unit_path)
                        if not files: st.caption("Vacío")
                        for f in files:
                            st.text(f"📄 {f}")
                            # Delete button could go here
    
    # --- RIGHT COLUMN: HOMEWORK SOLVER ---
    with col_task:
        st.markdown("### 🧠 Ayudante Inteligente")
        st.caption("Resuelve tareas usando SOLO la información de tu biblioteca.")
        
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
        
        if st.button("🚀 Resolver Tarea", key="solve_task", use_container_width=True):
            if not selected_units and not has_global:
                st.warning("⚠️ Tu biblioteca está vacía. Sube algo primero.")
            elif not task_prompt and not task_file:
                st.warning("⚠️ Escribe la tarea o sube un archivo.")
            else:
                # Gather context
                gathered_texts = []
                
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
                
                with st.spinner("Consultando biblioteca global y unidades seleccionadas..."):
                    try:
                        solution = assistant.solve_homework(task_prompt, gathered_texts, task_attachment=attachment_data)
                        st.session_state['homework_result'] = solution
                    except Exception as e:
                        st.error(f"Error resolviendo tarea: {e}")
        
        # --- RESULT DISPLAY ---
        if st.session_state['homework_result']:
            st.divider()
            # HEADER + COPY ICON
            c_head, c_copy = st.columns([0.9, 0.1])
            with c_head:
                st.markdown("### ✅ Respuesta")
            with c_copy:
                 if st.button("📄", key="cp_hw", help="Copiar Respuesta"):
                    clean_txt = clean_markdown(st.session_state['homework_result'])
                    if copy_to_clipboard(clean_txt):
                        st.toast("¡Copiado!", icon='📋')
            
            st.markdown(st.session_state['homework_result'])
