
import streamlit as st
import os
import glob
import uuid
from transcriber import Transcriber
from study_assistant import StudyAssistant
from PIL import Image, ImageGrab
import shutil
import time
import datetime
import extra_streamlit_components as stx  # --- PERSISTENCE ---
from library_ui import render_library # --- LIBRARY UI ---
from database import (
    get_user_courses, create_course, delete_course, rename_course, 
    get_chat_sessions, create_chat_session, rename_chat_session, delete_chat_session, 
    get_dashboard_stats, update_user_nickname, get_recent_chats, check_and_update_streak, 
    update_user_footprint, init_supabase, update_last_course
)


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
    @st.cache_data
    def get_b64_image(image_path):
        try:
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        except:
            return "" # Return empty string on error to prevent crash
        return ""

    logo_b64 = get_b64_image("assets/logo_main.png")
    hero_b64 = get_b64_image("assets/messimo_hero_new.png") # Updated to user provided PNG

    # --- CUSTOM CSS FOR FULL BACKGROUND MESSIMO STYLE ---
    
    # 1. STATIC STYLES (WhatsApp Chat & Layout) - No f-string risk
    st.markdown("""
        <style>
        /* WHATSAPP CHAT STYLES */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-bottom: 50px;
        }
        .chat-row {
            display: flex;
            width: 100%;
            margin-bottom: 5px;
        }
        .row-reverse {
            flex-direction: row-reverse;
        }
        .chat-bubble {
            padding: 10px 14px;
            border-radius: 10px;
            max-width: 75%;
            word-wrap: break-word;
            font-size: 16px;
            line-height: 1.5;
            position: relative;
            box-shadow: 0 1px 1px rgba(0,0,0,0.1);
            font-family: inherit;
        }
        .chat-bubble p {
            margin: 0;
        }
        .user-bubble {
            background-color: #d9fdd3; /* WhatsApp Light Green */
            color: #111;
            border-top-right-radius: 0;
        }
        .assistant-bubble {
            background-color: #ffffff;
            color: #111;
            border-top-left-radius: 0;
            border: 1px solid #eee;
        }
        /* Code blocks in bubbles */
        .chat-bubble pre {
            background: #f0f0f0;
            padding: 5px;
            border-radius: 5px;
            overflow-x: auto;
        }
        
        /* HIDE SCROLLBAR */
        ::-webkit-scrollbar {
            width: 0px;
            background: transparent;
        }
        
        /* RESTORE SCROLL ON CONTAINERS */
        section[data-testid="stAppViewContainer"] {
            overflow-y: auto !important;
        }
        
        /* LOGIN CARD & ALIGNMENT */
        .main .block-container {
            padding-top: 0rem !important; 
            transform: translateY(-50px) !important;
            padding-bottom: 0vh !important;
            max_width: 1200px !important;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            min-height: 10vh;
        }
        .login-card {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            padding: 50px 40px; 
            border-radius: 40px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 0px !important; 
            height: auto;
            border: 1px solid rgba(0,0,0,0.05);
        }
        .stTextInput > div > div > input {
            border-radius: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. DYNAMIC STYLES (Hero Background) - Using f-string for variable
    st.markdown(f'''
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{hero_b64}");
            background-size: cover; /* Changed to cover for better fit */
            background-position: center;
            background-repeat: no-repeat;
        }}

        
        /* HIDE SCROLLBAR (Optional, keeping getting rid of ugly bars but allowing scroll) */
        ::-webkit-scrollbar {{
            width: 0px;
            background: transparent;
        }}
        
        /* LOCK MAIN STREAMLIT CONTAINER REMOVED */
        section[data-testid="stAppViewContainer"] {{
            overflow-y: auto !important; /* ALLOW SCROLL */
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

        /* GLOBAL SCROLL KILLER REMOVED */
        
        /* 3. LOGIN CARD CONTAINER (Theme Aware) */
        .login-card {{
            background-color: var(--secondary-background-color);
            color: var(--text-color);
            padding: 50px 40px; 
            border-radius: 40px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 0px !important; 
            height: auto;
            border: 1px solid rgba(0,0,0,0.05); /* Subtle border for better definition */
        }}

        /* 4. PILL INPUTS (Theme Aware) */
        .stTextInput > div > div > input {{
            border-radius: 50px !important;
            border: 1px solid var(--secondary-background-color); 
            padding: 0px 25px; 
            background-color: var(--background-color);
            color: var(--text-color);
            height: 55px; 
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

        # FORM INPUTS (Wrapped in st.form to prevent jitter/refresh while typing)
        with st.form("login_form", clear_on_submit=False, border=False):
            # Hack to remove default form padding if needed, but border=False helps.
            email = st.text_input("Correo electrónico", key="login_email", placeholder="Correo electrónico", label_visibility="collapsed")
            password = st.text_input("Contraseña", type="password", key="login_pass", placeholder="Contraseña", label_visibility="collapsed")
            
            # Submit Button (Primary)
            submitted = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)
            
            if submitted:
                if email and password:
                    from database import sign_in
                    user = sign_in(email, password)
                    if user:
                        st.session_state['user'] = user
                        
                        # Try to set cookie
                        if 'supabase_session' in st.session_state:
                             try:
                                 sess = st.session_state['supabase_session']
                                 # Calculate expiry (e.g. 7 days)
                                 exp_date = datetime.datetime.now() + datetime.timedelta(days=7)
                                 # Set Keep Logged In
                                 cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=exp_date)
                                 print(f"Cookie set for user: {user.email}")
                                 time.sleep(2) # CRITICAL: Wait for frontend to set cookie
                             except Exception as e:
                                 print(f"Cookie set error: {e}")
                                 
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
                else:
                    st.warning("Por favor ingresa correo y contraseña.")


        
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
    @st.cache_data
    def load_logo_cached():
        if os.path.exists("assets/logo_sidebar.png"):
            return Image.open("assets/logo_sidebar.png")
        return None

    logo_img = load_logo_cached()
    if logo_img:
        st.image(logo_img, width=180)
    else:
        st.markdown("### 🎓 E-Education")
    
    st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True) # Spacer

    if st.session_state.get('user'):
        # User Info (Side-by-Side with Flexbox for tight control)
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <div style="font-size: 24px;">👤</div>
            <div style="font-size: 14px; color: #31333F; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{st.session_state['user'].email}">
                {st.session_state['user'].email}
            </div>
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
    # from database import ... (Moved to top)

    if 'current_chat_session' not in st.session_state:
        st.session_state['current_chat_session'] = None

    with st.expander("🗂️ Historial de Chats", expanded=True):
        # Create New
        if st.button("➕ Nuevo chat", use_container_width=True):
            new_sess = create_chat_session(st.session_state['user'].id, "Nuevo chat")
            if new_sess:
                st.session_state['current_chat_session'] = new_sess
                st.session_state['tutor_chat_history'] = [] # Reset for new chat
                st.session_state['redirect_target_name'] = "Tutoría 1 a 1" # Explicit Redirect
                st.session_state['force_chat_tab'] = True # Force switch
                st.rerun()

        # List Sessions
        sessions = get_chat_sessions(st.session_state['user'].id)
        
        # Determine active ID for highlighting
        active_id = st.session_state['current_chat_session']['id'] if st.session_state['current_chat_session'] else None

        # LIMIT TO TOP 1 (Minimalist)
        visible_sessions = sessions[:1]
        
        for sess in visible_sessions:
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
                st.session_state['redirect_target_name'] = "Tutoría 1 a 1" # Explicit Redirect
                st.session_state['force_chat_tab'] = True # Force switch
                
                # TRACK FOOTPRINT
                update_user_footprint(st.session_state['user'].id, {
                    "type": "chat",
                    "title": sess['name'],
                    "target_id": sess['id'],
                    "subtitle": "Continuar conversación"
                })
                
                st.rerun()

        # VIEW ALL BUTTON ALWAYS VISIBLE
        if True:
            st.write("")
            if st.button("📂 Ver todo el historial...", help="Ir al panel de gestión completo", use_container_width=True):
                st.session_state['redirect_target_name'] = "Inicio"
                st.session_state['force_chat_tab'] = True
                st.session_state['dashboard_mode'] = 'history' # Activate History View in Dashboard
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
                # Save immediately on change (Enter)
                rename_chat_session(st.session_state['current_chat_session']['id'], new_name)
                st.session_state['current_chat_session']['name'] = new_name # Valid local update
                st.rerun()
            
            if st.button("🗑️ Borrar chat", key="del_chat_btn"):
                delete_chat_session(st.session_state['current_chat_session']['id'])
                st.session_state['current_chat_session'] = None
                st.session_state['tutor_chat_history'] = []
                st.rerun()

        # --- BULK DELETE (GESTIÓN MASIVA) ---
        st.write("")
        with st.expander("🗑️ Gestión Masiva", expanded=False):
            # 1. Multi-Select with Invisible Uniqueness Hack
            # User wants clean names, but Streamlit merges duplicates.
            # Solution: Append zero-width spaces to duplicates.
            
            valid_sessions = [s for s in sessions if s and 'name' in s]
            
            # Pre-calc unique labels
            name_counts = {}
            processed_sessions = []
            for s in valid_sessions:
                original_name = s['name']
                count = name_counts.get(original_name, 0)
                # Append invisible characters equal to the count count
                invisible_suffix = "\u200b" * count
                s['unique_label'] = f"{original_name}{invisible_suffix}"
                processed_sessions.append(s)
                name_counts[original_name] = count + 1

            sel_sessions = st.multiselect(
                "Seleccionar chats:", 
                options=processed_sessions,
                format_func=lambda x: x['unique_label'],
                key="bulk_chat_select",
                placeholder="Elige para borrar..."
            )
            
            if sel_sessions:
                if st.button(f"Eliminar {len(sel_sessions)} chats", type="primary", use_container_width=True):
                    success_count = 0
                    deleted_ids = []
                    for s in sel_sessions:
                        if delete_chat_session(s['id']):
                            success_count += 1
                            deleted_ids.append(s['id'])
                    
                    if success_count > 0:
                        st.success(f"¡{success_count} chats borrados!")
                        
                        # Reset current if deleted
                        curr = st.session_state.get('current_chat_session')
                        if curr and curr['id'] in deleted_ids:
                             st.session_state['current_chat_session'] = None
                             st.session_state['tutor_chat_history'] = []
                        
                        time.sleep(0.5)
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
    # (Reload Trigger)
    
    # --- 4. ESPACIO DE TRABAJO ---
    st.markdown("#### 📂 Espacio de Trabajo")
    st.caption("Diplomado Actual:")
    
    # DB Ops
    # from database import ... (Moved to top)
    
    # GUARD: Ensure user is logged in before accessing ID
    if not st.session_state.get('user'):
        st.stop()
        
    current_user_id = st.session_state['user'].id
    db_courses = get_user_courses(current_user_id)
    course_names = [c['name'] for c in db_courses]
    course_map = {c['name']: c['id'] for c in db_courses}
    
    if not course_names: course_names = []
    if not course_names: course_names = []
    
    # RECOVERY LOGIC (Persistence)
    if 'current_course' not in st.session_state or (st.session_state['current_course'] not in course_names and st.session_state['current_course'] is not None):
        # Try metadata first
        saved_course = st.session_state['user'].user_metadata.get('last_course_name')
        if saved_course and saved_course in course_names:
             st.session_state['current_course'] = saved_course
        else:
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
        
        # PERSIST SELECTION
        update_last_course(selected_option)
        
        # --- RESTORED ACTIONS (RENAME / DELETE) ---
        st.write("") # Micro spacer
        
        # RENAME
        with st.expander("✏️ Renombrar"):
            rename_input = st.text_input("Nuevo nombre:", value=st.session_state['current_course'], key="rename_input_sb")
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
            // Style the tabList for scroll - FORCE OVERRIDE GLOBAL CSS
            tabList.style.setProperty('overflow-x', 'auto', 'important');
            tabList.style.setProperty('overflow-y', 'hidden', 'important');
            tabList.style.setProperty('white-space', 'nowrap', 'important');
            tabList.style.scrollBehavior = 'smooth';
            tabList.style.scrollbarWidth = 'none'; // Hide scrollbar
            
            // Create Left Button
            const btnLeft = doc.createElement('button');
            btnLeft.id = 'tab-scroll-left';
            btnLeft.innerHTML = '◀';
            btnLeft.onclick = (e) => {
                e.preventDefault();
                tabList.scrollBy({left: -200, behavior: 'smooth'});
            };
            
            // Create Right Button
            const btnRight = doc.createElement('button');
            btnRight.id = 'tab-scroll-right';
            btnRight.innerHTML = '▶';
            btnRight.onclick = (e) => {
                 e.preventDefault();
                 tabList.scrollBy({left: 200, behavior: 'smooth'});
            };
            
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
# --- TABS DEFINITION ---
# NEW: "Inicio" is the Dashboard Tab
tab_home, tab1, tab2, tab3, tab4, tab_lib, tab5, tab6 = st.tabs([
    "🏠 Inicio",
    "📹 Transcriptor", 
    "📝 Apuntes Simples", 
    "🗺️ Guía de Estudio", 
    "🧠 Zona Quiz",
    "📂 Biblioteca",
    "👩🏻‍🏫 Ayudante de Tareas",
    "📚 Tutoría 1 a 1"
])

import pandas as pd # FIX: Missing import for charts

# --- DASHBOARD TAB (HOME) ---
with tab_home:
    # Load Stats
    current_c_id = st.session_state.get('current_course_id')
    current_c_name = st.session_state.get('current_course', 'General')
    
    # --- NICKNAME LOGIC ---
    # 1. Try to load from User Metadata (Persistent)
    current_user = st.session_state['user']
    meta_nick = current_user.user_metadata.get('nickname') if current_user.user_metadata else None
    
    if 'user_nickname' not in st.session_state:
        # Priority: Metadata > Email
        if meta_nick:
            st.session_state['user_nickname'] = meta_nick
        else:
            st.session_state['user_nickname'] = current_user.email.split('@')[0].capitalize()
        
    # Header with Edit Button
    h_col1, h_col2 = st.columns([0.8, 0.2], vertical_alignment="center")
    with h_col1:
        st.markdown(f"## ¡Hola, {st.session_state['user_nickname']}! 👋🏻")
    with h_col2:
        with st.popover("✏️", help="Editar tu apodo"):
            new_nick = st.text_input("¿Cómo quieres que te llame?", value=st.session_state['user_nickname'])
            if new_nick != st.session_state['user_nickname']:
                 # SAVE TO DB
                 updated_user = update_user_nickname(new_nick)
                 if updated_user:
                     st.session_state['user'] = updated_user # Update session user to keep metadata fresh
                     st.session_state['user_nickname'] = new_nick
                     st.rerun()

    st.markdown(f"Estás estudiando: **{current_c_name}**")
    
    # --- DAILY QUOTE ---
    import random
    from datetime import datetime
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    random.seed(today_str) # Seed with date for consistency
    quotes = [
        "“La educación es el arma más poderosa que puedes usar para cambiar el mundo.” – Nelson Mandela",
        "“Cree en ti mismo y en lo que eres.” – Christian D. Larson",
        "“El éxito es la suma de pequeños esfuerzos repetidos día tras día.” – Robert Collier",
        "“No cuentes los días, haz que los días cuenten.” – Muhammad Ali",
        "“Lo único imposible es aquello que no intentas.”",
        "“La disciplina es el puente entre metas y logros.” – Jim Rohn",
        "“Aprender es como remar contra corriente: en cuanto se deja, se retrocede.” – Edward Benjamin Britten",
        "“Tu actitud, no tu aptitud, determinará tu altitud.” – Zig Ziglar",
        "“Si puedes soñarlo, puedes hacerlo.” – Walt Disney",
        "“El futuro pertenece a aquellos que creen en la belleza de sus sueños.” – Eleanor Roosevelt"
    ]
    daily_quote = random.choice(quotes)
    st.info(f"💡 **Frase del Día:** {daily_quote}")
    
    st.write("")
    
    st.write("")
    
    # --- DASHBOARD MODE CONTROLLER ---
    dash_mode = st.session_state.get('dashboard_mode', 'standard')
    
    if dash_mode == 'history':
        # --- FULL HISTORY VIEW ---
        c_h1, c_h2 = st.columns([0.8, 0.2])
        c_h1.markdown("### 📚 Historial Completo")
        if c_h2.button("🔙 Volver"):
            st.session_state['dashboard_mode'] = 'standard'
            st.rerun()
            
        # Search
        q_hist = st.text_input("🔍 Buscar en historial...", placeholder="Nombre del chat...")
        
        # Get All Chats
        all_chats = get_chat_sessions(st.session_state['user'].id)
        if q_hist:
            all_chats = [c for c in all_chats if q_hist.lower() in c['name'].lower()]
            
        # --- BULK DELETE IN DASHBOARD ---
        if all_chats:
            with st.expander("🗑️ Gestión Masiva (Eliminar)", expanded=False):
                # Unique Keys Logic
                sess_opts = []
                name_map = {}
                for s in all_chats:
                    raw_n = s['name']
                    count = name_map.get(raw_n, 0)
                    suffix = "\u200b" * count
                    label = f"{raw_n}{suffix}"
                    s['_label'] = label
                    sess_opts.append(s)
                    name_map[raw_n] = count + 1
                
                sel_del = st.multiselect("Seleccionar para borrar:", sess_opts, format_func=lambda x: x['_label'], key="dash_bulk_del")
                if sel_del:
                    st.warning(f"¿Estás seguro de borrar {len(sel_del)} conversaciones?")
                    if st.button("Sí, borrar definitivamente", key="btn_conf_dash_del"):
                        succ = 0
                        ids_del = []
                        for d in sel_del:
                            if delete_chat_session(d['id']):
                                succ += 1
                                ids_del.append(d['id'])
                        
                        if succ > 0:
                            st.success(f"Se eliminaron {succ} chats.")
                            # Check active
                            curr_s = st.session_state.get('current_chat_session')
                            if curr_s and curr_s['id'] in ids_del:
                                st.session_state['current_chat_session'] = None
                                st.session_state['tutor_chat_history'] = []
                            time.sleep(1)
                            st.rerun()
            
        if all_chats:
            h_cols = st.columns(3)
            for i, chat in enumerate(all_chats):
                with h_cols[i % 3]:
                    date_str = chat['created_at'].split('T')[0]
                    if st.button(f"📝 {chat['name']}\n\n📅 {date_str}", key=f"hist_all_{chat['id']}", use_container_width=True):
                        st.session_state['current_chat_session'] = chat
                        st.session_state['tutor_chat_history'] = [] 
                        st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                        st.session_state['force_chat_tab'] = True
                        st.rerun()
        else:
            st.warning("No se encontraron chats.")
            
    elif current_c_id:
        # --- STANDARD DASHBOARD VIEW ---
        stats = get_dashboard_stats(current_c_id, st.session_state['user'].id)
        
        # Calculate Real Streak
        streak = check_and_update_streak(st.session_state['user'])
        
        # Gamification Messages
        streak_msg = "¡Sigue así!"
        if streak >= 3: streak_msg = "🔥 ¡Estás en llamas!"
        if streak >= 7: streak_msg = "👑 ¡Leyenda!"
        
        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("📚 Archivos", stats['files'], delta="Recursos totales")
        m2.metric("💬 Sesiones", stats['chats'], delta="Conversaciones")
        m3.metric("🔥 Racha", f"{streak} Día{'s' if streak != 1 else ''}", delta=streak_msg)
        
        st.divider()
        
        # Visuals Row
        d1, d2 = st.columns([0.6, 0.4])
        
        with d1:
            st.markdown("##### 📊 Tu Biblioteca")
            # Simple Bar Chart of File Types
            chart_data = pd.DataFrame.from_dict(stats['file_types'], orient='index', columns=['Cantidad'])
            st.bar_chart(chart_data)
            
        with d2:
            st.markdown("##### 🚀 Acciones Rápidas")
            st.write("")
            if st.button("📂 Ir a Biblioteca", use_container_width=True):
                st.session_state['redirect_target_name'] = "Biblioteca"
                st.session_state['force_chat_tab'] = True 
                st.rerun()
            
            st.write("")
            if st.button("➕ Subir Archivo Nuevo", use_container_width=True):
                st.session_state['redirect_target_name'] = "Biblioteca"
                st.session_state['force_chat_tab'] = True
                st.session_state['lib_auto_open_upload'] = True
                st.rerun()
        
        st.divider()
        
        st.divider()
        
        # --- SMART CONTINUITY CARD ---
        st.markdown("##### 🕰️ Continuar donde lo dejaste")
        
        # Load Footprint
        curr_user = st.session_state['user']
        footprint = curr_user.user_metadata.get('smart_footprint') if curr_user.user_metadata else None
        
        # Helper to render the card
        def render_smart_card(icon, title, subtitle, btn_label, on_click_fn):
             # Styled Container
             with st.container(border=True):
                 c_icon, c_info, c_btn = st.columns([0.15, 0.65, 0.2])
                 with c_icon:
                     st.markdown(f"<div style='font-size: 30px; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
                 with c_info:
                     st.markdown(f"**{title}**")
                     st.caption(subtitle)
                 with c_btn:
                     st.write("") # Spacer
                     if st.button(btn_label, use_container_width=True, type="primary"):
                         on_click_fn()
                         st.rerun()

        if footprint:
             ftype = footprint.get('type')
             ftitle = footprint.get('title', 'Actividad Reciente')
             fsub = footprint.get('subtitle', 'Retomar actividad')
             ftarget = footprint.get('target_id')
             
             if ftype == 'chat':
                 def go_chat():
                     # Re-fetch session data (mock object minimal)
                     # ideally fetch full object, but for now ID and Name is enough for current_chat_session logic 
                     # if app relies on full object properties, we might need a fetch.
                     # Assuming app just needs id/name.
                     st.session_state['current_chat_session'] = {'id': ftarget, 'name': ftitle}
                     st.session_state['tutor_chat_history'] = []
                     st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                     st.session_state['force_chat_tab'] = True
                 
                 render_smart_card("💬", f"Chat: {ftitle}", "Estabas conversando con tu asistente", "Retomar Chat", go_chat)
                 
             elif ftype == 'unit':
                 def go_unit():
                     st.session_state['redirect_target_name'] = "Biblioteca"
                     st.session_state['force_chat_tab'] = True
                     st.session_state['lib_current_unit_id'] = ftarget
                     st.session_state['lib_current_unit_name'] = ftitle
                     # Breadcrumbs might be tricky to reconstruct perfectly without query, 
                     # but we can set simple path
                     st.session_state['lib_breadcrumbs'] = [{'id': ftarget, 'name': ftitle}]
                     
                 render_smart_card("📂", f"Carpeta: {ftitle}", "Estabas explorando archivos aquí", "Ir a Carpeta", go_unit)
                 
             else:
                 # Fallback for unknown types
                 st.info(f"Última actividad: {ftitle}")
                 
        else:
             # Fallback to Recents if no footprint (First run)
             st.info("Explora la app para generar tu tarjeta de viaje. 🚀")
             recent_chats = get_recent_chats(st.session_state['user'].id, limit=3) # Keep fallback just in case
             if recent_chats:
                chat = recent_chats[0]
                if st.button(f"📝 Último chat: {chat['name']}", key="fallback_rec"):
                        st.session_state['current_chat_session'] = chat
                        st.session_state['tutor_chat_history'] = [] 
                        st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                        st.session_state['force_chat_tab'] = True
                        st.rerun()

    else:
        st.info("Selecciona o crea un Diplomado en la barra lateral para ver tus estadísticas.")

# --- AUTO-SWITCH TAB LOGIC ---
if st.session_state.get('force_chat_tab'):
    # Inject JS to click the tab
    # timestamp ensures the component sends a new message to frontend even if target is same
    import time
    ts = time.time()
    st.components.v1.html(f"""
    <script>
        setTimeout(() => {{
            try {{
                const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
                const targetName = "{st.session_state.get('redirect_target_name', 'Ayudante de Tareas')}"; 
                for (const tab of tabs) {{
                    if (tab.innerText.includes(targetName)) {{
                        tab.click();
                        break;
                    }}
                }}
            }} catch(e) {{ console.log(e); }}
        }}, 100);
        // {ts}
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

# --- BATCH SYSTEM FOLDER CHECK (Prevention of "Popping" folders) ---
if st.session_state.get('current_course_id'):
    c_id_check = st.session_state['current_course_id']
    from database import get_units, create_unit
    
    # Check what exists BEFORE rendering tabs
    existing_units = get_units(c_id_check)
    existing_names = [u['name'] for u in existing_units]
    
    
    # CONSULTANT FIX: ONLY CREATE DEFAULTS IF COURSE IS EMPTY
    # If the user has deleted specific folders, we should NOT recreate them ("Zombie Folders").
    # But if the course is BRAND NEW (no units), we initialize the structure.
    required_folders = ["Transcriptor - Videos", "Transcriptor - Audios", "Apuntes Simples", "Guía de Estudio"]
    created_any_batch = False
    
    if not existing_units: # Only runs if 0 folders exist
        for req in required_folders:
             create_unit(c_id_check, req)
             created_any_batch = True
    
    # If we created anything new, RERUN ONCE to refresh all subsequent 'get_units' calls
    if created_any_batch:
        st.session_state['force_rerun_batch'] = True # Optional flag if needed
        st.rerun()

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
            <h2 class="transcriptor-title">1. Transcriptor de Audio y Video</h2>
            <p class="transcriptor-subtitle">
                Sube videos o audios para procesarlos y clasificarlos automáticamente.<br>
                <span style="font-size: 0.9rem; color: #888; font-weight: 500;">Soporta: MP4, MOV, MP3, WAV, M4A</span>
            </p>
        ''', unsafe_allow_html=True)
        
        # Dynamic Key for Uploader Reset
        if 'transcriptor_key' not in st.session_state: st.session_state['transcriptor_key'] = "up1"
        
        # File Uploader
        # Added .waptt (WhatsApp), .opus, .aac, .wma
        uploaded_files = st.file_uploader("Upload", type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav', 'm4a', 'flac', 'ogg', 'opus', 'waptt', 'aac', 'wma'], accept_multiple_files=True, key=st.session_state['transcriptor_key'], label_visibility="collapsed")
        
        if uploaded_files:
            # --- FOLDER SELECTION ---
            c_id = st.session_state.get('current_course_id')
            selected_unit_id = None
            
            if c_id:
                from database import get_units, create_unit, upload_file_to_db, get_files
                # RECURSIVE UNITS FETCH
                units = get_units(c_id, fetch_all=True) # Fetch ALL folders
                if units:
                    # Build Path Map
                    id_to_unit = {u['id']: u for u in units}
                    
                    def get_path(u):
                         parts = [u['name']]
                         curr = u
                         # Safety limit for depth
                         depth = 0
                         while curr.get('parent_id') and depth < 10:
                             pid = curr['parent_id']
                             parent = id_to_unit.get(pid)
                             if parent:
                                 parts.insert(0, parent['name'])
                                 curr = parent
                                 depth += 1
                             else:
                                 break
                         return " / ".join(parts)
                    
                    # Create Map: Path String -> ID
                    u_map = {get_path(u): u['id'] for u in units}
                    keys = sorted(list(u_map.keys()))
                    
                    # Default
                    def_idx = 0
                    for i, k in enumerate(keys):
                         if "Transcriptor" in k:
                             def_idx = i
                             break
                    
                    sel_name = st.selectbox("📂 ¿Dónde guardar la transcripción?", keys, index=def_idx, help="Elige cualquier carpeta o subcarpeta")
                    selected_unit_id = u_map[sel_name]
                else:
                    st.warning("⚠️ Tu diplomado no tiene carpetas. Se crearán automáticamente.")
            else:
                st.warning("⚠️ Por favor selecciona un diplomado en la barra lateral.")

            st.info(f"📂 {len(uploaded_files)} archivo(s) cargado(s).")
            
            # --- RENAME FEATURE ---
            file_renames = {}
            if uploaded_files:
                with st.expander("✍🏻 Renombrar archivos (Opcional)", expanded=True):
                    for i, uf in enumerate(uploaded_files):
                         base = os.path.splitext(uf.name)[0]
                         new_n = st.text_input(f"Nombre para {uf.name}:", value=base, key=f"ren_{i}")
                         file_renames[uf.name] = new_n
            
            if st.button("▶️ Iniciar Transcripción", type="primary", key="btn_start_transcription", use_container_width=True, disabled=(not selected_unit_id)):
                if not selected_unit_id:
                    st.error("Error: Carpeta no seleccionada.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # PROCESS LOOP
                    for i, file in enumerate(uploaded_files):
                        t_unit_id = selected_unit_id # Use manual selection
                        
                        status_text.markdown(f"**Procesando {file.name}... (0%)**")
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
                            
                            # Use Custom Name
                            custom_n = file_renames.get(file.name, os.path.splitext(file.name)[0])
                            final_name = f"{custom_n}.txt"
                            
                            upload_file_to_db(t_unit_id, final_name, trans_text, "transcript")
                            st.success(f"✅ Guardado como: {final_name}") 
                            st.session_state['transcript_history'].append({"name": custom_n, "text": trans_text})
                            
                            if os.path.exists(txt_path): os.remove(txt_path)
                            
                        except Exception as e:
                            st.error(f"Error procesando {file.name}: {e}")
                        finally:
                            if os.path.exists(temp_path): os.remove(temp_path)
                        
                        progress_bar.progress(1.0)

                    status_text.success("¡Procesamiento completo!")

    # History
    if st.session_state['transcript_history']:
        
        # Recents Header
        st.divider()
        c_hist_1, c_hist_2, c_hist_3 = st.columns([0.5, 0.25, 0.25], vertical_alignment="center")
        c_hist_1.markdown("### 📝 Resultados Recientes")
        
        # CLEAR BUTTON
        if c_hist_2.button("🧹 Limpiar Pantalla", help="Borra la pantalla y los archivos subidos (no borra de la biblioteca)", use_container_width=True):
            st.session_state['transcript_history'] = []
            import uuid
            st.session_state['transcriptor_key'] = str(uuid.uuid4()) # Force Uploader Reset
            st.rerun()
            
        # DISCUSS WITH TUTOR BUTTON
        if c_hist_3.button("🗣️ Debatir con Tutor", help="Abre un chat con el profesor para analizar estas transcripciones", type="primary", use_container_width=True):
             # 1. Aggregate Transcripts
             context_blob = "Aquí están las transcripciones de los archivos que acabo de procesar:\n\n"
             for item in st.session_state['transcript_history']:
                 context_blob += f"--- ARCHIVO: {item['name']} ---\n{item['text']}\n\n"
             
             context_blob += "\nAnalyzalas y dime qué podemos hacer con ellas (resumen, extraer datos, ordenar instrucciones, etc). ¿Qué sugieres?"
             
             # 2. Create Session
             from database import create_chat_session, save_chat_message
             import datetime
             sess_name = f"Debate Transcripciones {datetime.datetime.now().strftime('%H:%M')}"
             new_sess = create_chat_session(st.session_state['user'].id, sess_name)
             
             if new_sess:
                 # 3. Save Message & Prepare Redirect
                 st.session_state['current_chat_session'] = new_sess
                 st.session_state['tutor_chat_history'] = [] # Reset local
                 
                 save_chat_message(new_sess['id'], "user", context_blob)
                 st.session_state['tutor_chat_history'].append({"role": "user", "content": context_blob})
                 
                 # 4. Trigger AI & Switch
                 st.session_state['trigger_ai_response'] = True
                 st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                 st.session_state['force_chat_tab'] = True
                 st.rerun()
             else:
                 st.error("Error al crear sesión de chat.")
        
        for i, item in enumerate(st.session_state['transcript_history']):
            with st.expander(f"📄 {item['name']}", expanded=True):
                 # Header with Copy
                 c_txt, c_cp = st.columns([0.7, 0.3])
                 with c_txt:
                     st.caption("Texto Transcrito:")
                 with c_cp:
                     # JS COPY COMPONENT
                     import json
                     import streamlit.components.v1 as components
                     safe_txt = json.dumps(item['text'])
                     html_cp = f"""
                    <html>
                    <body style="margin:0; padding:0; background: transparent;">
                        <script>
                        function copyT() {{
                            navigator.clipboard.writeText({safe_txt}).then(function() {{
                                const b = document.getElementById('btn');
                                b.innerText = '✅';
                                setTimeout(() => {{ b.innerText = '📄'; }}, 2000);
                            }});
                        }}
                        </script>
                        <button id="btn" onclick="copyT()" style="
                            cursor: pointer; background: transparent; border: none; font-size: 20px;
                        " title="Copiar al portapapeles">
                            📄
                        </button>
                    </body>
                    </html>
                    """
                     components.html(html_cp, height=40)
                 
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
             from database import get_units, get_files, get_file_content, upload_file_to_db, get_course_files
             
             units = get_units(c_id)
             
             # GLOBAL SEARCH: Fetch "type=transcript" from ANY folder in this course
             # This finds files even if user has moved/renamed them or put them in custom folders
             transcript_files = get_course_files(c_id, type_filter="transcript")
             
             # Check Global Memory
             gl_ctx, gl_count = get_global_context()
             if gl_count > 0:
                st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")
            
             if not transcript_files:
                st.info("No hay transcripciones. Sube videos en la Pestaña 1 (se creará carpeta 'Transcriptor').")
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
                        
                        # Save to "Apuntes Simples" Unit in DB
                        target_folder = "Apuntes Simples"
                        n_unit = next((u for u in units if u['name'] == target_folder), None)
                        if not n_unit:
                             # Silent Fallback
                             from database import create_unit
                             n_unit = create_unit(c_id, target_folder)
                        
                        if n_unit:
                             # Convert JSON structure to Clean Markdown
                             md_content = f"# 📝 Apuntes: {selected_file.replace('_transcripcion.txt', '')}\n\n"
                             md_content += f"## 🟢 Nivel 1: Resumen Ultracorto\n{notes_data.get('ultracorto', '')}\n\n"
                             md_content += "---\n\n"
                             md_content += f"## 🟡 Nivel 2: Conceptos Intermedios\n{notes_data.get('intermedio', '')}\n\n"
                             md_content += "---\n\n"
                             md_content += f"## 🔴 Nivel 3: Profundidad Detallada\n{notes_data.get('profundo', '')}"
                             
                             base_name = selected_file.replace("_transcripcion.txt", "").replace(".txt", "").strip()
                             fname = f"Apuntes {base_name}.md"
                             
                             upload_file_to_db(n_unit['id'], fname, md_content, "note")
                             st.success(f"Apuntes guardados en '{target_folder}'/{fname}")
                        
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
            from database import get_units, get_files, get_file_content, upload_file_to_db, create_unit, get_course_files
            
            # Fetch Transcripts (Global Search in Course)
            units = get_units(c_id)
            transcript_files = get_course_files(c_id, type_filter="transcript")
            
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
                        
                        # Save to "Guía de Estudio" Unit in DB
                        target_guide_folder = "Guía de Estudio"
                        g_unit = next((u for u in units if u['name'] == target_guide_folder), None)
                        if not g_unit:
                             g_unit = create_unit(c_id, target_guide_folder)
                        
                        if g_unit:
                             base_name = selected_guide_file.replace("_transcripcion.txt", "").replace(".txt", "").strip()
                             fname = f"Guia {base_name}.md"
                             upload_file_to_db(g_unit['id'], fname, guide, "guide")
                             st.success(f"Guía guardada en '{target_guide_folder}'/{fname}")

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
            # CONSULTANT FIx: Real Paste Button (Client-Side)
            # Using st.fragment to preventing full-page reload (White Flash)
            
            @st.fragment
            def quiz_input_section():
                # 1. Paste Button Logic
                try:
                    from streamlit_paste_button import paste_image_button as pbutton
                    paste_result = pbutton(
                        label="📋 Pegar Imagen (Portapapeles)",
                        background_color="#4B22DD",
                        hover_background_color="#3600B3",
                        text_color="#ffffff",
                        key="pbutton_quiz_frag"
                    )
                    
                    if paste_result.image_data is not None:
                         img = paste_result.image_data
                         
                         # FIX: Prevent Re-Insertion Loop
                         # Hash the image to check if we already processed this specific paste event
                         import hashlib
                         img_bytes = img.tobytes()
                         img_hash = hashlib.md5(img_bytes).hexdigest()
                         
                         last_hash = st.session_state.get('last_paste_hash')
                         
                         # Only append if it's a NEW paste (Hash changed)
                         if img_hash != last_hash:
                             if img.mode == 'RGBA': img = img.convert('RGB')
                             st.session_state['pasted_images'].append(img)
                             st.session_state['last_paste_hash'] = img_hash # Mark as processed
                             st.toast("Imagen pegada con éxito!", icon='📸')
                except Exception as e:
                    st.error(f"Error cargando botón: {e}")

                # 2. Show Thumbnails (With Delete Option)
                if st.session_state['pasted_images']:
                    st.caption(f"📸 {len(st.session_state['pasted_images'])} capturas pegadas:")
                    cols_past = st.columns(max(1, len(st.session_state['pasted_images'])))
                    for idx, p_img in enumerate(st.session_state['pasted_images']):
                        if idx < len(cols_past):
                            with cols_past[idx]: 
                                st.image(p_img, width=50)
                                # CONSULTANT FIX: Individual Delete
                                if st.button("🗑️", key=f"del_img_{st.session_state['quiz_key']}_{idx}", help="Eliminar esta imagen"):
                                    st.session_state['pasted_images'].pop(idx)
                                    st.rerun()

                # 3. Inputs
                st.text_area("✍🏻 O escribe tu pregunta aquí directamente:", height=100, placeholder="Ej: ¿Cuál es la capital de Francia? a) París b) Roma...", key=f"q_txt_{st.session_state['quiz_key']}")
                st.file_uploader("O sube archivos manualmente:", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True, key=f"up4_{st.session_state['quiz_key']}")

                # 4. Trigger
                # Calculate if valid
                # Access via session_state to be safe inside fragment
                q_key = st.session_state['quiz_key']
                txt_val = st.session_state.get(f"q_txt_{q_key}", "")
                files_val = st.session_state.get(f"up4_{q_key}", [])
                
                has_text = bool(txt_val.strip())
                total_items = (len(files_val) if files_val else 0) + len(st.session_state['pasted_images']) + (1 if has_text else 0)

                # Context Toggle
                use_context = st.checkbox("🔗 Vincular imágenes con el texto (Contexto)", value=False, key=f"chk_ctx_{q_key}", help="Si activas esto, el texto y las imágenes se enviarán JUNTOS para responder. Si no, se analizan por separado.")

                if total_items > 0:
                    if st.button("Resolver Preguntas", key="btn4_frag", type="primary"):
                        st.session_state['trigger_quiz_solve'] = True
                        st.session_state['quiz_use_context'] = use_context # Pass preference
                        st.rerun()

            # Call Fragment
            quiz_input_section()
            
            # --- MAIN THREAD PROCESSING ---
            if st.session_state.get('trigger_quiz_solve', False):
                # Reset Trigger immediately so it doesn't loop
                st.session_state['trigger_quiz_solve'] = False
                
                # Fetch Data AGAIN from Session context
                q_key = st.session_state['quiz_key']
                input_text_quiz = st.session_state.get(f"q_txt_{q_key}", "")
                img_files = st.session_state.get(f"up4_{q_key}", [])
                has_text = bool(input_text_quiz.strip())
                progress_bar = st.progress(0)
                status = st.empty()
                results = [] 
            
                # 1. Process Queue
                # 1. Process Queue
                use_ctx_mode = st.session_state.get('quiz_use_context', False)
                
                # Collect ALL Images
                all_pil_images = []
                
                # From Upload
                if img_files:
                    for f in img_files:
                        try:
                            pil_i = Image.open(f)
                            if pil_i.mode == 'RGBA': pil_i = pil_i.convert('RGB')
                            all_pil_images.append(pil_i)
                        except: pass
                        
                # From Paste
                all_pil_images.extend(st.session_state['pasted_images'])
                
                items_to_process = []
                
                if use_ctx_mode:
                    # LINKED MODE: One Request
                    if not all_pil_images and not has_text:
                        st.warning("Nada que analizar.")
                    else:
                        items_to_process.append({
                            "type": "linked", 
                            "text": input_text_quiz, 
                            "images": all_pil_images, 
                            "name": "Análisis Contextual Integrado"
                        })
                else:
                    # SEPARATE MODE (Legacy)
                    if has_text:
                        items_to_process.append({"type": "text", "obj": input_text_quiz, "name": "Pregunta de Texto"})
                    
                    # Add Images separately
                    for i, img_obj in enumerate(all_pil_images):
                         items_to_process.append({"type": "image_obj", "obj": img_obj, "name": f"Imagen {i+1}"})

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
                             
                        elif item["type"] == "linked":
                             # Linked Mode
                             # Pass list of images
                             full_answer = assistant.solve_quiz(images=item["images"], question_text=item["text"], global_context=gl_ctx)
                             # Display first image as thumbnail?
                             disp_img = item["images"][0] if item["images"] else None
                             
                        elif item["type"] == "image_obj":
                            # Image Only
                            disp_img = item["obj"]
                            full_answer = assistant.solve_quiz(images=[disp_img], global_context=gl_ctx)

                        # Robust Regex Parsing for Short Answer
                        import re
                        short_answer = "Respuesta no detectada (Ver detalle)"
                        match = re.search(r"\*\*Respuesta Correcta:?\*\*?\s*(.*)", full_answer, re.IGNORECASE)
                        if match:
                             short_answer = match.group(1).strip()
                    
                        results.append({"name": item["name"], "full": full_answer, "short": short_answer, "img_obj": disp_img})
                
                    except Exception as e:
                        print(e)
                        results.append({"name": item["name"], "full": f"Error: {e}", "short": "Error", "img_obj": None})
                
                progress_bar.progress(1.0)
                status.success("¡Análisis Terminado! (100%)")
                st.session_state['quiz_results'] = results # Save results
                
                # CONSULTANT FIX: Proactive Chat Start
                # Clear previous chat and start fresh with context
                st.session_state['quiz_chat'] = []
                st.session_state['quiz_chat'].append({
                    "role": "assistant", 
                    "content": "✅ **Análisis completado.** He revisado tus preguntas.\n\n¿Estás de acuerdo con todas las respuestas o quieres debatir alguna?"
                })

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
                with st.expander(f"Ver detalle de Item {i+1}"):
                    if 'img_obj' in res:
                        try:
                            st.image(res['img_obj'], width=300)
                        except:
                            st.warning("Imagen no disponible tras recarga")
                    st.markdown(res['full'])

            # --- DEBATE CHAT ---
            st.divider()
            st.markdown("### 💬 Debatir Resultados")
            st.caption("¿No estás de acuerdo con una respuesta? Habla con el Profesor aquí mismo.")
            
            if 'quiz_chat' not in st.session_state: st.session_state['quiz_chat'] = []
            
            # Display History
            for msg in st.session_state['quiz_chat']:
                 with st.chat_message(msg["role"]): st.markdown(msg["content"])
                 
            # Input
            if prompt := st.chat_input("Escribe tu duda o corrección...", key="quiz_chat_input"):
                 # Add User Msg
                 st.session_state['quiz_chat'].append({"role": "user", "content": prompt})
                 with st.chat_message("user"): st.markdown(prompt)
                 
                 # Prepare Context (Last Quiz Results)
                 ctx_quiz = "SIN DATOS DE QUIZ RECIENTE"
                 if st.session_state['quiz_results']:
                     ctx_quiz = "--- RESULTADOS DEL QUIZ --- \n"
                     for res in st.session_state['quiz_results']:
                         # Truncate text to avoid token explosion
                         short_full = (res['full'][:500] + '..') if len(res['full']) > 500 else res['full']
                         ctx_quiz += f"[Item: {res['name']}]\nAI Dice: {short_full}\n\n"
                 
                 # Call AI
                 with st.chat_message("assistant"):
                     with st.spinner("El profesor está re-analizando las imágenes y tu argumento..."):
                          try:
                              # Gather Images for Context
                              images_ctx = []
                              if st.session_state['quiz_results']:
                                  for r in st.session_state['quiz_results']:
                                      if r.get('img_obj'): images_ctx.append(r['img_obj'])
                              
                              reply = assistant.debate_quiz(
                                  history=st.session_state['quiz_chat'][:-1], 
                                  latest_input=prompt, 
                                  quiz_context=ctx_quiz,
                                  images=images_ctx
                              )
                              st.markdown(reply)
                              st.session_state['quiz_chat'].append({"role": "assistant", "content": reply})
                          except Exception as e:
                              st.error(f"Error en chat: {e}")

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
            
            # CONSULTANT: SHOW LINKED LIBRARY FILE (Tab 5)
            if st.session_state.get('chat_context_file'):
                l_file = st.session_state['chat_context_file']
                st.success(f"📎 **VINCULADO:** {l_file['name']}")
                if st.button("❌ Desvincular", key="unlink_file_tab5", help="Quitar este archivo"):
                    st.session_state['chat_context_file'] = None
                    st.rerun()

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
                if task_file:
                     attachment_data = {
                         "mime_type": task_file.type,
                         "data": task_file.getvalue()
                     }
                # CONSULTANT: PREFER LINKED FILE IF NO UPLOAD
                elif st.session_state.get('chat_context_file'):
                     l_file = st.session_state['chat_context_file']
                     # We treat it as text context or attachment? 
                     # solve_homework takes 'task_attachment' (dict with data/mime) OR we append to text.
                     # Since it's from Library, we likely have text content.
                     # Let's append to gathered_texts for robustness.
                     c_txt = l_file.get('content') or l_file.get('content_text') or ""
                     gathered_texts.append(f"--- [ARCHIVO VINCULADO: {l_file['name']}] ---\n{c_txt}\n")
                     st.toast(f"📎 Usando archivo vinculado: {l_file['name']}")
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
                            st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
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
    
    # --- SESSION STATE FOR ACTIVE FILES ---
    if 'active_context_files' not in st.session_state:
        st.session_state['active_context_files'] = []

    # --- FETCH MESSAGES FROM DB IF SESSION ACTIVE ---
    from database import get_chat_messages, save_chat_message
    
    current_sess = st.session_state.get('current_chat_session')
    
    if not current_sess:
        # CONSULTANT FIX: Direct Access - Start Chat Immediately
        # Replaces the old "Go to sidebar" placeholder
        st.markdown("### ¿En qué te ayudo hoy? 🎓")
        st.caption("Escribe tu pregunta y crearé una sesión nueva automáticamente.")
        
        init_prompt = st.chat_input("Escribe tu pregunta para empezar...", key="new_chat_init_input")
        
        if init_prompt:
             # 1. Create Session
             # Generate a title from the prompt (truncated)
             short_title = init_prompt[:30] + "..." if len(init_prompt) > 30 else init_prompt
             new_session = create_chat_session(st.session_state['user'].id, short_title)
             
             if new_session:
                 # 2. Set as Active
                 st.session_state['current_chat_session'] = new_session
                 st.session_state['tutor_chat_history'] = [] 
                 
                 # 3. Save User Message
                 save_chat_message(new_session['id'], "user", init_prompt)
                 st.session_state['tutor_chat_history'].append({"role": "user", "content": init_prompt})
                 
                 # 4. Update Footprint (Sidebar Access)
                 footprint = {
                     "type": "chat",
                     "title": short_title,
                     "target_id": new_session['id'],
                     "subtitle": "Nueva consulta"
                 }
                 update_user_footprint(st.session_state['user'].id, footprint)
                 
                 # 5. Trigger AI Response
                 st.session_state['trigger_ai_response'] = True
                 
                 st.rerun()
             else:
                 st.error("Error iniciando sesión de chat.")
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
            
            # CONSULTANT: SHOW LINKED LIBRARY FILE
            if st.session_state.get('chat_context_file'):
                l_file = st.session_state['chat_context_file']
                st.success(f"📎 **VINCULADO:**\n{l_file['name']}")
                if st.button("❌ Desvincular", key="unlink_file", help="Quitar este archivo del chat"):
                    st.session_state['chat_context_file'] = None
                    st.rerun()
            
            st.divider()
            st.markdown("### 📎 Contexto Activo")
            
            # 1. SHOW ACTIVE FILES
            if st.session_state['active_context_files']:
                for idx, f in enumerate(st.session_state['active_context_files']):
                    c1, c2 = st.columns([0.8, 0.2])
                    c1.markdown(f"📄 `{f['name']}`")
                    if c2.button("✖️", key=f"del_ctx_{idx}", help="Quitar archivo"):
                        st.session_state['active_context_files'].pop(idx)
                        st.rerun()
            else:
                st.caption("No hay archivos en memoria.")

            # st.markdown("### ☁️ Subir Nuevo") # Removed for Floating Button
            # tutor_file = st.file_uploader("Agregar a contexto", type=['pdf', 'txt', 'png', 'jpg'], key="tutor_up")
            
            if st.button("🗑️ Limpiar pantalla", key="clear_chat"):
                 # This only clears screen, to delete history use delete session
                 # But maybe we want a 'Clear Messages' function?
                 # For now, just reset local state, but DB remains? 
                 # User asked for "create different chats".
                 pass

        # --- FLOATING UPLOAD BUTTON (JS Injection to Input) ---
        # 1. Render Popover (Hidden initially to prevent flash)
        # We use a specific container to help JS find it easily if needed, but data-testid is fine.
        
        # CSS to hide it initially and style the internal button
        st.markdown("""
        <style>
        /* Target the popover container - Initial State */
        div[data-testid="stPopover"] {
            /* We don't hide it fully via display:none or JS might fail to grab dimensions, 
               but we can use opacity or just rely on JS moving it quickly. 
               Let's style the button itself to look like a 'Clip'. 
            */
            border: none !important;
        }
        div[data-testid="stPopover"] button {
            background-color: transparent;
            border: none;
            color: #555;
            font-size: 24px;
            padding: 5px;
            transition: color 0.3s;
        }
        div[data-testid="stPopover"] button:hover {
            color: #1f77b4;
            background-color: rgba(0,0,0,0.05);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 2. POP_OVER CONTENT
        # We define it here. It renders at the bottom of the flow.
        # JS will move this element into the Chat Input container.
        with st.popover("➕", help="Adjuntar archivos"):
             st.markdown("### 📎 Adjuntar")
             new_uploads = st.file_uploader("Archivos", type=['pdf', 'txt', 'md', 'py', 'png', 'jpg'], accept_multiple_files=True, key="float_up_inj")
             if new_uploads:
                for up_file in new_uploads:
                    if not any(f['name'] == up_file.name for f in st.session_state['active_context_files']):
                        with st.spinner(f"Procesando {up_file.name}..."):
                            content_text = ""
                            if up_file.type == "application/pdf":
                                try:
                                    import PyPDF2
                                    pdf_reader = PyPDF2.PdfReader(up_file)
                                    for page in pdf_reader.pages:
                                        content_text += page.extract_text() + "\n"
                                except:
                                     try:
                                         content_text = assistant.extract_text_from_pdf(up_file.getvalue())
                                     except:
                                         content_text = "[Error leyendo PDF]"
                            else:
                                try:
                                    content_text = up_file.read().decode("utf-8")
                                except:
                                    content_text = f"[Archivo Binario/Imagen: {up_file.name}]"
                            
                            st.session_state['active_context_files'].append({
                                "name": up_file.name,
                                "content": content_text
                            })
                            st.success(f"✅")
        
        # --- HIDDEN PASTE RECEIVER ---
        with st.container():
             # Unique Label for reliable JS targeting
             paste_bin = st.file_uploader("Paste_Receiver_Hidden_Bin", type=['png','jpg','jpeg','pdf'], key="paste_bin", label_visibility='hidden')
        
        if paste_bin:
             if not any(f['name'] == paste_bin.name for f in st.session_state['active_context_files']):
                 st.session_state['active_context_files'].append({
                     "name": f"Pasted_{paste_bin.name}",
                     "content": f"[Archivo Pegado: {paste_bin.name}]" 
                 })
                 st.toast("📸 Archivo pegado!")

        st.components.v1.html("""
        <script>
        const observer = new MutationObserver(() => {
            const popovers = window.parent.document.querySelectorAll('div[data-testid="stPopover"]');
            const chatInput = window.parent.document.querySelector('[data-testid="stChatInput"]');
            
            if (chatInput && popovers.length > 0) {
                 const targetPopover = popovers[popovers.length - 1]; 
                 const textArea = chatInput.querySelector('textarea');
                 
                 if (textArea && textArea.parentElement) {
                     const capsule = textArea.parentElement;
                     
                     // 1. INJECT BUTTON
                     if (!capsule.contains(targetPopover)) {
                         targetPopover.style.position = 'relative';
                         targetPopover.style.margin = '0 5px 0 5px';
                         targetPopover.style.display = 'flex';
                         targetPopover.style.alignItems = 'center';
                         targetPopover.style.zIndex = '10';
                         capsule.insertBefore(targetPopover, capsule.firstChild);
                         textArea.style.paddingLeft = '0px';
                         
                         // 2. FOCUS FIX: Click on bubble -> Focus Textarea
                         capsule.onclick = (e) => {
                             if (!targetPopover.contains(e.target)) {
                                 textArea.focus();
                                 textArea.click(); // Redundant ensure
                             }
                         };
                     }
                 }
            }
            
            // 3. PASTE HANDLER & HIDE RECEIVER (ROBUST VERSION)
            // We search for the Uploader Wrapper that contains our specific LABEL text.
            // This ensures we do NOT hide the Popover uploader.
            
            const allUploaders = Array.from(window.parent.document.querySelectorAll('[data-testid="stFileUploader"]'));
            let pasteUploaderWrapper = null;
            let pasteInput = null;

            allUploaders.forEach(wrapper => {
                if (wrapper.innerText.includes("Paste_Receiver_Hidden_Bin")) {
                    pasteUploaderWrapper = wrapper;
                    pasteInput = wrapper.querySelector('input[type="file"]');
                }
            });

            if (pasteUploaderWrapper && pasteInput) {
                // Hide it!
                pasteUploaderWrapper.style.display = 'none';

                // Global Paste Listener
                window.parent.document.onpaste = (event) => {
                    // Only handle if text area is NOT focused (or even if it is, for images?)
                    // Streamlit text area handles text. We care about IMAGES/FILES.
                    
                    const items = (event.clipboardData || event.originalEvent.clipboardData).items;
                    let hasFile = false;
                    
                    for (index in items) {
                        const item = items[index];
                        if (item.kind === 'file') {
                            hasFile = true;
                            const blob = item.getAsFile();
                            
                            // Assign to Input
                            const dataTransfer = new DataTransfer();
                            dataTransfer.items.add(blob);
                            pasteInput.files = dataTransfer.files;
                            pasteInput.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    }
                    
                    // If we handled a file, we might want to prevent default text paste if it was mixed?
                    // Typically Ctrl+V with image doesn't have text.
                };
            }
            
            // SCROLL BUTTON LOGIC INTEGRATED
            const scrollBtn = window.parent.document.getElementById("tutor_scroll_btn");
            if (scrollBtn) {
                 scrollBtn.onclick = () => {
                    const anchor = window.parent.document.getElementById("tutor_chat_end_anchor");
                    if (anchor) anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    
                    if (chatInput) {
                        const ta = chatInput.querySelector('textarea');
                        if (ta) setTimeout(() => ta.focus(), 50);
                    }
                 };
            }

        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true, attributes: true });
        </script>
        """, height=0)

        with col_chat:
            # Display Chat History (WhatsApp Style)
            import markdown
            chat_html = '<div style="display: flex; flex-direction: column; gap: 15px; padding-bottom: 50px;">'
            
            for msg in st.session_state['tutor_chat_history']:
                is_user = msg['role'] == 'user'
                
                # Styles
                row_style = "display: flex; width: 100%; align-items: flex-end; margin-bottom: 2px;"
                if is_user:
                     row_style += " justify-content: flex-end;"
                else:
                     row_style += " justify-content: flex-start;"
                
                bubble_style = "padding: 10px 14px; border-radius: 12px; max-width: 70%; word-wrap: break-word; font-size: 16px; line-height: 1.5; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-family: inherit;"
                if is_user:
                    bubble_style += " background-color: #d9fdd3; color: #111; border-bottom-right-radius: 2px; margin-right: 8px;"
                else:
                    bubble_style += " background-color: #ffffff; color: #111; border-bottom-left-radius: 2px; border: 1px solid #f0f0f0; margin-left: 8px;"
                
                # AVATAR (Emoji based for robustness)
                avatar_icon = "👤" if is_user else "🎓"
                avatar_bg = "#eee" if is_user else "#e6f3ff"
                avatar_html = f'''
                <div style="width: 35px; height: 35px; min-width: 35px; border-radius: 50%; background-color: {avatar_bg}; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                    {avatar_icon}
                </div>
                '''

                # Convert Markdown
                raw_content = msg.get('content', '') or ''
                try:
                    msg_html = markdown.markdown(raw_content, extensions=['fenced_code', 'tables'])
                except:
                    msg_html = raw_content

                if is_user:
                    # User: Bubble Left of Avatar (Avatar on far right)
                    chat_html += f'<div style="{row_style}"><div style="{bubble_style}">{msg_html}</div>{avatar_html}</div>'
                else:
                    # Bot: Avatar Left of Bubble
                    chat_html += f'<div style="{row_style}">{avatar_html}<div style="{bubble_style}">{msg_html}</div></div>'
                    
            chat_html += '<div id="tutor_chat_end_anchor" style="height: 1px;"></div></div>'
            st.markdown(chat_html, unsafe_allow_html=True)
            
            # SCROLL BUTTON (INJECTED INTO PARENT)
            st.components.v1.html("""
            <script>
            // Create Floating Button
            const btnId = "tutor_scroll_btn";
            const existingBtn = window.parent.document.getElementById(btnId);
            if (existingBtn) {
                existingBtn.remove();
            }

            const btn = window.parent.document.createElement("button");
            btn.id = btnId;
            btn.innerHTML = "⬇️";
            btn.style.cssText = `
                position: fixed;
                bottom: 120px;
                right: 20px;
                z-index: 999999;
                width: 45px;
                height: 45px;
                border-radius: 50%;
                background: white;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                border: 1px solid #ddd;
                cursor: pointer;
                font-size: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            `;
            
            btn.onmouseover = () => { btn.style.transform = "scale(1.1)"; };
            btn.onmouseout = () => { btn.style.transform = "scale(1)"; };
            
            btn.onclick = () => {
                const anchor = window.parent.document.getElementById("tutor_chat_end_anchor");
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                } else {
                     const selectors = ['section[data-testid="stAppViewContainer"]', '.main', 'section.main'];
                     for (const sel of selectors) {
                        const el = window.parent.document.querySelector(sel);
                        if (el) el.scrollTop = el.scrollHeight;
                     }
                }
                
                // FOCUS INPUT
                try {
                    const chatInput = window.parent.document.querySelector('[data-testid="stChatInput"]');
                    if (chatInput) {
                        const textArea = chatInput.querySelector('textarea');
                        if (textArea) {
                            setTimeout(() => { textArea.focus(); }, 100); // Small delay to ensure scroll finishes or UI stabilizes
                        }
                    }
                } catch(e) { console.error("Focus failed", e); }
            };
            
            window.parent.document.body.appendChild(btn);
            </script>
            """, height=0)

            # --- AI GENERATION BLOCK (Context-Aware) ---
            if st.session_state.get('trigger_ai_response'):
                 # Logic to generate response
                 # Need to fetch the last user message
                 hist = st.session_state['tutor_chat_history']
                 if hist and hist[-1]['role'] == 'user':
                     last_msg = hist[-1]['content']
                     
                     # Context Prep
                     gl_ctx, _ = get_global_context()
                     
                     # File Context - USE PERSISTENT LIST
                     gen_files = st.session_state.get('active_context_files', [])
                     
                     # Add Linked Library File if exists (Ephemeral)
                     if st.session_state.get('chat_context_file'):
                         l_f = st.session_state['chat_context_file']
                         c_t = l_f.get('content') or l_f.get('content_text') or ""
                         # Hydrate if needed (lazy)
                         if not c_t and 'id' in l_f:
                             from database import get_file_content
                             c_t = get_file_content(l_f['id'])
                         # Check duplicate
                         if not any(f['name'] == l_f['name'] for f in gen_files):
                             gen_files.append({"name": l_f['name'], "content": c_t})
                     
                     with st.chat_message("assistant"):
                        with st.spinner("El profesor está pensando..."):
                            try:
                                full_resp = assistant.chat_tutor(
                                    last_msg,
                                    chat_history=hist[:-1],
                                    context_files=gen_files,
                                    global_context=gl_ctx
                                )
                                st.markdown(full_resp)
                                
                                # Save
                                save_chat_message(current_sess['id'], "assistant", full_resp)
                                st.session_state['tutor_chat_history'].append({"role": "assistant", "content": full_resp})
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                 
                 st.session_state['trigger_ai_response'] = False # Safety

        # --- INPUT MOVED OUTSIDE OF COLUMNS (STICKY FOOTER FIX) ---
        if prompt := st.chat_input(f"Pregunta sobre {current_sess['name']}..."):
            # 1. Handle New Uploads logic
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
                    
                    # Deduplicate by name
                    if 'active_context_files' not in st.session_state: st.session_state['active_context_files'] = []
                    
                    if not any(f['name'] == tutor_file.name for f in st.session_state['active_context_files']):
                        st.session_state['active_context_files'].append({"name": tutor_file.name, "content": content})
                        st.toast(f"📎 Archivo {tutor_file.name} guardado en memoria.")
                except Exception as e:
                    st.error(f"Error leyendo archivo: {e}")
            
            # 2. Add User Message
            save_chat_message(current_sess['id'], "user", prompt)
            
            # Update UI State
            st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt})
            
            # 3. Trigger Response
            st.session_state['trigger_ai_response'] = True
            st.rerun()

# Force Reload Triggered
