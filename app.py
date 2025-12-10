
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
from database import delete_course, rename_course # Force import availability


# --- GENERATE VALID ICO (FIX) ---
try:
    import os
    from PIL import Image
    # Always regenerate to ensure validity
    if os.path.exists("assets/favicon.jpg"):
        img = Image.open("assets/favicon.jpg")
        img.save("assets/windows_icon.ico", format='ICO', sizes=[(256, 256)])
        print("VALID ICO GENERATED: assets/windows_icon.ico")
except Exception as e:
    print(f"ICO GEN ERROR: {e}")
# --------------------------------

# --- PAGE CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="E-Education",
    page_icon="assets/favicon.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'quiz_results' not in st.session_state: st.session_state['quiz_results'] = []
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []
if 'notes_result' not in st.session_state: st.session_state['notes_result'] = None
if 'guide_result' not in st.session_state: st.session_state['guide_result'] = None

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
if not st.session_state['user'] and not st.session_state.get('force_logout'):
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
                 # CRITICAL FIX: Update cookie with NEW refresh token to keep chain alive
                 cookie_manager.set("supabase_refresh_token", res.session.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                 st.success("⚡ Sesión restaurada. Actualizando...")
                 time.sleep(2) # Allow cookie to set
                 st.rerun()
                 
    except Exception as e:
        print(f"Auto-login failed: {e}")


# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP

# If not logged in, show Login Screen and STOP
if not st.session_state['user']:
    import datetime
    import base64

    # --- HELPER: ASSETS ---
    def get_b64_image(image_path):
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    logo_b64 = get_b64_image("assets/logo_main.png")
    hero_b64 = get_b64_image("assets/messimo_hero_new.png") # Updated to user provided PNG

    # --- CUSTOM CSS FOR FULL BACKGROUND MESSIMO STYLE ---
    st.markdown(f'''
        <style>
        /* 1. RESET & FULL BACKGROUND */
        .stApp {{
            background-image: url("data:image/png;base64,{hero_b64}");
            background-size: contain; /* User wants no whitespace, so cover is best */
            background-position: center;
            background-repeat: no-repeat;
            overflow: hidden !important; /* LOCK SCROLL */
        }}
        
            overflow: hidden !important; /* LOCK SCROLL */
        }}
        
        /* HIDE SCROLLBAR */
        ::-webkit-scrollbar {{
            display: none;
        }}
        
        /* LOCK MAIN STREAMLIT CONTAINER */
        section[data-testid="stAppViewContainer"] {{
            overflow: hidden !important;
        }}
        
        /* 2. ALIGNMENT CONTAINER */
        .main .block-container {{
            padding-top: 0rem !important; /* Reduced to lift card */
            transform: translateY(-50px) !important; /* LIFT GRANDFATHER SUPREME forceful */
            padding-bottom: 0vh !important;
            max_width: 1200px !important;
            display: flex;
            flex-direction: column;
            justify-content: flex-start; /* Align to top instead of center */
            min-height: 10vh;
        }}

        /* GLOBAL SCROLL KILLER */
        * {{
            overflow: hidden !important;
        }}
        
        /* 3. LOGIN CARD CONTAINER (Reference Replica) */
        .login-card {{
            background-color: #FFFFFF;
            padding: 50px 40px; /* Spacious structure like reference */
            border-radius: 40px; /* Large rounded corners from reference */
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 0px !important; /* No bottom margin */
            height: auto;
        }}

        /* 4. PILL INPUTS (Reference Style) */
        .stTextInput > div > div > input {{
            border-radius: 50px !important;
            border: 1px solid #E2E8F0; /* Subtle border */
            padding: 0px 25px; /* Vertical centering is handled by height usually, but padding helps */
            background-color: #FFFFFF;
            color: #1F2937;
            height: 55px; /* Taller inputs like reference */
            font-size: 1rem;
            transition: all 0.2s;
        }}
        .stTextInput > div > div > input:focus {{
            border-color: #3500D3;
            box-shadow: 0 0 0 4px rgba(53, 0, 211, 0.1);
            outline: none;
        }}

        /* 5. PRIMARY BUTTON (Reference Shape) */
        div[data-testid="stButton"] > button[kind="primary"] {{
            width: 100%;
            background-color: #4625b8 !important; /* Brand Purple */
            color: white !important;
            border: none;
            border-radius: 50px !important;
            height: 55px; /* Tall button */
            font-weight: 700;
            font-size: 1.1rem;
            margin-top: 10px;
            box-shadow: none !important; /* Clean shape, no shadow */
            transition: transform 0.2s;
        }}
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background-color: #2900A5 !important;
            transform: translateY(-2px);
            box-shadow: none !important;
        }}
        
        /* 6. SECONDARY/LINK BUTTONS */
        div[data-testid="stButton"] > button[kind="secondary"] {{
            background: transparent !important;
            border: none !important;
            color: #9CA3AF !important; /* Gray for "Have an account?" links check */
            font-weight: 600;
            font-size: 0.9rem;
        }}
        div[data-testid="stButton"] > button[kind="secondary"]:hover {{
            color: #3500D3 !important;
        }}

        /* 7. TYPOGRAPHY */
        .messimo-title {{
            font-family: 'Manrope', sans-serif;
            font-weight: 600; 
            font-size: 2.5rem; /* Large Title */
            color: #7fb74e;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}
        .messimo-subtitle {{
            color: #6B7280;
            margin-bottom: 30px;
            font-size: 1rem;
            font-weight: 500;
        }}
        
        /* 9. FORM CONTAINER OVERRIDE (INPUTS REPLICA FIX) */
        div[data-testid="stVerticalBlock"]:has(div#login_anchor):not(:has(div[data-testid="stVerticalBlock"])) {{
            background-color: #FFFFFF !important;
            padding: 50px 50px !important; /* Balanced padding */
            border-radius: 40px !important;
            box-shadow: none !important; /* Clean flat card */
            gap: 1rem !important; /* Increased gap for better spacing */
            display: flex;
            flex-direction: column;
            margin-top: 0px !important; /* Force card container UP */
            margin-bottom: 0px !important;
        }}

        /* 4. PILL INPUTS (V41 RESTORED) */
        
        /* Phase 1: Parent Layout - Force Full Width and No Clipping */
        div[data-testid="stTextInput"] {{
            width: 100% !important;
            min-width: 100% !important;
            height: auto !important;
            overflow: visible !important; /* Fix bottom border clipping */
        }}
        
        div[data-testid="stTextInput"] > div {{
            width: 100% !important;
            background-color: transparent !important;
            border: none !important;
        }}

        /* Phase 2: The Pill Wrapper - Force Full Width */
        /* Using a robust selector that catches both Standard and Password (with Eye) inputs */
        div[data-testid="stTextInput"] div:has(input) {{
            background-color: #FFFFFF !important;
            border-radius: 50px !important;
            border: 2px solid #D1D5DB !important;
            height: 55px !important; /* Slightly taller to prevent clipping */
            padding: 0px 15px !important;
            box-shadow: none !important;
            width: 100% !important; /* Crucial for Password field */
            box-sizing: border-box !important;
            display: flex !important;
            align-items: center !important; 
        }}
        
        /* Remove inner divs bordering if any (Ghost line prev) */
        div[data-testid="stTextInput"] div:has(input) > div {{
             border: none !important;
        }}

        /* AUTOFILL HACK: Remove ugly blue background from browser autofill */
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus, 
        input:-webkit-autofill:active {{
            -webkit-box-shadow: 0 0 0 30px white inset !important;
            -webkit-text-fill-color: #374151 !important;
            transition: background-color 5000s ease-in-out 0s; /* Delay default bg */
        }}

        /* Phase 3: The Input Element Itself */
        div[data-testid="stTextInput"] input {{
             background-color: transparent !important;
             border: none !important;
             outline: none !important;
             box-shadow: none !important;
             color: #374151 !important;
             width: 100% !important;
        }}

        /* Phase 4: Focus State */
        div[data-testid="stTextInput"] div:has(input):focus-within {{
            border-color: #3500D3 !important;
            box-shadow: none !important; /* Removed glow/double border */
        }}
        
        /* HIDE UI */
        #MainMenu, header, footer {{ display: none !important; }}
        
        /* HIDE SIDEBAR ON LOGIN PAGE */
        [data-testid="stSidebar"] {{ display: none !important; }}
        [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        </style>
    ''', unsafe_allow_html=True)

    # --- JS: NUCLEAR SCROLL LOCK ---
    import streamlit.components.v1 as components
    components.html("""
        <script>
            function lockScroll() {
                try {
                    const doc = window.parent.document;
                    // Lock Body and HTML
                    doc.body.style.overflow = "hidden";
                    doc.documentElement.style.overflow = "hidden";
                    
                    // Lock Streamlit Containers
                    const scrollContainers = doc.querySelectorAll('section[data-testid="stAppViewContainer"], section.main, .stApp');
                    scrollContainers.forEach(el => {
                        el.style.overflow = "hidden";
                    });
                } catch(e) {}
            }
            
            // Run immediately and then every 100ms to fight re-renders
            lockScroll();
            setInterval(lockScroll, 100);
        </script>
    """, height=0, width=0)

    # --- LAYOUT: Right Sided Card ---
    
    c_spacer, c_login = st.columns([1.3, 1]) 

    with c_spacer:
        st.write("") 

    with c_login:
        # ANCHOR FOR CSS TARGETING
        st.markdown('<div id="login_anchor"></div>', unsafe_allow_html=True)
        
        # LOGO HEADER
        
        logo_html = ""
        if logo_b64:
             # Height 280px. Adjusted margins: -110px Top (Lifted), -50px Bottom (Separated)
             logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 280px; width: auto; max-width: 100%; display: block; margin: -110px auto -50px auto;">'
        
        # Title: "Vamos a estudiar" - Title lifted closer to logo, inputs compensated
        st.markdown(f'<div style="text-align: center; margin-bottom: 30px; margin-top: 0px;"><div style="display: flex; align-items: center; justify-content: center; margin-bottom: -20px;">{logo_html}</div><div class="messimo-title" style="margin-top: -30px;">¡Vamos a estudiar!</div></div>', unsafe_allow_html=True)

        # FORM INPUTS
        email = st.text_input("Email", key="login_email", placeholder="Correo electrónico", label_visibility="collapsed")
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Contraseña", label_visibility="collapsed")
        
        if st.button("Iniciar sesión", type="primary", key="btn_login", use_container_width=True):
                if email and password:
                    from database import sign_in
                    user = sign_in(email, password)
                    if user:
                        st.session_state['user'] = user
                        if 'supabase_session' in st.session_state:
                             try:
                                 sess = st.session_state['supabase_session']
                                 cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                                 time.sleep(2) # Wait for cookie to write
                             except Exception as e: 
                                 print(f"Cookie set error: {e}")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")


        
        # TERMS & FOOTER
        # Keeping Terms in English for now or translating? "ponerlo en español todo lo inglés" -> Translate everything.

        
        # Sign up button/link
        if st.button("¿No tienes una cuenta? Regístrate", type="secondary", key="goto_signup", use_container_width=True):
            st.session_state['auth_mode'] = 'signup'
            st.rerun()


    st.stop()















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
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
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
    except Exception as e:
        st.error(f"Error al iniciar IA: {e}")


# --- SPOTLIGHT RESULT DISPLAY ---
if 'spotlight_query' in st.session_state and st.session_state['spotlight_query']:
    query = st.session_state['spotlight_query']
    mode = st.session_state.get('spotlight_mode', "⚡ Concepto Rápido")
    
    # Visual Container
    st.markdown(f"#### 🔍 Resultados de Búsqueda rápida: *{query}*")
    
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
                        st.success(final_res, icon="🕵🏻")
                        
                except Exception as e:
                    st.error(f"Error en Spotlight: {e}")
            
    if st.button("Cerrar búsqueda", key="close_spot"):
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
        padding-top: 0rem !important; /* LIFT LOGO (removed padding) */
    }
    
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
        margin-bottom: 1.5rem !important;
        margin-top: 1rem !important;
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
        width: 350px !important;
        min-width: 350px !important;
        max-width: 350px !important;
        flex: 0 0 350px !important; /* Strict Flex locking */
        aspect-ratio: 1 / 1.1; /* Maintain exact proportion */
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto; /* Center in column */
        overflow: hidden;
    }
    
    .green-frame img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        max-width: 100% !important;
        border-radius: 20px;
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
    
    /* Exact replica of green-frame but Purple */
    .purple-frame {
        background-color: #4B22DD;
        border-radius: 30px;
        padding: 20px;
        box-shadow: 0 15px 30px rgba(75, 34, 221, 0.25);
        width: 350px !important;
        min-width: 350px !important;
        max-width: 350px !important;
        flex: 0 0 350px !important; /* Strict Flex locking */
        aspect-ratio: 1 / 1.1; /* Maintain exact proportion */
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto; /* Center in column */
        overflow: hidden;
    }
    
    .purple-frame img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        max-width: 100% !important;
        border-radius: 20px;
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
    }

    /* --- GLOBAL HEADERS (BRANDING) --- */
    h1, h2, h3, h4, h5, h6 {
        color: #4B22DD !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Specific Streamlit markdown headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4B22DD !important;
    } 
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
        color: white !important;

    }

    /* Hover State */
    .stTabs [data-baseweb="tab-list"] button:not([role="tab"]):hover {
        background-color: #3b1aa3 !important;
    }

    /* --- SIDEBAR WIDTH CONTROL --- */
    section[data-testid="stSidebar"] {
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
        flex: 0 0 280px !important;
    }

</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    # --- 1. LOGO & USER ---
    # Left Aligned ("RAS con el resto")
    st.image("assets/logo_sidebar.png", width=180)
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True) # Spacer
    
    if st.session_state.get('user'):
        # User Info (Side-by-Side with Flexbox for tight control)
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="font-size: 24px;">👤</div>
            <div style="font-size: 14px; color: #31333F; word-break: break-all;">{st.session_state['user'].email}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Cerrar sesión", key="logout_btn", use_container_width=True):
            st.session_state['force_logout'] = True # Prevent immediate auto-login loop
            st.session_state['user'] = None
            if 'supabase_session' in st.session_state: del st.session_state['supabase_session']
            try:
                cookie_manager.delete("supabase_refresh_token")
            except Exception as e: print(f"Logout cookie error: {e}")
            import time
            time.sleep(0.5) # Allow cleanup time
            st.rerun()
    st.divider()
    
    # --- 1.5 HISTORIAL DE CLASES (MULTI-CHAT) ---
    from database import get_chat_sessions, create_chat_session, rename_chat_session, delete_chat_session

    if 'current_chat_session' not in st.session_state:
        st.session_state['current_chat_session'] = None

    with st.expander("📚 Espacios de trabajo", expanded=True):
        # Create New
        if st.button("➕ Nuevo chat", use_container_width=True):
            new_sess = create_chat_session(st.session_state['user'].id, "Nuevo chat")
            if new_sess:
                st.session_state['current_chat_session'] = new_sess
                st.session_state['tutor_chat_history'] = [] # Reset for new chat
                st.session_state['force_chat_tab'] = True # Force switch
                st.rerun()

        # List Sessions
        sessions = get_chat_sessions(st.session_state['user'].id)
        
        # Determine active ID for highlighting
        active_id = st.session_state['current_chat_session']['id'] if st.session_state['current_chat_session'] else None

        for sess in sessions:
            # Highlight active session button style could be done via key or custom CSS, 
            # for now standard buttons.
            # Truncate name to prevent fat buttons
            display_name = sess['name']
            if len(display_name) > 28:
                display_name = display_name[:25] + "..."
                
            label = f"📝 {display_name}"
            if active_id == sess['id']:
                label = f"🟢 {display_name}"
            
            if st.button(label, key=f"sess_{sess['id']}", use_container_width=True):
                st.session_state['current_chat_session'] = sess
                st.session_state['tutor_chat_history'] = [] # Force reload
                st.session_state['force_chat_tab'] = True # Force switch
                st.rerun()

        # Management for Active Session
        if st.session_state['current_chat_session']:
            st.caption("Gestionar Actual:")
            c_edit, c_del = st.columns(2)
            with c_edit:
                # Rename popover or input? simpler to use text input below for now
                 pass
            
            new_name = st.text_input("Renombrar:", value=st.session_state['current_chat_session']['name'], key="rename_chat_input")
            if new_name != st.session_state['current_chat_session']['name']:
                if st.button("Guardar nombre"):
                    rename_chat_session(st.session_state['current_chat_session']['id'], new_name)
                    st.session_state['current_chat_session']['name'] = new_name # Valid local update
                    st.rerun()
            
            if st.button("🗑️ Borrar chat", key="del_chat_btn"):
                delete_chat_session(st.session_state['current_chat_session']['id'])
                st.session_state['current_chat_session'] = None
                st.session_state['tutor_chat_history'] = []
                st.rerun()

    st.divider()

    # --- 2. SPOTLIGHT ACADÉMICO ---
    st.markdown("#### 🔍 Búsqueda rápida")
    st.caption("¿Qué buscas hoy?")
    
    # Styled Input defined in CSS
    search_query = st.text_input("Busqueda", placeholder="Ej: 'Concepto de Lead'...", label_visibility="collapsed")
    
    # Radio with custom icons workaround via emoji
    search_mode = st.radio("Modo:", ["⚡ Concepto Rápido", "🕵🏻 Análisis Profundo"], horizontal=False, label_visibility="collapsed")
    
    # Search Button (Purple Pill via CSS)
    if st.button("Buscar 🔍", key="btn_spotlight", use_container_width=True):
        if search_query:
            st.session_state['spotlight_query'] = search_query
            st.session_state['spotlight_mode'] = search_mode
            st.rerun()
    
    # --- 3. CONFIGURACIÓN PERSONAL (HIDDEN via User Request) ---
    # System uses st.secrets["GEMINI_API_KEY"] automatically via load_api_key()

    st.divider()
    
    # --- 4. ESPACIO DE TRABAJO ---
    st.markdown("#### 📂 Espacio de Trabajo")
    st.caption("Diplomado Actual:")
    
    # DB Ops
    from database import get_user_courses, create_course
    
    # GUARD: Ensure user is logged in before accessing ID
    if not st.session_state.get('user'):
        st.stop()
        
    current_user_id = st.session_state['user'].id
    db_courses = get_user_courses(current_user_id)
    course_names = [c['name'] for c in db_courses]
    course_map = {c['name']: c['id'] for c in db_courses}
    
    if not course_names: course_names = []
    if 'current_course' not in st.session_state or st.session_state['current_course'] not in course_names:
        st.session_state['current_course'] = course_names[0] if course_names else None

    options = course_names + ["➕ Crear nuevo..."]
    idx = 0
    if st.session_state['current_course'] in course_names: idx = course_names.index(st.session_state['current_course'])
    
    selected_option = st.selectbox("Diplomado", options, index=idx, label_visibility="collapsed")

    if selected_option == "➕ Crear nuevo...":
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
                if st.button("Solicitar eliminación", type="primary", key="btn_req_del"):
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
                        if st.button("✅ Sí, confirmar", type="primary", key="btn_confirm_del"):
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
    function lockSidebar() {
        const doc = window.parent.document;
        
        // 1. Force Sidebar Width
        const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.minWidth = '280px';
            sidebar.style.maxWidth = '280px';
            sidebar.style.width = '280px';
            sidebar.style.flex = '0 0 280px';
        }
        
        // 2. Hide specific resize handle if present (safer selector)
        const resizeHandle = doc.querySelector('div[class*="stSidebarResizeHandle"]');
        if (resizeHandle) {
            resizeHandle.style.display = 'none';
        }
    }

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
                background-color: #4B22DD;
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
    
    // Aggressive Loop to fight React Re-renders
    setInterval(lockSidebar, 100);
    setTimeout(lockSidebar, 500);
    
    // Run Tab Buttons
    setTimeout(addTabScrollButtons, 500);
    setTimeout(addTabScrollButtons, 1500); // Retry
    </script>
    """, height=0)

    # --- TABS DEFINITION ---
tab1, tab2, tab3, tab4, tab_lib, tab5, tab6 = st.tabs([
    "📹 Transcriptor", 
    "📝 Apuntes Simples", 
    "🗺️ Guía de Estudio", 
    "🧠 Zona Quiz",
    "📂 Biblioteca",
    "👩🏻‍🏫 Ayudante de Tareas",
    "📚 Tutoría 1 a 1"
])

# --- AUTO-SWITCH TAB LOGIC ---
if st.session_state.get('force_chat_tab'):
    # Inject JS to click the tab
    st.components.v1.html("""
    <script>
        try {
            const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
            for (const tab of tabs) {
                if (tab.innerText.includes("Tutoría 1 a 1")) {
                    tab.click();
                    break;
                }
            }
        } catch(e) { console.log(e); }
    </script>
    """, height=0)
    # Reset flag so it doesn't keep clicking
    st.session_state['force_chat_tab'] = False

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
        # Image Display (Dynamic Update)
        import base64
        img_path = "assets/transcriptor_header_v2.jpg"
        img_b64 = ""
        if os.path.exists(img_path):
            with open(img_path, "rb") as image_file:
                img_b64 = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f'''
            <div class="green-frame" style="padding: 20px;">
                <img src="data:image/jpeg;base64,{img_b64}" style="width: 100%; border-radius: 15px; object-fit: cover;">
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
            if st.button("Iniciar transcripción", key="btn1", use_container_width=True):
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
        # Image Display (Dynamic Update)
        import base64
        img_b64_notes = ""
        img_path_notes = "assets/notes_header.jpg"
        if os.path.exists(img_path_notes):
            with open(img_path_notes, "rb") as image_file:
                img_b64_notes = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f'''
            <div class="purple-frame" style="padding: 20px;">
                <img src="data:image/jpeg;base64,{img_b64_notes}" style="width: 100%; border-radius: 15px; object-fit: cover;">
            </div>
        ''', unsafe_allow_html=True)
         
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
                
                if selected_file and st.button("Generar apuntes", key="btn2"):
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
        # Image Display (Dynamic Update)
        import base64
        img_b64_guide = ""
        img_path_guide = "assets/study_guide_header.jpg"
        if os.path.exists(img_path_guide):
            with open(img_path_guide, "rb") as image_file:
                img_b64_guide = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f'''
            <div class="green-frame" style="padding: 20px;">
                <img src="data:image/jpeg;base64,{img_b64_guide}" style="width: 100%; border-radius: 15px; object-fit: cover;">
            </div>
        ''', unsafe_allow_html=True)
    
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
        # Image Display (Dynamic Update)
        import base64
        img_b64_quiz = ""
        img_path_quiz = "assets/quiz_helper_header.jpg"
        if os.path.exists(img_path_quiz):
            with open(img_path_quiz, "rb") as image_file:
                img_b64_quiz = base64.b64encode(image_file.read()).decode()
        
        st.markdown(f'''
            <div class="purple-frame" style="padding: 20px;">
                <img src="data:image/jpeg;base64,{img_b64_quiz}" style="width: 100%; border-radius: 15px; object-fit: cover;">
            </div>
        ''', unsafe_allow_html=True)
        
    with col_text:
        tab4_html = (
            '<div class="card-text">'
            '<h2 style="margin-top:0;">4. Zona Quiz</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">Sube tus preguntas y obtén orientación inmediata</p>'
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

            # Text Input Option
            input_text_quiz = st.text_area("✍🏻 O escribe tu pregunta aquí directamente:", height=100, placeholder="Ej: ¿Cuál es la capital de Francia? a) París b) Roma...", key=f"q_txt_{st.session_state['quiz_key']}")

            img_files = st.file_uploader("O sube archivos manualmente:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"up4_{st.session_state['quiz_key']}")
        
        # COMBINE INPUTS
        has_text = bool(input_text_quiz.strip())
        total_items = (len(img_files) if img_files else 0) + len(st.session_state['pasted_images']) + (1 if has_text else 0)

        if total_items > 0 and st.button("Resolver Preguntas", key="btn4"):
            progress_bar = st.progress(0)
            status = st.empty()
            results = [] 
            
            # 1. Process Queue
            items_to_process = []
            
            # Add Text Item if exists
            if has_text:
                items_to_process.append({"type": "text", "obj": input_text_quiz, "name": "Pregunta de Texto"})

            # Add Uploaded Files
            if img_files:
                for f in img_files:
                    items_to_process.append({"type": "upload", "obj": f, "name": f.name})
            
            # Add Pasted Images
            for i, p_img in enumerate(st.session_state['pasted_images']):
                 items_to_process.append({"type": "paste", "obj": p_img, "name": f"Captura_Pegada_{i+1}.png"})

            for i, item in enumerate(items_to_process):
                # Calculate percentages
                current_percent = int((i / len(items_to_process)) * 100)
                status.markdown(f"**Analizando item {i+1} de {len(items_to_process)}... ({current_percent}%)**")
                progress_bar.progress(i / len(items_to_process))
                
                try:
                    full_answer = ""
                    disp_img = None
                    
                    if item["type"] == "text":
                         # Text Only
                         full_answer = assistant.solve_quiz(question_text=item["obj"], global_context=gl_ctx)
                         disp_img = None
                    
                    else:
                        # Image Processing
                        temp_img_path = f"temp_quiz_{i}.png"
                        if item["type"] == "upload":
                            with open(temp_img_path, "wb") as f: f.write(item["obj"].getbuffer())
                        else:
                            item["obj"].save(temp_img_path, format="PNG")
                        
                        # Load for display
                        disp_img = Image.open(temp_img_path).copy()
                        
                        # Solve with Image
                        full_answer = assistant.solve_quiz(image_path=temp_img_path, global_context=gl_ctx)
                        
                        # Cleanup Temp
                        if os.path.exists(temp_img_path):
                             try: os.remove(temp_img_path)
                             except: pass

                    # Robust Regex Parsing for Short Answer
                    import re
                    short_answer = "Respuesta no detectada (Ver detalle)"
                    match = re.search(r"\*\*Respuesta Correcta:?\*\*?\s*(.*)", full_answer, re.IGNORECASE)
                    if match:
                         short_answer = match.group(1).strip()
                    
                    results.append({"name": item["name"], "full": full_answer, "short": short_answer, "img_obj": disp_img})
                
                except Exception as e:
                    results.append({"name": item["name"], "full": f"Error: {e}", "short": "Error", "img_obj": None})
                
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
        '<h2 style="margin-top:0;">5. Ayudante de Tareas</h2>'
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
        arg_mode = st.toggle("💬 Activar Modo Argumentador", key="arg_mode_toggle", help="Activa un análisis profundo con 4 dimensiones: Respuesta, Fuentes, Paso a Paso y Contra-argumento.")
        
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
                     if st.button("📄 Copiar respuesta", key="cp_arg_resp"):
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
            if st.button("🗣️ Debatir esta respuesta con el profesor (Ir a tutoría)", key="btn_bridge_tutor", help="Crea un nuevo chat, envía esta tarea y te redirige para discutirla."):
                # 1. Prepare Content
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

                # 2. Database Integration
                from database import create_chat_session, save_chat_message
                import datetime
                
                # Create New Session
                # Name it based on task or timestamp
                sess_name = f"Debate Tarea: {task_prompt[:20]}..." if task_prompt else "Debate Tarea"
                new_sess = create_chat_session(st.session_state['user'].id, sess_name)
                
                if new_sess:
                    # Set as Active
                    st.session_state['current_chat_session'] = new_sess
                    st.session_state['tutor_chat_history'] = [] # Reset local
                    
                    # 3. Save User Message
                    save_chat_message(new_sess['id'], "user", bridge_msg)
                    st.session_state['tutor_chat_history'].append({"role": "user", "content": bridge_msg})
                    
                    # 4. Generate Response (with Spinner)
                    # Prepare Context (Global)
                    gl_ctx_bridge, _ = get_global_context()
                    
                    with st.spinner("El profesor está leyendo tu tarea y creando el chat..."):
                        try:
                            response_bridge = assistant.chat_tutor(
                                bridge_msg, 
                                chat_history=st.session_state['tutor_chat_history'], 
                                context_files=[], 
                                global_context=gl_ctx_bridge
                            )
                            
                            # 5. Save Assistant Response
                            save_chat_message(new_sess['id'], "assistant", response_bridge)
                            st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response_bridge})
                            
                            st.success("✅ Chat creado. Redirigiendo...")
                            
                            # 6. FORCE REDIRECT
                            st.session_state['force_chat_tab'] = True
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error generando respuesta: {e}")
                else:
                    st.error("No se pudo crear la sesión de chat.")

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
    
    # --- FETCH MESSAGES FROM DB IF SESSION ACTIVE ---
    from database import get_chat_messages, save_chat_message
    
    current_sess = st.session_state.get('current_chat_session')
    
    if not current_sess:
        st.warning("👈 Por favor, **inicia un nuevo chat** o selecciona uno existente en la barra lateral para comenzar.")
        st.image("https://media.giphy.com/media/l0HlHFRbmaZtBRhXG/giphy.gif", width=300) # Optional fun placeholder
    else:
        # Load History from DB (Sync)
        # We re-fetch to ensure we have the latest state relative to DB
        # Optimization: Could check if len mismatch, but fetching is safer for consistency.
        db_msgs = get_chat_messages(current_sess['id'])
        # Convert DB format to Chat format if needed (DB: role, content. Chat: role, content. Match!)
        st.session_state['tutor_chat_history'] = db_msgs
        
        col_chat, col_info = st.columns([2, 1], gap="large")
        
        with col_info:
            st.info(f"📝 **Clase Actual:** {current_sess['name']}")
            st.caption("El profesor recuerda todo lo hablado en esta clase.")
            st.divider()
            st.markdown("### 📎 Adjunto rápido")
            tutor_file = st.file_uploader("Subir archivo al chat", type=['pdf', 'txt', 'png', 'jpg'], key="tutor_up")
            
            if st.button("🗑️ Limpiar pantalla", key="clear_chat"):
                 # This only clears screen, to delete history use delete session
                 # But maybe we want a 'Clear Messages' function?
                 # For now, just reset local state, but DB remains? 
                 # User asked for "create different chats".
                 pass

        with col_chat:
            # Display Chat History
            for msg in st.session_state['tutor_chat_history']:
                with st.chat_message(msg['role']):
                    st.markdown(msg['content'])
            
            # User Input
            if prompt := st.chat_input(f"Pregunta sobre {current_sess['name']}..."):
                # 1. Add User Message
                # Save to DB FIRST
                save_chat_message(current_sess['id'], "user", prompt)
                
                # Update UI State
                st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                    
                # 2. Prepare Context (Global + Upload)
                # GUARD: Check assistant
                if not assistant:
                    st.error("⚠️ Error: El asistente no se ha iniciado correctamente. revisa tu API Key.")
                    st.stop()

                gl_ctx, _ = get_global_context()
                
                chat_files = []
                if tutor_file:
                    try:
                        content = ""
                        if tutor_file.type == "application/pdf":
                            content = assistant.extract_text_from_pdf(tutor_file.getvalue(), tutor_file.type)
                        else:
                            try:
                               content = tutor_file.getvalue().decode("utf-8", errors='ignore')
                            except:
                               content = "Archivo binario no procesado."
                        
                        chat_files.append({"name": tutor_file.name, "content": content})
                        st.toast(f"📎 Archivo {tutor_file.name} enviado.")
                    except Exception as e:
                        st.error(f"Error leyendo archivo: {e}")

                # 3. Generate Response
                with st.chat_message("assistant"):
                    with st.spinner("El profesor está pensando..."):
                        response = assistant.chat_tutor(
                            prompt, 
                            chat_history=st.session_state['tutor_chat_history'], # Pass full history including just added user msg
                            context_files=chat_files, 
                            global_context=gl_ctx
                        )
                        st.markdown(response)
                
                # 4. Save Response to DB
                save_chat_message(current_sess['id'], "assistant", response) # Using 'assistant' to match Streamlit, map to 'model' in DB if needed? 
                # DB schema has 'role'. Streamlit uses 'assistant'. Gemini uses 'model'.
                # Let's standardize: If database.py expects 'model', I should send 'model'.
                # But my database.py save function just inserts the string.
                # Standard practice: UI = 'assistant', DB/Model = 'model'.
                # I'll save as 'assistant' to keep UI simple, or map it.
                # Let's simple save as 'assistant' for now since `chat_tutor` handles the conversion for Gemini.
                
                st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response})

# Force Reload Triggered
