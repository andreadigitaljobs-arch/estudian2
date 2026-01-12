import streamlit as st
import os
print("DEBUG: LOADING V72 - SYNTAX FIXED")
import glob
import uuid
import gc # Trigger V215: RAM Safety
from transcriber import Transcriber

# Helper: Play Sound
# Helper: Play Sound
def play_sound(mode='success'):
    """Reproduces a notification sound. mode: 'loud' (chirp) or 'soft' (beep)."""
    try:
        # Determine Sound Type
        if mode == 'loud':
            # Visual Notification for Major Success
            st.toast("🔔 **¡Proceso Completado!**", icon="✅")
            
            # Loud Chirp (600Hz -> 900Hz)
            sound_script = """
                <script>
                    (function() {
                        try {
                            const AudioContext = window.AudioContext || window.webkitAudioContext;
                            if (!AudioContext) return;
                            const ctx = new AudioContext();
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(600, ctx.currentTime);
                            osc.frequency.linearRampToValueAtTime(900, ctx.currentTime + 0.1); 
                            gain.gain.setValueAtTime(0.5, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start();
                            osc.stop(ctx.currentTime + 0.8);
                        } catch(e) { console.error("Audio play failed", e); }
                    })();
                </script>
            """
        else:
            # Soft Beep (400Hz, Short)
            # No toast for minor steps to avoid clutter, or maybe a small one?
            # User wants sound distinction.
            sound_script = """
                <script>
                    (function() {
                        try {
                            const AudioContext = window.AudioContext || window.webkitAudioContext;
                            if (!AudioContext) return;
                            const ctx = new AudioContext();
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.type = 'sine';
                            osc.frequency.setValueAtTime(400, ctx.currentTime);
                            gain.gain.setValueAtTime(0.2, ctx.currentTime); # Lower volume
                            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3); # Short
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.start();
                            osc.stop(ctx.currentTime + 0.3);
                        } catch(e) { console.error("Audio play failed", e); }
                    })();
                </script>
            """
            
        components.html(sound_script, height=0, width=0)
        
    except Exception as e:
        print(f"Sound Error: {e}")

# --- CRASH LOGGER (V218) ---
CRASH_LOG_FILE = "crash_log.txt"
def log_debug(msg):
    try:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        with open(CRASH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except: pass # Never crash the logger

# --- CRASH REPORT UI ---
if os.path.exists(CRASH_LOG_FILE):
    with st.expander("🐞 Debug & Crash Log (Últimos eventos)", expanded=False):
        try:
            with open(CRASH_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                st.code("".join(lines[-20:]), language="text") # Show last 20 lines
            
            if st.button("Limpiar Log"):
                os.remove(CRASH_LOG_FILE)
                st.rerun()
        except: st.error("No se pudo leer el log.")
from study_assistant import StudyAssistant
from PIL import Image, ImageGrab
import shutil
import time
import datetime
import markdown
import streamlit.components.v1 as components
import extra_streamlit_components as stx  # --- PERSISTENCE ---
from library_render import render_library_v2 as render_library # --- LIBRARY UI V2 (RELOADED V5) ---
import db_handler as database
from db_handler import (
    get_user_courses, create_course, delete_course, rename_course, 
    get_chat_sessions, create_chat_session, rename_chat_session, delete_chat_session,
    get_units, get_course_files,
    get_dashboard_stats, update_user_nickname, get_recent_chats, check_and_update_streak, 
    get_user_footprint, init_supabase, update_last_course, 
    save_chat_message, get_chat_messages, get_file_content, get_course_files, delete_file, get_course_full_context,
    get_user_memory, save_user_memory, upload_file_to_db, get_last_transcribed_file_name, get_recent_files,
    search_global, get_weekly_activity
)



# --- PAGE CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="E-Education",
    page_icon="assets/favicon.jpg",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# V400: MOBILE PWA & IMAGE FIXES
# =========================================================
# =========================================================
# V401: MOBILE NAVBAR & PWA FIX
# =========================================================
# =========================================================
# V402: MOBILE NAVBAR (NUCLEAR OPTION)
# =========================================================
def setup_pwa():
    """Injects CSS to FORCE sidebar button visibility + PWA Tags."""
    try:
        # STATIC ICON PATH
        import time
        ts = int(time.time())
        icon_url = f"app/static/pwa_icon.png?v={ts}"
        
        # PWA Manifest (Data URI)
        manifest_json = f"""
        {{
            "name": "E-Education",
            "short_name": "E-Education",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#4B22DD",
            "icons": [
                {{
                    "src": "{icon_url}",
                    "sizes": "192x192",
                    "type": "image/png"
                }},
                {{
                    "src": "{icon_url}",
                    "sizes": "512x512",
                    "type": "image/png"
                }}
            ]
        }}
        """
        import base64
        b64_manifest = base64.b64encode(manifest_json.encode()).decode()
        manifest_href = f"data:application/manifest+json;base64,{b64_manifest}"

        # JAVASCRIPT INJECTION TO PARENT HEAD
        js_pwa = f"""
        <script>
            (function() {{
                var head = window.parent.document.getElementsByTagName('head')[0];
                if (!head) return;

                function addTag(tagType, attributes) {{
                    var el = window.parent.document.createElement(tagType);
                    for (var key in attributes) {{
                        el.setAttribute(key, attributes[key]);
                    }}
                    head.appendChild(el);
                }}
                addTag('link', {{'rel': 'manifest', 'href': '{manifest_href}'}});
                addTag('link', {{'rel': 'apple-touch-icon', 'href': '{icon_url}'}});
                addTag('meta', {{'name': 'apple-mobile-web-app-capable', 'content': 'yes'}});
                addTag('meta', {{'name': 'apple-mobile-web-app-title', 'content': 'E-Education'}});
                addTag('meta', {{'name': 'viewport', 'content': 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover'}});
            }})();
        </script>
        """
        
        # Inject JS
        components.html(js_pwa, height=0, width=0)
        
        # --- NUCLEAR CSS FOR SIDEBAR BUTTON ---
        mobile_css = """
        <style>
            /* 1. FORCE TOGGLE VISIBILITY (Fixed Position) */
            [data-testid="stSidebarCollapsedControl"] {
                position: fixed !important;
                display: block !important;
                visibility: visible !important;
                z-index: 9999999 !important;
                top: 10px !important;
                left: 10px !important;
                width: 50px !important;
                height: 50px !important;
                background-color: white !important;
                border-radius: 50% !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                border: 2px solid #4B22DD !important;
                text-align: center !important;
                line-height: 50px !important;
            }
            
            /* 2. Style the Icon inside */
            [data-testid="stSidebarCollapsedControl"] svg {
                fill: #4B22DD !important;
                stroke: #4B22DD !important;
                width: 30px !important;
                height: 30px !important;
                margin-top: 10px !important;
            }

            /* 3. Hide Footer/Header Clutter */
            footer {display: none !important;}
            #MainMenu {display: none !important;}
            .stApp > header {display: none !important;}
            
            /* 4. Global Image Fit */
            img { object-fit: contain !important; }
        </style>
        """
        st.markdown(mobile_css, unsafe_allow_html=True)
        
        # VISIBLE DEBUG MARKER (To verify deployment)
        st.markdown(
            '<div style="position:fixed; top:0; right:0; background:red; color:white; padding:5px; z-index:999999;">v402</div>',
            unsafe_allow_html=True
        )
        
    except Exception as e:
        print(f"PWA Setup Error: {e}")

setup_pwa()

# --- V252: VISUAL MARKER ---
if 'v316_marker' not in st.session_state:
    # st.toast("✅ Aplicación Actualizada a V316")
    st.session_state['v316_marker'] = True

# Banner removed - Deployment Verified


# --- V249: HYBRID SNAPPY LOADER (RE-FIXED) ---
components.html("""
<script>
    (function() {
        const root = window.parent.document;
        const appNode = root.querySelector('.stApp');
        if (!appNode) return;

        // 1. Force Cleanup ensuring no ghost loaders exist
        ['estudian2_cute_loader', 'estudian2_master_loader'].forEach(id => {
            const old = root.getElementById(id);
            if (old) old.remove();
        });

        // 2. Inject Styles (Only once)
        const styleId = 'estudian2_snappy_css';
        if (!root.getElementById(styleId)) {
            const style = root.createElement('style');
            style.id = styleId;
            style.innerHTML = `
                #estudian2_cute_loader {
                    position: fixed;
                    top: 0; left: 0; width: 100vw; height: 100vh;
                    background: #F6F3FF; /* Clean Light Lilac - Solid masking */
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    z-index: 2147483647 !important; /* V299: Match max elevators */
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.25s ease;
                }
                #estudian2_cute_loader.active {
                    opacity: 1;
                    pointer-events: auto;
                }
                .cute-spinner {
                    width: 32px;
                    height: 32px;
                    border: 3.5px solid rgba(75, 34, 221, 0.1);
                    border-top: 3.5px solid #4B22DD;
                    border-radius: 50%;
                    animation: cute-spin 0.6s linear infinite;
                }
                .cute-text {
                    margin-top: 15px;
                    color: #4B22DD;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 14px;
                    font-weight: 500;
                    letter-spacing: 0.5px;
                }
                @keyframes cute-spin { to { transform: rotate(360deg); } }
            `;
            root.head.appendChild(style);
        }

        // 3. Create Loader Element with Progress Support
        const loader = root.createElement('div');
        loader.id = 'estudian2_cute_loader';
        loader.innerHTML = `
            <div class="cute-spinner"></div>
            <div class="cute-text" id="loader-main-text">Cargando...</div>
            <div class="cute-text" id="loader-progress-text" style="margin-top: 10px; font-size: 18px; font-weight: 700;"></div>
        `;
        root.body.appendChild(loader);
        
        // --- V256: SMART PROGRESS TRACKER WITH POLLING ---
        window.updateTranscriptionProgress = (message, percentage) => {
            const mainText = root.getElementById('loader-main-text');
            const progressText = root.getElementById('loader-progress-text');
            if (mainText) mainText.textContent = message;
            if (progressText) progressText.textContent = percentage !== null ? `${percentage}%` : '';
        };
        
        // Poll for progress updates from session state
        setInterval(() => {
            const progressMsg = root.body.getAttribute('data-transcription-message');
            const progressPct = root.body.getAttribute('data-transcription-percentage');
            if (progressMsg || progressPct) {
                window.updateTranscriptionProgress(progressMsg || 'Procesando...', progressPct ? parseInt(progressPct) : null);
            }
        }, 500);

        // 4. Robust State Observer
        const updateLoader = () => {
            const state = appNode.getAttribute('data-test-script-state');
            
            // --- V255: ALWAYS SHOW LOADER WHEN RUNNING ---
            // We no longer suppress it; instead we update its content dynamically
            if (state === 'running') {
                loader.classList.add('active');
                // V299: Hide Navigation Arrows
                const elevator = root.getElementById('v231_auth_elevator');
                if (elevator) elevator.style.display = 'none';
            } else {
                setTimeout(() => {
                    const currentState = appNode.getAttribute('data-test-script-state');
                    if (currentState !== 'running') {
                        loader.classList.remove('active');
                        // V299: Show Navigation Arrows
                        const elevator = root.getElementById('v231_auth_elevator');
                        if (elevator) elevator.style.display = 'flex';

                        // Reset text
                        const mainText = root.getElementById('loader-main-text');
                        const progressText = root.getElementById('loader-progress-text');
                        if (mainText) mainText.textContent = 'Cargando...';
                        if (progressText) progressText.textContent = '';
                        
                        // --- V298: CRITICAL CLEANUP ---
                        // Remove ghost attributes to prevent "¡Listo!" showing on next run
                        root.body.removeAttribute('data-transcription-message');
                        root.body.removeAttribute('data-transcription-percentage');
                    }
                }, 80); 
            }
        };

        const observer = new MutationObserver(updateLoader);
        observer.observe(appNode, { attributes: true, attributeFilter: ['data-test-script-state'] });
        
        // Initial check
        updateLoader();
    })();
</script>
""", height=0)

# --- EMERGENCY SIDEBAR RESCUE (V153: CLEAN UP) ---
st.markdown("""
<style>
    /* 1. FORCE NATIVE ARROW (The "Right" Way) */
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 99999999 !important;
        color: black !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        border-radius: 5px;
        top: 0px !important;
        left: 0px !important;
        margin: 5px !important;
    }
    
    /* Ensure Header itself is visible if it was hidden */
    /* Ensure Header background is hidden but allow arrow to be seen */
    header[data-testid="stHeader"] {
        visibility: hidden !important;
        background-color: transparent !important;
    }
    
    /* Hide the top decoration bar (colorful line) */
    header[data-testid="stHeader"]::before {
        display: none !important;
    }
    
    /* Hide the hamburger menu if user wants it clean */
    /* .stApp header .stMainMenu { visibility: hidden; } */
</style>
""", unsafe_allow_html=True)



# --- INSTANTIATE AI ENGINES (GLOBAL Fix) ---
try:
    # V350: PRIORITY ORDER FOR API KEY
    # 1. Custom user key (from sidebar)
    # 2. System secrets key
    # 3. Local file
    
    _api_key = None
    
    # Check custom key first
    if st.session_state.get('custom_api_key'):
        _api_key = st.session_state['custom_api_key']
    # Fallback to system secrets
    elif st.secrets.get("GEMINI_API_KEY"):
        _api_key = st.secrets.get("GEMINI_API_KEY")
    
    if _api_key:
         # V290: Explicitly use Stable 1.5 Flash
         transcriber = Transcriber(api_key=_api_key, model_name="gemini-1.5-flash-latest")
         assistant = StudyAssistant(api_key=_api_key)
    else:
         transcriber = None
         assistant = None
except Exception as e:
    print(f"AI Init Error: {e}")
    transcriber = None
    assistant = None

# --- GLOBAL CONTEXT HELPERS ---
def get_global_context():
    # Only fetches content if really needed (Heavy)
    try:
        if not st.session_state.get('current_course'): return "", 0
        cid = st.session_state['current_course']['id']
        txt = get_course_full_context(cid)
        
        # --- CONSULTANT: INJECT USER MEMORY (OVERRIDES) ---
        user_mem = get_user_memory(cid)
        if user_mem:
            txt += "\n\n=== 🧠 CORRECCIONES Y APRENDIZAJES DEL USUARIO (PRIORIDAD MÁXIMA) ===\n"
            txt += "Estas son correcciones explícitas que el usuario te ha enseñado. Tienen prioridad sobre cualquier otra información:\n" 
            txt += user_mem
            txt += "\n=========================================================================\n"

        fls = get_course_files(cid)
        return txt, len(fls)
    except:
        return "", 0

def get_global_file_count_only():
    # Lightweight count fetch (Optimized for Render)
    try:
        if not st.session_state.get('current_course'): return 0
        cid = st.session_state['current_course']['id']
        # Use get_dashboard_stats or similar fast query
        stats = get_dashboard_stats(cid, st.session_state['user'].id)
        return stats['files']
    except:
        return 0

# --- GENERATE VALID ICO (FIX) ---
# --- VALID ICO GENERATOR (Optimized: Check only once) ---
@st.cache_resource
def ensure_favicon():
    try:
        if os.path.exists("assets/favicon.jpg") and not os.path.exists("assets/windows_icon.ico"):
            from PIL import Image
            img = Image.open("assets/favicon.jpg")
            img.save("assets/windows_icon.ico", format='ICO', sizes=[(256, 256)])
    except: pass

ensure_favicon()
# --------------------------------


if 'quiz_results' not in st.session_state: st.session_state['quiz_results'] = []
if 'transcript_history' not in st.session_state: st.session_state['transcript_history'] = []
if 'notes_result' not in st.session_state: st.session_state['notes_result'] = None
if 'guide_result' not in st.session_state: st.session_state['guide_result'] = None
if 'last_transcribed_file' not in st.session_state: st.session_state['last_transcribed_file'] = None

if 'pasted_images' not in st.session_state: st.session_state['pasted_images'] = []
# --- GLOBAL CSS (Prevents FOUC on Logout) ---
st.markdown("""
    <style>
    /* HIDE SCROLLBAR GLOBALLY */
    ::-webkit-scrollbar {
        width: 0px;
        background: transparent;
    }

    /* --- GLOBAL VARIABLES (Theme Persistence) --- */
    :root {
        --primary-purple: #4B22DD;
        --accent-green: #6CC04A;
        --bg-color: #F8F9FE;
        --card-bg: #FFFFFF;
        --text-color: #1A1A1A;
        --border-color: #E3E4EA;
    }
    
    /* --- SYNC LAYOUT STABILITY (Prevent FOUC & Fix Login) --- */
    /* Only apply aggressive negative margins when LOGGED IN */
    """ + (f"""
    .block-container {{
        padding-top: 0rem !important;
        padding-bottom: 2rem !important;
        margin-top: -550px !important;
        transform: translateY(-100px);
        max-width: 100% !important;
    }}
    div[data-testid="stAppViewContainer"] > section[data-testid="stMain"] > div.block-container {{
        margin-top: -550px !important;
    }}
    """ if st.session_state.get('user') else f"""
    .block-container {{
        padding-top: 4rem !important;
        margin-top: 0px !important;
        transform: none;
        max-width: 100% !important;
    }}
    """) + """

    /* Hide the top decoration bar completely */
    header {
        visibility: hidden !important;
        display: none !important;
    }
    
    /* HIDE LOADING SPINNERS / ARROWS */
    .stSpinner, [data-testid="stStatusWidget"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    
    /* Remove gap at top */
    div.stApp {
        margin-top: 0px !important;
    }

    /* DYNAMIC: FREEZE SCROLL & HIDE SIDEBAR ON LOGIN */
    """ + ("""
    .stApp, section.main, .block-container, [data-testid="stAppViewContainer"], html, body {
        overflow: hidden !important;
    }
    """ if not st.session_state.get('user') else "") + """
    
    /* TAB SCROLL ARROWS */
    .stTabs [data-baseweb="tab-list"] button:not([role="tab"]) {
        background-color: #4B22DD !important;
        color: white !important;
        border-radius: 50% !important;
        width: 30px !important;
        height: 30px !important;
        border: none !important;
        display: flex !important;
    }

    /* --- SIDEBAR WIDTH CONTROL --- */
    section[data-testid="stSidebar"] {
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
        flex: 0 0 280px !important;
    }

    /* --- NUCLEAR SEPARATOR HIDER FOR SIDEBAR (ULTIMATE NUKE) --- */
    /* Target every single element in sidebar to kill borders, shadows, and GAPS */
    [data-testid="stSidebar"] *, 
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div,
    [data-testid="stSidebar"] [data-testid="element-container"],
    [data-testid="stSidebar"] [data-testid="stExpander"],
    [data-testid="stSidebar"] hr {
        border: none !important;
        border-bottom: none !important;
        border-top: none !important;
        box-shadow: none !important;
    }
    
    /* KILL ALL LAYOUT GAPS */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 8px !important; /* Restore a small, natural gap */
    }
    
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
    }

    /* --- SCROLLER STYLES --- */
    .aesthetic-sep {
        height: 1px;
        background: rgba(75, 34, 221, 0.1);
        margin: 10px 0 !important;
        width: 100%;
    }

    /* Ensure no background or border on expanders in sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: none !important;
        background-color: transparent !important;
    }

    /* Highlight Styles */
    .sc-base { background-color: #ffcccc !important; padding: 2px 5px !important; border-radius: 5px !important; font-weight: bold !important; color: #900 !important; border: 1px solid #ff9999 !important; display: inline; }
    .sc-example { background-color: #cce5ff !important; padding: 2px 5px !important; border-radius: 5px !important; color: #004085 !important; border: 1px solid #b8daff !important; display: inline; }
    .sc-note { background-color: #d4edda !important; padding: 2px 5px !important; border-radius: 5px !important; color: #155724 !important; border: 1px solid #c3e6cb !important; display: inline; }
    .sc-data { background-color: #fff3cd !important; padding: 2px 5px !important; border-radius: 5px !important; color: #856404 !important; border: 1px solid #ffeeba !important; display: inline; }
    .sc-key { background-color: #e2d9f3 !important; padding: 2px 5px !important; border-radius: 5px !important; color: #512da8 !important; border: 1px solid #d1c4e9 !important; display: inline; }
    .study-mode-off .sc-base, .study-mode-off .sc-example, .study-mode-off .sc-note, .study-mode-off .sc-data, .study-mode-off .sc-key,
    .stApp.study-mode-off .sc-base, .stApp.study-mode-off .sc-example, .stApp.study-mode-off .sc-note, .stApp.study-mode-off .sc-data, .stApp.study-mode-off .sc-key {
        background-color: transparent !important; padding: 0 !important; color: inherit !important; border: none !important; font-weight: inherit !important; 
    }

    /* --- NUCLEAR UPLOADER HIDING --- */
    div[data-testid="stFileUploader"]:has(input[aria-label="KILL_ME_NOW"]),
    div[data-testid="stFileUploader"]:has(label:contains("KILL_ME_NOW")),
    .paste-bin-hidden-wrapper {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        position: absolute !important;
    }
    
    /* --- V334 RESTORED: CSS REMOVED (Handled locally in library_render.py) --- */
    </style>
""", unsafe_allow_html=True)

if 'quiz_key' not in st.session_state: st.session_state['quiz_key'] = 0
if 'tutor_chat_history' not in st.session_state: st.session_state['tutor_chat_history'] = []
if 'current_course' not in st.session_state: st.session_state['current_course'] = None
if 'homework_result' not in st.session_state: st.session_state['homework_result'] = ""
if 'spotlight_query' not in st.session_state: st.session_state['spotlight_query'] = ""
if 'spotlight_mode' not in st.session_state: st.session_state['spotlight_mode'] = "⚡ Concepto Rápido"
if 'custom_api_key' not in st.session_state: st.session_state['custom_api_key'] = None

# --- TAB RESTORATION LOGIC (Removed - Switched to JS LocalStorage) ---
if 'has_restored_tab' not in st.session_state:
    st.session_state['has_restored_tab'] = True

# --- CHAT SESSION RESTORATION (URL PARAMS) ---
# This runs once on startup or reload
if 'has_restored_chat' not in st.session_state and st.session_state.get('user'):
    try:
        qp = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
        target_chat_id = qp.get('chat_id') if hasattr(st, 'query_params') else (qp.get('chat_id')[0] if qp.get('chat_id') else None)
        
        if target_chat_id:
            # Validate ownership
            from db_handler import get_chat_sessions
            user_chats = get_chat_sessions(st.session_state['user'].id)
            found_chat = next((c for c in user_chats if str(c['id']) == str(target_chat_id)), None)
            
            if found_chat:
                st.session_state['current_chat_session'] = found_chat
                st.session_state['tutor_chat_history'] = [] # Force reload messages
                # st.toast(f"📂 Chat restaurado: {found_chat['name']}")
    except Exception as e:
        print(f"Chat restore error: {e}")
    st.session_state['has_restored_chat'] = True

# --- AUTHENTICATION CHECK ---
if 'user' not in st.session_state:
    st.session_state['user'] = None

# --- COOKIE MANAGER (PERSISTENCE) ---
cookie_manager = stx.CookieManager()

# --- AUTO-LOGIN CHECK ---
# Only skip auto-login if user explicitly logged out (force_logout flag)
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    # Try to get token from cookie
    # We use REFRESH TOKEN for long-term persistence (simpler than session reconstruction)
    try:
        time.sleep(0.1)
        refresh_token = cookie_manager.get("supabase_refresh_token")
        if refresh_token:
             from db_handler import init_supabase
             client = init_supabase()
             res = client.auth.refresh_session(refresh_token)
             if res.session:
                 st.session_state['user'] = res.user
                 st.session_state['supabase_session'] = res.session
                 # CRITICAL FIX: Update cookie with NEW refresh token to keep chain alive
                 cookie_manager.set("supabase_refresh_token", res.session.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                 print(f"✅ Auto-login successful for: {res.user.email}")
                 time.sleep(1) # Allow cookie to set
                 st.rerun()
                 
    except Exception as e:
        print(f"Auto-login failed: {e}")

# Clear force_logout flag after it's been checked (one-time use)
if st.session_state.get('force_logout'):
    st.session_state['force_logout'] = False

# --- SCROLLBAR & OVERFLOW CONTROL (Conditional) ---
is_login_view = st.session_state.get('user') is None

# Rules Config
scroll_rules = ""
overflow_mode = "hidden"
height_mode = "100%"

if is_login_view:
    # LOGIN: Scorched Earth (No Scroll, Fixed Height)
    scroll_rules = """
            /* HIDE SCROLLBARS (Login) */
            ::-webkit-scrollbar { width: 0px !important; height: 0px !important; background: transparent !important; display: none !important; }
            * { scrollbar-width: none !important; -ms-overflow-style: none !important; }
    """
    overflow_mode = "hidden"
    height_mode = "100vh"
else:
    # DASHBOARD: Native Scrolling (No Kill Rules)
    scroll_rules = "/* Dashboard: Scrollbars Enabled */"
    overflow_mode = "hidden" # Default Streamlit: Body hidden, Container scrolls
    height_mode = "100%" 

components.html(f"""
<script>
    (function() {{
        const root = window.parent.document;
        const styleId = 'estudian2_scrollbar_manager';
        
        // Cleanup Old Tags
        const old = root.getElementById(styleId);
        if (old) old.remove();
        const oldLegacy = root.getElementById('estudian2_scrollbar_kill_V3_FINAL');
        if (oldLegacy) oldLegacy.remove();
        
        const style = root.createElement('style');
        style.id = styleId;
        style.innerHTML = `
            {scroll_rules}
            
            /* Root Config (Streamlit Standard) */
            html, body, .stApp {{
                overflow-y: {overflow_mode} !important;
                height: {height_mode} !important;
            }}
            
            /* Force Scroll on App Container for Dashboard */
            [data-testid="stAppViewContainer"] {{
                overflow-y: {'auto' if overflow_mode == 'hidden' and not is_login_view else 'hidden'} !important;
                height: 100% !important;
            }}
            
            /* Clean Layout (Always Active) - FORCE CONTENT UP */
            .block-container {{
                padding-top: 0px !important;
                margin-top: -80px !important;
                max-width: 100% !important;
                padding-bottom: 100px !important; /* Ensure space for chat input */
            }}
            
            /* TARGET ST_BOTTOM (The Container of Chat Input) */
            .stBottom {{
                position: fixed !important;
                bottom: 0px !important;
                left: 0px !important;
                right: 0px !important;
                background: transparent !important;
                z-index: 99999 !important;
            }}
            
            header {{
                visibility: visible !important;
                display: block !important;
                opacity: 1 !important;
                z-index: 1000000 !important;
                background-color: transparent !important;
            }}
            
            /* HIDE SIDEBAR COLLAPSE BUTTON (The << Arrow) */
            [data-testid="stSidebarCollapseButton"] {{
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
            }}
            
            /* Extra safety: Target the button inside the sidebar header */
            section[data-testid="stSidebar"] header button {{
                display: none !important;
            }}
        `;
        root.head.appendChild(style);
    }})();
</script>
""", height=0)

# --- GLOBAL THEME CSS (Moved to Top to Prevent Logout Flash) ---
THEME_CSS = """
<style>
/* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* HIDE STREAMLIT STATUS WIDGET & DECORATION */
    div[data-testid="stStatusWidget"] { visibility: hidden !important; }
    div[data-testid="stDecoration"] { visibility: hidden !important; }

    /* --- ULTIMATE KILL TO LOADING OVERLAY (NO MORE WHITE TRANSPARENCY) --- */
    /* Target every possible container Streamlit uses for the "dimming" effect */
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMainViewContainer"],
    [data-test-script-state="running"] [data-testid="stAppViewBlockContainer"],
    [data-test-script-state="running"] [data-testid="stAppViewContainer"],
    [data-test-script-state="running"] .stApp,
    section.main,
    div.block-container,
    .stApp > div {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    
    /* Force background to stay solid and kill any covering pseudo-elements */
    .stApp::before, .stApp::after, 
    [data-testid="stAppViewContainer"]::before,
    [data-testid="stAppViewContainer"]::after {
        display: none !important;
        opacity: 0 !important;
    }

    /* --- GLOBAL VARIABLES (Moved to Top) --- */
    /* :root variables are now prevalent globally to prevent FOUC */

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

    /* LOGIN FORM BUTTON - GREEN FORCE (Submit Only - No SVGs) */
    [data-testid="stForm"] button:not(:has(svg)) {
        background-color: #6CC04A !important;
        border: none !important;
        color: white !important;
    }
    [data-testid="stForm"] button:not(:has(svg)):hover {
        background-color: #5ab03a !important;
    }

    /* --- GLOBAL HEADERS (BRANDING) --- */
    h1, h2, h3, h4, h5, h6 {
        color: #4B22DD !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Specific Streamlit markdown headers */
    /* Specific Streamlit markdown headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4B22DD !important;
    } 

    div.stButton > button:active {
        background-color: #2a1275 !important;
        transform: translateY(0);
    }
</style>
"""
st.markdown(THEME_CSS + """
<style>
/* HIDE ROGUE HORIZONTAL LINES UNDER TABS */
.stTabs ~ hr, .stTabs + .element-container hr {
    display: none !important;
}

/* User identified specific unwanted line: tab-border */
div[data-baseweb="tab-border"] {
    display: none !important;
    visibility: hidden !important;
}

/* Ensure the Tab Border itself is visible (Line 1 - The main container border) */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #F0F0F0 !important;
}
</style>
""", unsafe_allow_html=True)






if st.session_state.get('force_logout'):
    components.html("""
    <script>
        // Clear all storage to prevent ghost state
        window.localStorage.removeItem('st_tab_target');
        window.sessionStorage.clear();
    </script>
    """, height=0)


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
        .main .block-container, div[data-testid="stAppViewBlockContainer"] {{
            padding-top: 5vh !important;
            margin-top: 2rem !important; /* LOWERED POSITION */
            padding-bottom: 5vh !important;
            max_width: 1200px !important;
            display: flex;
            flex-direction: column;
            justify-content: flex-start !important;
            min-height: 80vh; 
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
    # LIFT LOGIN CARD (User Request: "mas arriba" - RIGHT SIDE ONLY via Logo Margin)
    
    c_spacer, c_login = st.columns([1.3, 1]) 

    with c_spacer:
        st.write("") 

    with c_login:
        # ANCHOR FOR CSS TARGETING + VERTICAL CENTERING
        st.markdown('''
            <style>
            [data-testid="column"]:last-child {
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                margin-top: -230px;
            }
            </style>
            <div id="login_anchor"></div>
        ''', unsafe_allow_html=True)
        
        # LOGO HEADER
        
        logo_html = ""
        if logo_b64:
             # Height 280px. Adjusted margins: -180px Top (Much higher), -50px Bottom
             logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 280px; width: auto; max-width: 100%; display: block; margin: -180px auto -50px auto;">'
        
        # Title: "Vamos a estudiar" - Title lifted closer to logo, inputs compensated
        st.markdown(f'<div style="text-align: center; margin-bottom: 30px; margin-top: 0px;"><div style="display: flex; align-items: center; justify-content: center; margin-bottom: -20px;">{logo_html}</div><div class="messimo-title" style="margin-top: -30px; color: #4B22DD;">¡Vamos a estudiar!</div></div>', unsafe_allow_html=True)

        # FORM INPUTS (Wrapped in st.form to prevent jitter/refresh while typing)
        with st.form("login_form", clear_on_submit=False, border=False):
            # Hack to remove default form padding if needed, but border=False helps.
            email = st.text_input("Correo electrónico", key="login_email", placeholder="Correo electrónico", label_visibility="collapsed")
            password = st.text_input("Contraseña", type="password", key="login_pass", placeholder="Contraseña", label_visibility="collapsed")
            
            # Submit Button (Primary)
            submitted = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)
            
            if submitted:
                if email and password:
                    from db_handler import sign_in
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
        st.markdown('<div style="text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 15px;">¿No tienes una cuenta? <span style="color: #4B22DD; font-weight: 600;">Regístrate</span></div>', unsafe_allow_html=True)


    # --- HUNTER-KILLER: MOVED TO BOTTOM (V236) TO PREVENT LAYOUT SHIFT ---
    components.html("""
    <script>
        const root = window.parent.document;
        // 1. CLEANUP OLD SCROLLERS
        if (window.parent.estudian2_scroller_interval) clearInterval(window.parent.estudian2_scroller_interval);
        const oldScroller = root.getElementById('estudian2_nuclear_scroller');
        if (oldScroller) oldScroller.remove();
        
        // 2. ERASE NAVIGATION ARROWS ON LOGIN
        const killArrows = () => {
             const arrowIds = ['v231_auth_elevator', 'v223_global_elevator', 'v222_nav_elevator'];
             arrowIds.forEach(id => {
                 const el = root.getElementById(id);
                 if (el) el.remove();
             });
        };
        killArrows();
        setInterval(killArrows, 500);

        // 3. ATOMIC LIFT (V239): Force Container UP
        const forceLift = () => {
            const containers = [
                root.querySelector('.main .block-container'),
                root.querySelector('[data-testid="stAppViewBlockContainer"]'),
                root.querySelector('.block-container')
            ];
            containers.forEach(c => {
                if (c) {
                    c.style.setProperty('margin-top', '5vh', 'important');
                    c.style.setProperty('padding-top', '5vh', 'important');
                }
            });
            // Also hide header decoration if visible
            const deco = root.querySelector('[data-testid="stDecoration"]');
            if (deco) deco.style.display = 'none';
        };
        forceLift();
        setInterval(forceLift, 500);
    </script>
    """, height=0)

    st.stop()















# --- DUAL NAVIGATION ARROWS (V243 - Conditional Visibility) ---
def inject_navigation_arrows():
    # Show arrows on all pages with content
    components.html("""
    <script>
    const setupElevator = () => {
        const doc = window.parent.document;
        const CONTAINER_ID = 'v231_auth_elevator';
        
        console.log("🛗 [Elevator V231] Auth Init...");

        // 1. CLEANUP (Remove any old versions)
        const oldIds = ['v110_phoenix_arrow', 'v221_nav_container', 'v222_nav_elevator', 'v223_global_elevator', CONTAINER_ID];
        oldIds.forEach(id => {
            const el = doc.getElementById(id);
            if (el) el.remove();
        });

        // 2. CREATE CONTAINER
        const navContainer = doc.createElement('div');
        navContainer.id = CONTAINER_ID;
        Object.assign(navContainer.style, {
            position: 'fixed',
            bottom: '30px',
            right: '25px',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            zIndex: '2147483647', // Max Int
            pointerEvents: 'auto',
            filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))'
        });

        // 3. BUTTON FACTORY
        const createBtn = (iconClass, title, action, color) => {
            const btn = doc.createElement('button');
            btn.innerHTML = `<i class="${iconClass}"></i>`;
            btn.title = title;
            Object.assign(btn.style, {
                width: '48px',
                height: '48px',
                backgroundColor: color,
                color: 'white',
                borderRadius: '50%',
                border: '2px solid rgba(255,255,255,0.2)',
                cursor: 'pointer',
                fontSize: '22px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
            });
            
            // Hover
            btn.onmouseenter = () => { 
                btn.style.transform = 'scale(1.15) translateY(-2px)'; 
                btn.style.boxShadow = '0 8px 15px rgba(0,0,0,0.3)';
            };
            btn.onmouseleave = () => { 
                btn.style.transform = 'scale(1)'; 
                btn.style.boxShadow = 'none';
            };
            
            btn.onclick = (e) => {
                e.stopPropagation(); // Prevent bubbling
                action();
            };
            return btn;
        };

        // 4. SCROLL LOGIC (V229 Nuclear)
        const scrollNuclear = (toBottom) => {
            console.log("☢️ Nuclear Scroll Activated");
            const val = toBottom ? 9999999 : 0;
            const behavior = 'smooth'; 
            try { window.parent.scrollTo({ top: val, behavior: behavior }); } catch(e){}
            const all = doc.querySelectorAll('*');
            all.forEach(el => {
                if (el.scrollHeight > el.clientHeight) {
                    const style = window.parent.getComputedStyle(el);
                    if (style.overflowY === 'scroll' || style.overflowY === 'auto' || style.overflow === 'auto') {
                         el.scrollTo({ top: val, behavior: behavior });
                    }
                }
            });
        };

        const scrollUp = () => { scrollNuclear(false); };
        const scrollDown = () => { scrollNuclear(true); };

        // 5. RESTORED & ANIMATED (V330)
        const btnUp = createBtn('fas fa-arrow-up', 'Inicio', scrollUp, '#4B22DD');
        const btnDown = createBtn('fas fa-arrow-down', 'Final', scrollDown, '#4B22DD');

        navContainer.appendChild(btnUp);
        navContainer.appendChild(btnDown);
        
        // CSS ANIMATION INJECTION
        const style = doc.createElement('style');
        style.innerHTML = `
            @keyframes fadeInElevator {
                0% { opacity: 0; transform: translateY(10px); }
                100% { opacity: 1; transform: translateY(0); }
            }
        `;
        doc.head.appendChild(style);

        // INITIAL STATE: Hidden -> Animation handles reveal
        navContainer.style.opacity = '0';
        // Delay 2s, Duration 0.5s
        navContainer.style.animation = 'fadeInElevator 0.5s ease 2s forwards';

        // 6. INJECT
        doc.body.appendChild(navContainer);
        console.log("🛗 [Elevator V231] Mounted & Animating...");

        // 7. ENSURE CSS
        if (!doc.getElementById('fa-v6-core')) {
            const link = doc.createElement('link');
            link.id = 'fa-v6-core';
            link.rel = 'stylesheet';
            link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
            doc.head.appendChild(link);
        }
    };

    setTimeout(setupElevator, 1500);
</script>
""", height=0)


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
    """Removes all markdown baggage for a perfect clean copy (V3)."""
    import re
    if not text: return ""
    # 1. Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # 2. Headers #
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 3. Bold/Italic ** * __ _
    text = re.sub(r'(\*\*|__|\*|_)', '', text)
    # 4. Bullets / Lists
    text = re.sub(r'^[ \t]*[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    # 5. Blockquotes >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 6. Links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 7. Code blocks `
    text = text.replace("`", "")
    # 8. @ symbols
    text = text.replace("@", "")
    # 9. Excessive empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
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
    from db_handler import get_course_full_context
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
# --- INITIALIZATION UTILS (Cached) ---
from transcriber import Transcriber
from study_assistant import StudyAssistant

@st.cache_resource
def get_transcriber_engine(key, model_choice="gemini-2.0-flash", breaker="V6"):
    return Transcriber(key, model_name=model_choice, cache_breaker=breaker)

@st.cache_resource
def get_assistant_engine(key, model_choice="gemini-2.0-flash", breaker="V19"):
    return StudyAssistant(key, model_name=model_choice, cache_breaker=breaker)

api_key = saved_key
transcriber = None
assistant = None

if api_key:
    try:
        # Force fresh engines with explicit model choice
        # REVERTING TO CLASSIC V9 LOGIC
        transcriber = get_transcriber_engine(api_key, model_choice="gemini-2.0-flash", breaker="V13_Classic") 
        assistant = get_assistant_engine(api_key, model_choice="gemini-2.0-flash", breaker="V19")
    except Exception as e:
        st.error(f"Error al iniciar IA: {e}")

    # DEBUG: Confirm Version to User (DISABLED BY REQUEST)
    # if 'v9_classic_toast_shown' not in st.session_state:
    #     st.toast("🦄 Sistema IA: V9.0 (Clásico) Restaurado", icon="✅")
    #     st.session_state['v9_classic_toast_shown'] = True


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

    /* HIDE STREAMLIT STATUS WIDGET & DECORATION */
    div[data-testid="stStatusWidget"] { visibility: hidden !important; }
    div[data-testid="stDecoration"] { visibility: hidden !important; }

    /* --- ULTIMATE KILL TO LOADING OVERLAY (NO MORE WHITE TRANSPARENCY) --- */
    /* Target every possible container Streamlit uses for the "dimming" effect */
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMainViewContainer"],
    [data-test-script-state="running"] [data-testid="stAppViewBlockContainer"],
    [data-test-script-state="running"] [data-testid="stAppViewContainer"],
    [data-test-script-state="running"] .stApp,
    section.main,
    div.block-container,
    .stApp > div {
        opacity: 1 !important;
        filter: none !important;
        transition: none !important;
    }
    
    /* Force background to stay solid and kill any covering pseudo-elements */
    .stApp::before, .stApp::after, 
    [data-testid="stAppViewContainer"]::before,
    [data-testid="stAppViewContainer"]::after {
        display: none !important;
        opacity: 0 !important;
    }

    /* --- GLOBAL VARIABLES (Moved to Top) --- */
    /* :root variables are now prevalent globally to prevent FOUC */

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



    /* GLOBAL CONTENT POSITIONING - Move all tabs MUCH higher */
    section.main > div {
        padding-top: 0 !important;
        margin-top: -50px !important;
    }
    
    [data-testid="stAppViewContainer"] > section.main {
        padding-top: 0 !important;
    }
    
    /* Override block container padding completely */
    .block-container {
        padding-top: 0 !important;
        margin-top: -50px !important;
    }
    
    /* Target the main content wrapper */
    section[data-testid="stMain"] {
        padding-top: 0 !important;
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

    /* LOGIN FORM BUTTON - GREEN FORCE (Submit Only - No SVGs) */
    [data-testid="stForm"] button:not(:has(svg)) {
        background-color: #6CC04A !important;
        border: none !important;
        color: white !important;
    }
    [data-testid="stForm"] button:not(:has(svg)):hover {
        background-color: #5ab03a !important;
    }

    /* --- GLOBAL HEADERS (BRANDING) --- */
    h1, h2, h3, h4, h5, h6 {
        color: #4B22DD !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Specific Streamlit markdown headers */
    /* Specific Streamlit markdown headers */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #4B22DD !important;
    } 

    div.stButton > button:active {
        background-color: #2a1275 !important;
        transform: translateY(0);
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# --- EMERGENCY SIDEBAR RESET ---
# Forces Sidebar buttons to be normal size, ignoring any global leaks
st.markdown("""
<style>
section[data-testid="stSidebar"] div.stButton > button {
    height: auto !important;
    width: 100% !important;
    padding: 0.5rem 1rem !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    display: flex !important;
    flex-direction: row !important; /* Standard row for text */
    align-items: center !important;
    justify-content: center !important;
    border-radius: 8px !important;
}

/* Reset ::first-line for Sidebar to avoid giant emojis if leak persists */
section[data-testid="stSidebar"] div.stButton > button::first-line,
section[data-testid="stSidebar"] div.stButton > button > div::first-line,
section[data-testid="stSidebar"] div.stButton > button p::first-line {
    font-size: inherit !important;
    line-height: inherit !important;
    font-weight: inherit !important;
}

/* --- MAIN AREA BUTTON RESET (Protect Dashboard from Library CSS) --- */
/* Reset ALL buttons in main area EXCEPT those in library tab */
section[data-testid="stMain"] div.stButton > button {
    height: auto !important;
    padding: 0.6rem 2rem !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: normal !important;
}

/* Reset ::first-line for main area buttons */
section[data-testid="stMain"] div.stButton > button::first-line,
section[data-testid="stMain"] div.stButton > button > div::first-line,
section[data-testid="stMain"] div.stButton > button p::first-line {
    font-size: inherit !important;
    line-height: inherit !important;
    font-weight: inherit !important;
}
</style>
""", unsafe_allow_html=True)

# Hidden duplicate button removed.
# Duplicate button cleanup complete.


# Hidden duplicate button removed.
# Duplicate button cleanup complete.

# Sidebar
with st.sidebar:
    # --- V252: FORCE ARROW INJECTION ---
    inject_navigation_arrows()
    
    # st.caption("🚀 v3.3 (API Fix)") # Removed per user request
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
    if st.session_state.get('user'):
        # User Info (Consistent spacing)
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 30px; margin-bottom: 20px;">
            <div style="font-size: 24px;">👤</div>
            <div style="font-size: 14px; color: #31333F; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{st.session_state['user'].email}">
                {st.session_state['user'].email}
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Cerrar sesión", key="logout_btn", use_container_width=True):
            st.session_state['force_logout'] = True 
            st.session_state['user'] = None
            if 'supabase_session' in st.session_state: del st.session_state['supabase_session']
            
            # --- V239: QUERY PARAM REDIRECT (KILL AUTO-LOGIN LOOP) ---
            st.query_params['logout'] = 'true'
            
            # Try to delete via cookie manager
            try:
                cookie_manager.delete("supabase_refresh_token")
            except: pass
            
            components.html("""
            <script>
                const killCookie = (name) => {
                    const domain = window.location.hostname;
                    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/;';
                    window.parent.document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/;';
                };
                killCookie('supabase_refresh_token');
                window.parent.localStorage.clear();
                window.parent.sessionStorage.clear();
            </script>
            """, height=0)
            
            time.sleep(0.5)
            st.rerun()

    st.markdown('<div class="aesthetic-sep"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:15px;"></div>', unsafe_allow_html=True)

    # --- MODO ESTUDIO & LEYENDA ---
    study_mode = st.toggle("Modo Estudio (Resaltadores) 🎨", value=True, help="Activa o desactiva los colores de estudio.", key="study_mode_toggle")
    
    # Combined block for toggle logic and legend
    with st.expander("📚 Leyenda de Colores", expanded=study_mode):
        st.markdown("""
            <div style="font-size: 0.8rem; line-height: 1.4;">
                <div style="margin-bottom:6px;"><span style="background-color: #ffcccc; color: #900; border: 1px solid #ff9999; padding: 1px 4px; border-radius: 3px; font-weight: bold;">Rojo</span>: Definiciones.</div>
                <div style="margin-bottom:6px;"><span style="background-color: #cce5ff; color: #004085; border: 1px solid #b8daff; padding: 1px 4px; border-radius: 3px; font-weight: bold;">Azul</span>: Ejemplos.</div>
                <div style="margin-bottom:6px;"><span style="background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; padding: 1px 4px; border-radius: 3px; font-weight: bold;">Verde</span>: Notas.</div>
                <div style="margin-bottom:6px;"><span style="background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 1px 4px; border-radius: 3px; font-weight: bold;">Amarillo</span>: Datos.</div>
                <div style="margin-bottom:6px;"><span style="background-color: #e2d9f3; color: #512da8; border: 1px solid #d1c4e9; padding: 1px 4px; border-radius: 3px; font-weight: bold;">Púrpura</span>: Claves.</div>
            </div>
        """, unsafe_allow_html=True)

    # LOGIC: Python-Based Toggle (Clean & Synchronous)
    # When toggle is changed, script reruns. We simply inject the hiding CSS if needed.
    if not study_mode:
        st.markdown("<style>span[style*='background-color'] { background-color: transparent !important; color: inherit !important; border: none !important; padding: 0 !important; }</style>", unsafe_allow_html=True)
        st.markdown("""
            <style>
            .sc-base, .sc-example, .sc-note, .sc-data, .sc-key,
            .stApp .sc-base, .stApp .sc-example, .stApp .sc-note, .stApp .sc-data, .stApp .sc-key {
                background-color: transparent !important;
                padding: 0 !important;
                color: inherit !important;
                border: none !important;
                font-weight: inherit !important;
            }
            </style>
        """, unsafe_allow_html=True)

    # Fixed version marker removed




    # --- 2. HISTORIAL DE CHATS (DISABLED) ---
    if False and st.session_state.get('user'):
        pass
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
                    
                    # UPDATE URL
                    try:
                        if hasattr(st, 'query_params'):
                            st.query_params['chat_id'] = str(new_sess['id'])
                        else:
                            st.experimental_set_query_params(chat_id=str(new_sess['id']))
                    except: pass
                    
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
                    
                    # UPDATE URL
                    try:
                        if hasattr(st, 'query_params'):
                            st.query_params['chat_id'] = str(sess['id'])
                        else:
                            st.experimental_set_query_params(chat_id=str(sess['id']))
                    except: pass
                    
                    st.rerun()

            # VIEW ALL BUTTON ALWAYS VISIBLE
            if True:
                if st.button("📂 Ver todo el historial...", help="Ir al panel de gestión completo", use_container_width=True):
                    st.session_state['redirect_target_name'] = "Inicio"
                    st.session_state['force_chat_tab'] = True
                    st.session_state['dashboard_mode'] = 'history' # Activate History View in Dashboard
                    st.rerun()

            # Management for Active Session
            if st.session_state['current_chat_session']:
                st.caption("Gestionar Actual:")
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
                
                # CLEAR URL
                try:
                    if hasattr(st, 'query_params'):
                        if 'chat_id' in st.query_params: del st.query_params['chat_id']
                    else:
                        st.experimental_set_query_params()
                except: pass
                
                st.rerun()

        # --- BULK DELETE (DISABLED) ---
        if False and st.session_state.get('user'):
            with st.expander("🗑️ Gestión Masiva", expanded=False):
                # 1. Multi-Select with Invisible Uniqueness Hack
                # User wants clean names, but Streamlit merges duplicates.
                # Solution: Append zero-width spaces to duplicates.
                
                # Check if sessions exists (safety)
                if 'sessions' in locals():
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



    st.markdown('<div class="aesthetic-sep"></div>', unsafe_allow_html=True)

    # --- 2.5 API KEY PERSONALIZADA (REDESIGNED) ---
    st.markdown("#### 🔑 API Key Personalizada")
    st.caption("Usa tu propia API de Gemini para evitar límites compartidos.")
    
    # Add spacing
    st.write("")
    
    # Check if user has custom key in session
    custom_key = st.session_state.get('custom_api_key', '')
    
    with st.expander("⚙️ Configurar API Key", expanded=False):
        st.write("")  # Top padding
        
        api_input = st.text_input(
            "Tu API Key de Google:", 
            value=custom_key,
            type="password",
            placeholder="AIza...",
            key="api_key_input_sidebar",
            help="Obtén tu key gratis en: https://aistudio.google.com/app/apikey"
        )
        
        st.write("")  # Spacing before buttons
        
        # Custom HTML buttons for perfect alignment
        st.markdown("""
        <style>
        .api-key-buttons {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            justify-content: stretch;
        }
        .api-key-buttons button {
            flex: 1;
            height: 2.5rem;
            border: none;
            border-radius: 0.5rem;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-save {
            background: #4B22DD;
            color: white;
        }
        .btn-save:hover {
            background: #3A1AAA;
            transform: scale(1.02);
        }
        .btn-clear {
            background: #E53935;
            color: white;
        }
        .btn-clear:hover {
            background: #C62828;
            transform: scale(1.02);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Use columns for Streamlit buttons with fixed alignment
        col_save, col_clear = st.columns([1, 1], gap="small")
        with col_save:
            if st.button("✅", use_container_width=True, type="primary", key="btn_save_api", help="Guardar API Key"):
                if api_input and api_input.startswith("AIza"):
                    st.session_state['custom_api_key'] = api_input
                    st.cache_resource.clear()
                    st.success("✅ Key guardada!")
                    st.rerun()
                else:
                    st.error("Key inválida")
        
        with col_clear:
            if st.button("❌", use_container_width=True, type="primary", key="btn_clear_api", help="Borrar API Key"):
                st.session_state['custom_api_key'] = None
                st.cache_resource.clear()
                st.info("Usando key del sistema")
                st.rerun()
        
        st.write("")  # Bottom padding
    
    # Show status with better spacing
    st.write("")
    if st.session_state.get('custom_api_key'):
        st.success("🔐 Usando tu API Key personal", icon="✅")
    else:
        st.info("🌐 Usando API Key compartida del sistema")

    st.write("")  # Extra spacing after section
    st.markdown('<div class="aesthetic-sep"></div>', unsafe_allow_html=True)

    # --- 3. SPOTLIGHT ACADÉMICO ---
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

    st.markdown('<div class="aesthetic-sep"></div>', unsafe_allow_html=True)

    # --- 4. ESPACIO DE TRABAJO ---
    st.markdown("#### 📂 Espacio de Trabajo")
    st.caption("Diplomado Actual:")
    user = st.session_state.get('user')
    if not user:
        st.stop()
    
    # Robust ID Extraction (Dict or Object)
    current_user_id = user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)
    
    if not current_user_id:
        st.error("Error de Sesión: Usuario inválido.")
        st.stop()

    db_courses = get_user_courses(current_user_id) or [] # V199 Fix: Default to list
    course_names = [c['name'] for c in db_courses]
    course_map = {c['name']: c['id'] for c in db_courses}
    if not course_names: course_names = []
    # RECOVERY LOGIC (Persistence)
    if 'current_course' not in st.session_state or (st.session_state['current_course'] not in course_names and st.session_state['current_course'] is not None):
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
        if st.session_state.get('current_course') != selected_option:
            st.session_state['last_transcribed_file'] = None # Reset on change
        st.session_state['current_course'] = selected_option
        st.session_state['current_course_id'] = course_map[selected_option]
        update_last_course(selected_option)
        # --- ACTIONS (RENAME / DELETE) ---
        
        # RENAME
        with st.expander("✏️ Renombrar"):
            rename_input = st.text_input("Nuevo nombre:", value=st.session_state['current_course'], key="rename_input_sb")
            if rename_input and rename_input != st.session_state['current_course']:
                # Simple sanitize
                safe_rename = "".join([c for c in rename_input if c.isalnum() or c in (' ', '-', '_')]).strip()
                
                # DB Update
                from db_handler import rename_course
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
                            from db_handler import delete_course
                            success_count = 0
                            
                            for c_name in courses_to_delete:
                                c_id_del = course_map.get(c_name)
                                if c_id_del:
                                    if delete_course(c_id_del):
                                        success_count += 1
                            
                            if success_count > 0:
                                st.success(f"¡{success_count} cursos borrados!")
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
    components.html("""
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
    
    // --- CONSULTANT FIX: LOCAL STORAGE PERSISTENCE (Option B) ---
    function setupTabPersistence() {
        const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
        
        // 1. ADD LISTENERS (Save on click)
        tabs.forEach(tab => {
            tab.onclick = () => {
                localStorage.setItem("my_active_tab", tab.innerText);
            };
        });

        // 2. RESTORE (Click saved tab)
        const savedTab = localStorage.getItem("my_active_tab");
        if (savedTab) {
             for (const tab of tabs) {
                 if (tab.innerText === savedTab && tab.getAttribute('aria-selected') !== 'true') {
                     tab.click();
                     break;
                 }
             }
        }
    }
    
    // Run periodically to catch re-renders
    setTimeout(setupTabPersistence, 1000);
    setInterval(setupTabPersistence, 3000); 
    
    </script>
    """, height=0)

    # --- DUAL NAVIGATION ARROWS ---
    inject_navigation_arrows()

    # --- TABS DEFINITION ---
# --- TABS DEFINITION ---
# NEW: "Inicio" is the Dashboard Tab
# NEW: "Explorador Didáctico" replaces Apuntes/Guide
tab_home, tab1, tab_didactic, tab_quiz, tab_lib = st.tabs([
    "🏠 Inicio", 
    "🎤 Transcriptor", 
    "📘 Didáctica", 
    "📝 Quiz", 
    "📂 Biblioteca"
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

    st.markdown(f"Estás estudiando: **{current_c_name.strip()}**")
    
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
                        
                        # UPDATE URL
                        try:
                            if hasattr(st, 'query_params'):
                                st.query_params['chat_id'] = str(chat['id'])
                            else:
                                st.experimental_set_query_params(chat_id=str(chat['id']))
                        except: pass

                        st.rerun()
        else:
            st.warning("No se encontraron chats.")
            
    elif current_c_id:
        # --- DASHBOARD V2: THE PREMIUM EXPERIENCE ---
        
        # 1. UNIVERSAL SEARCH HERO
        st.markdown("<h2 style='text-align: center; color: #4B22DD;'>¿Qué quieres aprender hoy?</h2>", unsafe_allow_html=True)
        search_q = st.text_input("🔍 Busca archivos, chats o carpetas...", placeholder="Ej: Historia del Arte, Ecuaciones, Resumen...", label_visibility="collapsed")
        
        if search_q:
            results = search_global(st.session_state['user'].id, current_c_id, search_q)
            if results:
                st.markdown(f"##### 🎯 Resultados para: '{search_q}'")
                for r in results:
                    with st.container(border=True):
                        c1, c2 = st.columns([0.85, 0.15])
                        c1.markdown(f"**{r['icon']} {r['name']}**  \n<small style='color:grey'>{r['preview']}</small>", unsafe_allow_html=True)
                        if c2.button("Ir", key=f"go_{r['id']}"):
                            # Simple Navigation Logic
                            if r['type'] == 'chat':
                                # Restore chat logic
                                st.session_state['current_chat_session'] = {'id': r['id'], 'name': r['name']}
                                st.session_state['tutor_chat_history'] = []
                                st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                                st.session_state['force_chat_tab'] = True
                                
                                # Update URL if possible
                                try:
                                    if hasattr(st, 'query_params'): st.query_params['chat_id'] = str(r['id'])
                                    else: st.experimental_set_query_params(chat_id=str(r['id']))
                                except: pass
                                
                                st.rerun()
                            elif r['type'] == 'file':
                                # Jump to Library (Requires logic, for now just toast)
                                st.toast(f"Ve a la Biblioteca > {r['name']}")
            else:
                st.info("No encontramos nada. Intenta otra palabra clave.")
            st.divider()

        # 2. KEY METRICS & INSIGHTS ROW
        stats = get_dashboard_stats(current_c_id, st.session_state['user'].id)
        
        m1, m2, m3 = st.columns([1, 1, 2])
        m1.metric("📚 Archivos", stats.get('files', 0), delta="Total")
        m2.metric("💬 Chats", stats.get('chats', 0), delta="Sesiones")
        
        with m3:
            # AI Insight Card (Mockup logic for now)
            files_count = stats.get('files', 0)
            if files_count > 5:
                msg = "🔥 ¡Vas muy bien! Tienes una buena base de conocimientos."
            elif files_count > 0:
                msg = "💡 Sube más archivos para que la IA sea más inteligente."
            else:
                msg = "🚀 Empieza subiendo tu primer PDF en la Biblioteca."
            
            st.info(f"**Insight Diario:**\n\n{msg}", icon="🤖")



        # 3. ADVANCED DASHBOARD WIDGETS (E-Learning Style)
        
        # --- PREPARE DATA ---
        all_units = get_units(current_c_id)
        all_files = get_course_files(current_c_id)
        
        # Calculate Counts per Unit (Optimization: Python-side grouping)
        unit_counts = {u['id']: 0 for u in all_units}
        for f in all_files:
            if f.get('unit_id') in unit_counts:
                unit_counts[f['unit_id']] += 1
                
        # --- WIDGET A: LEARNING PATH (Route - COMPACT) ---
        st.write("")
        st.subheader("🗺️ Tu Ruta de Aprendizaje (Activa)")
        
        if all_units:
            # 1. Sort units by content count (Most active first)
            # This ensures the dashboard always shows where the work is happening
            sorted_units = sorted(all_units, key=lambda x: unit_counts.get(x['id'], 0), reverse=True)
            
            # 2. Slice Top 4
            top_units = sorted_units[:4]
            hidden_count = len(sorted_units) - 4
            
            # Grid Layout for Units
            u_cols = st.columns(2)
            for i, unit in enumerate(top_units):
                count = unit_counts.get(unit['id'], 0)
                # Calculate simple progress
                progress = min(1.0, count / 5) 
                
                with u_cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**📂 {unit['name']}**")
                        st.progress(progress)
                        st.caption(f"{count} Recursos")
                        
            # 3. See All Link (if needed)
            if hidden_count > 0:
                if st.button(f"Ver {hidden_count} carpetas más en la Biblioteca →", key="btn_see_all_units", type="tertiary"):
                     st.session_state['redirect_target_name'] = "Biblioteca"
                     st.session_state['force_chat_tab'] = True
                     st.session_state['lib_auto_open_upload'] = False 
                     # Reset to Root
                     st.session_state['lib_current_unit_id'] = None
                     st.session_state['lib_breadcrumbs'] = []
                     st.rerun()
                     
        else:
            st.info("Aún no tienes unidades creadas. Ve a la Biblioteca para organizar tu curso.")

        # --- WIDGET B: COMPACT CONTENT ROW (News + Actions) ---
        st.write("")
        st.write("")
        
        # Layout: 70% News | 30% Actions (Side-by-Side)
        c_news, c_actions = st.columns([0.7, 0.3], gap="medium")
        
        # --- LEFT: NEWS CAROUSEL ---
        with c_news:
            st.subheader("🆕 Novedades")
            recents = all_files[:3] # Limit to 3 for space
            
            if recents:
                r_cols = st.columns(3)
                for i, f in enumerate(recents):
                    with r_cols[i]:
                        with st.container(border=True):
                            # Icon Logic
                            icon = "📄"
                            if f['type'] == 'transcript': icon = "📹"
                            elif "quiz" in f['name'].lower(): icon = "📝"
                            
                            st.markdown(f"**{icon} {f['name'][:15]}{'...' if len(f['name'])>15 else ''}**")
                            if st.button("Ver", key=f"btn_rec_{f['id']}", use_container_width=True):
                                    # DEEP LINKING LOGIC
                                    st.session_state['redirect_target_name'] = "Biblioteca"
                                    st.session_state['force_chat_tab'] = True
                                    
                                    # 1. Set Folder Context
                                    target_unit_id = f.get('unit_id')
                                    if target_unit_id:
                                        # Find Unit Name
                                        u_name = "Carpeta"
                                        for u in all_units:
                                            if u['id'] == target_unit_id:
                                                u_name = u['name']
                                                break
                                        
                                        st.session_state['lib_current_unit_id'] = target_unit_id
                                        st.session_state['lib_current_unit_name'] = u_name
                                        st.session_state['lib_breadcrumbs'] = [{'id': target_unit_id, 'name': u_name}]
                                    
                                    # 2. Set File Open State (Auto-Expand)
                                    st.session_state[f"edit_mode_{f['id']}"] = True
                                    
                                    st.rerun()
            else:
                st.caption("Sube archivos para verlos aquí.") 

        # --- RIGHT: QUICK ACTIONS (Vertical) ---
        with c_actions:
            st.subheader("⚡ Acciones")
            # Vertical Stack naturally
            if st.button("📤 Subir Archivo", use_container_width=True):
                 st.session_state['redirect_target_name'] = "Biblioteca"
                 st.session_state['force_chat_tab'] = True
                 st.session_state['lib_auto_open_upload'] = True
                 st.rerun()
                 
            if st.button("📝 Crear Quiz", use_container_width=True):
                 st.session_state['redirect_target_name'] = "Zona Quiz"
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
    components.html(f"""
    <script>
        setTimeout(() => {{
            try {{
                const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
                const targetName = "{st.session_state.get('redirect_target_name', 'Ayudante de Tareas')}"; 
                for (const tab of tabs) {{
                    if (tab.innerText.includes(targetName)) {{
                        tab.click();
                        // Also sync URL immediately to be sure
                        const newUrl = new URL(window.parent.location);
                        newUrl.searchParams.set('tab', tab.innerText);
                        window.parent.history.pushState({{}}, '', newUrl);
                        break;
                    }}
                }}
            }} catch(e) {{ console.log(e); }}
        }}, 500);
        // Retry logic for slow loaders
        setTimeout(() => {{ 
             const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
             const targetName = "{st.session_state.get('redirect_target_name', 'Ayudante de Tareas')}"; 
             for (const tab of tabs) {{ if (tab.innerText.includes(targetName)) tab.click(); }}
        }}, 2000);
        setTimeout(() => {{ 
             const tabs = window.parent.document.querySelectorAll('button[data-testid="stTab"]');
             const targetName = "{st.session_state.get('redirect_target_name', 'Ayudante de Tareas')}"; 
             for (const tab of tabs) {{ if (tab.innerText.includes(targetName)) tab.click(); }}
        }}, 5000); 
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
    from db_handler import get_units, create_unit
    
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

        c_id = st.session_state.get('current_course_id')
        
        # --- LAST PROCESSED DISPLAY (ALWAYS VISIBLE) ---
        if st.session_state['last_transcribed_file'] is None and c_id:
            st.session_state['last_transcribed_file'] = get_last_transcribed_file_name(c_id)
        
        if st.session_state['last_transcribed_file']:
            # V339: Layout Fix - Aesthetic Spacing
            # More gap ("large"), slightly different ratio to push button right but keeping it accessible
            c_ban, c_btn = st.columns([0.70, 0.30], gap="large", vertical_alignment="center")

            with c_ban:
                st.markdown(f"""
                    <div style="background-color: #EBF5FF; border: 2px solid #4B22DD; border-left: 8px solid #4B22DD; padding: 15px; border-radius: 12px; margin-bottom: 0px; box-shadow: 0 4px 12px rgba(75, 34, 221, 0.1);">
                        <div style="color: #4B22DD; font-weight: 800; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">
                            🎯 Último archivo procesado:
                        </div>
                        <div style="color: #1a1a1a; font-size: 1.1rem; font-weight: 600;">
                            {st.session_state['last_transcribed_file']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # RENDER BUTTON NEXT TO BANNER
            with c_btn:
                 # 3. CLEAR VIEW (Simple)
                 # Add top padding if vertical_alignment isn't perfect for some themes
                 if st.button("🧹 Limpiar Vista", key="clean_view_only_v2", help="Limpia la pantalla", use_container_width=True):
                    st.session_state['transcript_history'] = []
                    st.session_state['last_transcribed_file'] = None
                    st.query_params.clear() # V340: Fix AttributeError
                    import uuid
                    st.session_state['transcriptor_key'] = str(uuid.uuid4()) # Reset uploader
                    st.rerun()
            
            # Spacing below banner/button block to separate from Uploader
            st.write("")
            st.write("")
        
        # Dynamic Key for Uploader Reset
        if 'transcriptor_key' not in st.session_state: st.session_state['transcriptor_key'] = "up1"
        
        # File Uploader
        # Added .waptt (WhatsApp), .opus, .aac, .wma
        uploaded_files = st.file_uploader("Upload", type=['mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav', 'm4a', 'flac', 'ogg', 'opus', 'waptt', 'aac', 'wma'], accept_multiple_files=True, key=st.session_state['transcriptor_key'], label_visibility="collapsed")
        
        if uploaded_files:
            # VISUAL MODE TOGGLE (DISABLED V178: User Request - Too slow/Tokens limit)
            # st.caption("Opciones de Procesamiento:")
            # use_visual = st.checkbox(...) 
            use_visual = False # Hardcoded off for speed
            # st.divider()

            # --- MEMORY SAFETY CHECK (TRAFFIC CONTROL) ---
            # --- MEMORY SAFETY CHECK (TRAFFIC CONTROL) ---
            total_size_bytes = sum(f.size for f in uploaded_files)
            total_size_mb = total_size_bytes / (1024 * 1024)
            SAFE_RAM_LIMIT_MB = 1500 # Hard Limit (Server Protection)
            WARNING_LIMIT_MB = 500   # User Experience Limit (Avoid "Oh no")
            
            if total_size_mb > SAFE_RAM_LIMIT_MB:
                st.error(
                    f"⛔ **LÍMITE EXCEDIDO ({total_size_mb:.0f} MB)**\n\n"
                    f"El servidor no puede procesar más de {SAFE_RAM_LIMIT_MB} MB de golpe.\n"
                    f"👉 **Solución:** Sube los archivos en grupos más pequeños (ej: de 3 en 3).", 
                    icon="🛑"
                )
                st.stop() # Force execution stop
            elif total_size_mb > WARNING_LIMIT_MB:
                st.warning(
                    f"⚠️ **ZONA DE RIESGO ({total_size_mb:.0f} MB)**\n\n"
                    f"Estás subiendo muchos megas. Si ves la pantalla de 'Oh no', reduce la cantidad.\n"
                    f"Consejo: Convierte videos pesados a MP3 antes de subir para ir más rápido.",
                    icon="⚖️"
                )

            # --- FOLDER SELECTION ---
            c_id = st.session_state.get('current_course_id')
            selected_unit_id = None
            
            if c_id:
                # from db_handler import get_units (Available Global)
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

            # V208: Sound on Upload Complete
            if 'last_upload_count' not in st.session_state:
                st.session_state['last_upload_count'] = 0
            
            curr_count = len(uploaded_files)
            if curr_count > st.session_state['last_upload_count']:
                # New file arrived!
                play_sound('start')
                st.session_state['last_upload_count'] = curr_count
            elif curr_count < st.session_state['last_upload_count']:
                # Files removed, just sync
                st.session_state['last_upload_count'] = curr_count

            st.info(f"📂 {len(uploaded_files)} archivo(s) cargado(s).")
            
            # --- RENAME FEATURE ---
            file_renames = {}
            if uploaded_files:
                st.caption(f"💡 **Modo Lote:** {len(uploaded_files)} archivos en cola. Se procesarán uno por uno en la carpeta seleccionada.")
                with st.expander("✍🏻 Renombrar archivos (Opcional)", expanded=True):
                    for i, uf in enumerate(uploaded_files):
                         base = os.path.splitext(uf.name)[0]
                         new_n = st.text_input(f"Nombre para {uf.name}:", value=base, key=f"ren_{i}")
                         file_renames[uf.name] = new_n
            

            if st.button("▶️ Iniciar Transcripción Inteligente", type="primary", key="btn_start_transcription", use_container_width=True, disabled=(not selected_unit_id)):
                try:
                    # V207: Start Sound (Blip)
                    play_sound('start')
                    
                    if not selected_unit_id:
                        st.error("Error: Carpeta no seleccionada.")
                    else:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        js_bridge = st.empty() # V295: Dedicated slot for JS bridge to avoid vertical space accumulation
                        import time
                        from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
                        
                        # --- SMART BATCH LOGIC ---
                        # User Request: "Procesar 40 videos de 3 en 3 automáticamente"
                        all_files = uploaded_files
                        total_files = len(all_files)
                        # Reduce Batch Size to 1 to prevent Memory Overload with 700MB videos
                        BATCH_SIZE = 1
                        
                        for start_idx in range(0, total_files, BATCH_SIZE):
                            batch = all_files[start_idx : start_idx + BATCH_SIZE]
                            batch_num = (start_idx // BATCH_SIZE) + 1
                            total_batches = (total_files + BATCH_SIZE - 1) // BATCH_SIZE
                            
                            # Update Status for Lote
                            status_text.markdown(f"**🚀 Procesando Archivo {batch_num} de {total_files}**")
                            log_debug(f"--- BATCH {batch_num} START ---")
                            # Clean UI: Removed raw DEBUG print
                            
                            for batch_idx, file in enumerate(batch):
                                current_file_num = start_idx + batch_idx + 1
                                t_unit_id = selected_unit_id 
                                
                                # CHECK TRANSCRIBER EARLY
                                if transcriber is None:
                                    raise Exception("El motor de IA no está conectado. Verifica tu API Key.")

                                # V217: Defensive File Handling (UUID + Guard)
                                safe_ext = os.path.splitext(file.name)[1]
                                temp_path = f"temp_upload_{uuid.uuid4()}{safe_ext}"
                                log_debug(f"Procesando: {file.name} -> {temp_path} ({file.size} bytes)")
                                
                                try:
                                    # Memory-Safe Write (Chunk by Chunk) to avoid RAM duplication
                                    log_debug("Inicio escritura disco...")
                                    file.seek(0)  # CRITICAL FIX: Ensure pointer is at start
                                    with open(temp_path, "wb") as f:
                                        # Write in 4MB chunks
                                        while True:
                                            chunk = file.read(4 * 1024 * 1024)
                                            if not chunk: break
                                            f.write(chunk)
                                            del chunk # V304: Explicit Delete
                                    log_debug("Escritura disco OK.")
                                    
                                    # V302: Memory Optimization for Large Files
                                    import gc
                                    gc.collect()
                                    
                                except Exception as e:
                                    log_debug(f"ERROR ESCRITURA: {e}")
                                    st.error(f"❌ Error CRÍTICO escribiendo disco: {e}")
                                    # Cleanup if write failed
                                    if os.path.exists(temp_path):
                                        os.remove(temp_path)
                                    continue
                                
                                # RETRY LOGIC (Quota Protection)
                                max_retries = 3
                                success = False
                                attempt = 0
                                
                                while attempt < max_retries and not success:
                                    try:
                                        status_text.markdown(f"**⚡ Transcribiendo: {file.name}...**")
                                        
                                        def update_ui(msg, prog):
                                            # Update both text and bar
                                            pct = int(prog * 100)
                                            
                                            # V350: Better Feedback (File X of Y)
                                            # We emphasize the CURRENT file clearly
                                            file_prefix = f"📄 Archivo {current_file_num}/{total_files}: {file.name}"
                                            
                                            status_text.markdown(f"**{file_prefix}**\n\n⚡ {msg} ({pct}%)")
                                            progress_bar.progress(prog)
                                            
                                            # --- V257: SIMPLIFIED UPDATE ---
                                            try:
                                                # Include file name in the global loader too
                                                clean_prefix = f"[{current_file_num}/{total_files}]"
                                                msg_clean = f"{clean_prefix} {msg}".replace("'", "")
                                                
                                                with js_bridge:
                                                    components.html(f"""
                                                        <script>
                                                            window.parent.document.body.setAttribute('data-transcription-message', '{msg_clean}');
                                                            window.parent.document.body.setAttribute('data-transcription-percentage', '{pct}');
                                                        </script>
                                                    """, height=0)
                                            except:
                                                pass
                                        
                                        # Process
                                        log_debug(f"Iniciando transcriber.process_video (Intento {attempt+1})")
                                        # FORCE GC
                                        import gc
                                        gc.collect()

                                        # Determine visual mode
                                        is_video = safe_ext.lower() in ['.mp4', '.mov', '.avi', '.mkv']
                                        use_visual = (is_video and st.session_state.get('visual_mode', False))

                                        trans_text = transcriber.process_video(temp_path, visual_mode=use_visual, progress_callback=update_ui)
                                        log_debug("Transcriber success.")

                                        # Validation check
                                        if trans_text.startswith("[ERROR]"):
                                            raise Exception(trans_text)
                                            
                                        # V290: Strict Anti-Silent-Failure Check
                                        if not trans_text or len(trans_text.strip()) < 20:
                                             raise Exception("La IA devolvió una transcripción vacía. Es posible que el audio no se haya procesado correctamente o esté en silencio.")
                                        
                                        # The new process_video returns TEXT directly, not a path!
                                        # (Review transcriber.py: return response.text or full_text)
                                        
                                        # So we skip the open() step.
                                        
                                        custom_n = file_renames.get(file.name, os.path.splitext(file.name)[0])
                                        
                                        # V198 Fix: Sanitize filename (remove slashes/colons from dates)
                                        # User reported error with "2024/11/06 18:00"
                                        custom_n = custom_n.replace("/", "-").replace("\\", "-").replace(":", "-").replace("|", "-")
                                        
                                        final_name = f"{custom_n}.txt"
                                        
                                        # ROBUST UPLOAD: Retry with timestamp if fails (likely duplicate)
                                        saved_id = upload_file_to_db(t_unit_id, final_name, trans_text, "transcript")
                                        if not saved_id:
                                            # Retry with suffix
                                            import time
                                            suffix = int(time.time())
                                            final_name_retry = f"{custom_n}_{suffix}.txt"
                                            saved_id = upload_file_to_db(t_unit_id, final_name_retry, trans_text, "transcript")
                                            
                                            if saved_id:
                                                st.toast(f"⚠️ Nombre duplicado. Guardado como: {final_name_retry}", icon="📝")
                                                final_name = final_name_retry
                                            else:
                                                st.error(f"❌ Error CRÍTICO: No se pudo guardar '{custom_n}' en la base de datos.")
                                        
                                        if saved_id:
                                            # st.toast(f"✅ Listo: {final_name}")  # Removed to avoid spam
                                            # V336: Store ID for Deep Clean
                                            st.session_state['transcript_history'].append({"name": custom_n, "text": trans_text, "id": saved_id})
                                            st.session_state['last_transcribed_file'] = custom_n # Update last processed
                                            # V206: Play Sound (Soft for individual files)
                                            play_sound('soft')
                                        
                                        # Cleanup handled by logic
                                        # if os.path.exists(txt_path): os.remove(txt_path) # DEPRECATED V174
                                        success = True
                                        time.sleep(2) # Micro-pause between files
                                        
                                    except ResourceExhausted:
                                        status_text.warning(f"⏳ **Alcalzamos el límite de IA (Quota).** Esperando 60 segundos para enfriar motores...")
                                        time.sleep(65) # Wait out the minute limit
                                        attempt += 1
                                    except ServiceUnavailable:
                                        status_text.warning(f"⚠️ Servidor ocupado. Reintentando en 10s...")
                                        time.sleep(10)
                                        attempt += 1
                                    except BaseException as e:
                                        error_msg = f"❌ Error fatal en {file.name}: {str(e)}"
                                        st.error(error_msg)
                                        log_debug(f"EXCEPTION: {error_msg}")
                                        import traceback
                                        st.code(traceback.format_exc())
                                        attempt = max_retries # Abort this file
                                    finally:
                                        pass

                                # Cleanup Temp
                                if os.path.exists(temp_path): 
                                    try: os.remove(temp_path)
                                    except: pass
                                
                                # V215: Explicit Memory Cleanup for 500MB+ files
                                gc.collect()
                            
                            # Update Global Progress
                            progress_bar.progress(min((start_idx + BATCH_SIZE) / total_files, 1.0))
                            
                            # Inter-Batch Cooldown (Be nice to API)
                            if start_idx + BATCH_SIZE < total_files:
                                status_text.info(f"☕ Tomando un respiro de 10s antes del siguiente lote...")
                                time.sleep(10)
                                
                        status_text.success("¡Misión Cumplida! Todos los archivos han sido procesados. 🏁")
                        # V350: BATCH COMPLETE NOTIFICATION
                        play_sound('loud') # Only ring loud when everything is done
                        
                        time.sleep(2)
                        try:
                            st.rerun()
                        except Exception:
                            pass # If rerun fails (e.g. RerunData error), just continue to avoid crashing content
                        
                except BaseException as e:
                    st.error(f"💥 Error Fatal en la aplicación (Nivel Sistema): {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    log_debug(f"FATAL APP CRASH: {traceback.format_exc()}")

    # History
    if st.session_state['transcript_history']:
        
        # Recents Header
        st.divider()
        st.markdown(f"### 📝 Resultados Recientes")
        
        # Buttons moved to top (next to banner) for better UX
        
        for i, item in enumerate(st.session_state['transcript_history']):
            with st.expander(f"📄 {item['name']}", expanded=True):
                 # Header with Copy integrated better
                 c_lbl, c_cp = st.columns([0.85, 0.15])
                 with c_lbl:
                      st.markdown(f"**Transcripción: {item['name']}**")
                 with c_cp:
                      # JS COPY COMPONENT (Fixed positioning)
                      import json
                      import streamlit.components.v1 as components
                      
                      # Clean text (User Request V298)
                      raw_txt = item['text']
                      clean_txt = clean_markdown(raw_txt)
                      
                      safe_txt = json.dumps(clean_txt)
                      
                      html_cp = f"""
                    <html>
                    <body style="margin:0; padding:0; background: transparent;">
                        <script>
                        function copyT() {{
                            const text = {safe_txt};
                            const b = document.getElementById('btn');
                            
                            function done() {{
                                b.innerText = '✅';
                                b.style.color = '#10b981';
                                setTimeout(() => {{ b.innerText = '📄'; b.style.color = '#888'; }}, 2000);
                            }}

                            // Plan A
                            if (navigator.clipboard && window.isSecureContext) {{
                                navigator.clipboard.writeText(text).then(done).catch(err => fallback(text));
                            }} else {{
                                fallback(text);
                            }}

                            function fallback(text) {{
                                const t = document.createElement("textarea");
                                t.value = text;
                                t.style.position = "fixed";
                                t.style.left = "-9999px";
                                document.body.appendChild(t);
                                t.focus();
                                t.select();
                                try {{
                                    if(document.execCommand('copy')) done();
                                }} catch (err) {{}}
                                document.body.removeChild(t);
                            }}
                        }}
                        </script>
                        <div style="display: flex; justify-content: flex-end; padding-top: 5px;">
                            <button id="btn" onclick="copyT()" style="
                                cursor: pointer; background: transparent; border: none; font-size: 18px; color: #888;
                            " title="Copiar al portapapeles">
                                📄
                            </button>
                        </div>
                    </body>
                    </html>
                    """
                      components.html(html_cp, height=35)
                 
                 # NATIVE SCROLL CONTAINER (Cleanest approach)
                 with st.container(height=400):
                       # CLEANUP: Remove any accidental markdown code blocks that prevent color rendering
                       processed_text = item['text']
                       if "```" in processed_text:
                            processed_text = processed_text.replace("```markdown", "").replace("```html", "").replace("```", "")
                       
                       # V341: Fix UI Gap - Strip leading whitespace
                       st.markdown(processed_text.strip(), unsafe_allow_html=True)


# --- TAB 2: Explorador Didáctico (Traductor de Conocimiento) ---
with tab_didactic:
    col_img, col_text = st.columns([1, 1.5], gap="large")
    
    with col_img:
        # Image Display
        import base64
        img_b64_notes = ""
        img_path_notes = "assets/notes_header.jpg" # Reusing assets or we can add new one
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
            '<h2 style="margin-top:0;">🧠 Explorador Didáctico</h2>'
            '<p style="color: #64748b; font-size: 1.1rem;">"Traduce" la clase difícil a lenguaje simple con analogías y ejemplos cotidianos.</p>'
            '</div>'
        )
        st.markdown(tab2_html, unsafe_allow_html=True)
        
        c_id = st.session_state.get('current_course_id')
        if not c_id:
             st.info("Selecciona Espacio de Trabajo.")
        else:
             from db_handler import get_files, get_file_content, upload_file_to_db, get_course_files, get_units, create_unit
             
             transcript_files = get_course_files(c_id, type_filter="transcript")
             
             # Check Global Memory
             gl_ctx, gl_count = get_global_context()
             if gl_count > 0:
                st.success(f"✅ **Memoria Global Activa:** {gl_count} archivos base detectados.")
            
                if not transcript_files:
                    st.info("No hay transcripciones disponibles. Sube videos en la Pestaña 1.")
                else:
                    options = [f['name'] for f in transcript_files]
                    file_map = {f['name']: f['id'] for f in transcript_files}
                    
                    c1_sel, c2_fold = st.columns([1, 1], gap="small")
                    
                    with c1_sel:
                         selected_file = st.selectbox("Selecciona la clase a traducir:", options, key="sel_didactic")
                    
                    with c2_fold:
                         # --- FOLDER SELECTOR (Reused Logic) ---
                         # Fetch all units
                         u_all = get_units(c_id, fetch_all=True)
                         if u_all:
                             id_to_u = {u['id']: u for u in u_all}
                             def get_p(u):
                                  parts = [u['name']]
                                  curr = u
                                  depth = 0
                                  while curr.get('parent_id') and depth < 5:
                                      pid = curr['parent_id']
                                      parent = id_to_u.get(pid)
                                      if parent:
                                          parts.insert(0, parent['name'])
                                          curr = parent
                                          depth += 1
                                      else: break
                                  return " / ".join(parts)
                             
                             map_u = {get_p(u): u['id'] for u in u_all}
                             keys_u = sorted(list(map_u.keys()))
                             
                             # Default to "Apuntes Didácticos" if exists
                             idx_def = 0
                             for i, k in enumerate(keys_u):
                                 if "Didácticos" in k or "Apuntes" in k:
                                     idx_def = i
                                     break
                                     
                             sel_fold_name = st.selectbox("Guardar en:", keys_u, index=idx_def, key="sel_fold_didactic")
                             target_unit_id = map_u[sel_fold_name]
                             target_unit_name = sel_fold_name # Display name path
                         else:
                             st.warning("Sin carpetas. Se creará una por defecto.")
                             target_unit_id = None
                    
                    
                    if selected_file and st.button("🔍 Traducir a Lenguaje Simple", key="btn_didactic", type="primary"):
                        from db_handler import get_file_content, upload_file_to_db, get_units, create_unit 
                        f_id = file_map[selected_file]
                        text = get_file_content(f_id)
                        
                        with st.spinner("Traduciendo conceptos complejos a lenguaje humano..."):
                            # CALL NEW AI FUNCTION
                            didactic_data = assistant.generate_didactic_explanation(text, global_context=gl_ctx)
                            
                            st.session_state['didactic_result'] = didactic_data
                            
                            # SAVE LOGIC
                            if not target_unit_id:
                                 # Fallback create
                                 target_folder = "Apuntes Didácticos"
                                 n_unit = create_unit(c_id, target_folder)
                                 n_unit_to_use = n_unit['id']
                                 t_folder_name = target_folder
                            else:
                                 n_unit_to_use = target_unit_id
                                 t_folder_name = target_unit_name
                            
                            if n_unit_to_use:
                                 # Create a Markdown representation for saving
                                 md_save = f"# 🧠 Explicación Didáctica: {selected_file}\n\n"
                                 
                                 modules = []
                                 if isinstance(didactic_data, list):
                                     if len(didactic_data) > 0 and isinstance(didactic_data[0], dict) and 'modules' in didactic_data[0]:
                                         modules = didactic_data[0]['modules']
                                     else:
                                         modules = didactic_data
                                 elif isinstance(didactic_data, dict):
                                     modules = didactic_data.get('modules', [])
                                 
                                 if not modules:
                                     md_save += f"_{didactic_data.get('introduction', '')}_\n\n"
                                     for b in didactic_data.get('blocks', []):
                                         md_save += f"### {b.get('concept_title', 'Concepto')}\n"
                                         md_save += f"{b.get('simplified_explanation', '')}\n\n"
                                     md_save += f"\n{didactic_data.get('conclusion', '')}"
                                 else:
                                     for m in modules:
                                         m_type = m.get('type', 'DEEP_DIVE')
                                         title = m.get('title', 'Módulo')
                                         c = m.get('content', {})
                                         
                                         md_save += f"## {title}\n"
                                         
                                         if m_type == 'STRATEGIC_BRIEF':
                                             md_save += f"**Tesis:** {c.get('thesis')}\n\n"
                                             md_save += f"**Impacto:** {c.get('impact')}\n\n"
                                             
                                         elif m_type == 'DEEP_DIVE':
                                             md_save += f"**Definición:** {c.get('definition')}\n\n"
                                             md_save += f"**Explicación:** {c.get('explanation')}\n\n"
                                             if c.get('example'):
                                                md_save += f"> **Ejemplo:** {c.get('example')}\n\n"
                                         
                                         elif m_type == 'REALITY_CHECK':
                                             md_save += f"❓ **{c.get('question')}**\n\n"
                                             md_save += f"✅ {c.get('insight')}\n\n"
                                             
                                         elif m_type == 'TOOLKIT':
                                             md_save += f"{c.get('intro')}\n"
                                             for s in c.get('steps', []):
                                                 md_save += f"- [ ] {s}\n"
                                             md_save += "\n"
                                             
                                         md_save += "---\n\n"
                                 
                                 fname = f"Didactico_{selected_file.replace('.txt', '')[:50]}.md"
                                 # Using upload_file_to_db (not upload_file_v2 which looked like a typo in previous code)
                                 upload_file_to_db(n_unit_to_use, fname, md_save, "note")
                                 st.success(f"Explicación guardada en '{t_folder_name}'")

                # --- RENDER RESULT ---
                res = st.session_state.get('didactic_result')
                if res:
                    st.divider()
                    
                    # DYNAMIC MODULE RENDERER
                    modules = []
                    if isinstance(res, list):
                        # Check if it's a list containing the root object -> [{'modules': ...}]
                        if len(res) > 0 and isinstance(res[0], dict) and 'modules' in res[0]:
                             modules = res[0]['modules']
                        else:
                             modules = res
                    elif isinstance(res, dict):
                        modules = res.get('modules', [])
                        if not modules and 'blocks' in res: 
                             # Fallback for old cache (v8)
                             st.warning("⚠️ Formato antiguo detectado. Por favor regenera la explicación.")
                    
                    for i, m in enumerate(modules):
                        # --- SMART ADAPTER FOR LEGACY/MALFORMED BLOCKS ---
                        # If the AI returns a flat object (Old Schema) instead of nested 'content'
                        if 'content' not in m and 'simplified_explanation' in m:
                             m_type = 'DEEP_DIVE'
                             title = m.get('concept_title', 'Concepto')
                             c = {
                                 'definition': m.get('academic_definition'),
                                 'explanation': m.get('simplified_explanation'),
                                 'example': m.get('analogy'),
                             }
                        else:
                             m_type = m.get('type', 'DEEP_DIVE').upper()
                             # SANITIZE TYPE: Remove emojis and spaces if AI gets creative
                             import re
                             m_type = re.sub(r'[^A-Z_]', '', m_type) 
                             
                             title = m.get('title', 'Módulo')
                             c = m.get('content', {})
                        
                        # Fallback for completely empty content
                        if not c and not m_type == 'STRATEGIC_BRIEF': 
                             # Try to salvage anything
                             c = {'explanation': str(m), 'definition': 'N/A'}

                        # 1. 🎯 STRATEGIC BRIEF (Hero Section)
                        
                        # 1. 🎯 STRATEGIC BRIEF (Hero Section)
                        if m_type == 'STRATEGIC_BRIEF':
                            with st.container():
                                st.markdown(f"## 🎯 {title}")
                                st.info(f"**TESIS:** {c.get('thesis')}", icon="💡")
                                st.markdown(f"**💎 Impacto:** {c.get('impact')}")
                            st.divider()

                        # 2. 🧠 DEEP DIVE (Technical Expander)
                        elif m_type == 'DEEP_DIVE':
                            with st.expander(f"🧠 {title}", expanded=True):
                                st.markdown(f"**📖 Definición:** {c.get('definition')}")
                                st.markdown(f"**⚙️ Funcionamiento:**\n{c.get('explanation')}")
                                if c.get('example'):
                                    st.markdown(f"**💼 Caso Real:**\n_{c.get('example')}_")

                        # 3. 🕵🏻 REALITY CHECK (Critical Analysis)
                        elif m_type == 'REALITY_CHECK':
                            with st.container(border=True):
                                c1, c2 = st.columns([0.1, 0.9])
                                with c1: st.markdown("## 🕵🏻")
                                with c2:
                                    st.markdown(f"### {title}")
                                    st.warning(f"**❓ {c.get('question')}**")
                                    st.markdown(f"**✅ Insight:** {c.get('insight')}")

                        # 4. 🛠️ TOOLKIT (Action Steps)
                        elif m_type == 'TOOLKIT':
                            with st.container():
                                st.markdown(f"### 🛠️ {title}")
                                st.caption(c.get('intro'))
                                check_steps = c.get('steps', [])
                                for j, step in enumerate(check_steps):
                                    c1, c2 = st.columns([0.85, 0.15])
                                    with c1:
                                        st.checkbox(step, key=f"step_{i}_{j}")
                                    with c2:
                                        if st.button("❓", key=f"help_{i}_{j}", help="Dime cómo hago esto"):
                                            with st.spinner("Generando guía..."):
                                                guide = assistant.generate_micro_guide(step)
                                                st.session_state[f"guide_{i}_{j}"] = guide
                                    
                                    # Show guide if exists
                                    if f"guide_{i}_{j}" in st.session_state:
                                        with st.expander(f"💡 Guía: {step[:30]}...", expanded=True):
                                            st.markdown(st.session_state[f"guide_{i}_{j}"])
                                
                                # Export Action Plan
                                csv_content = "To-Do;Estado\n" + "\n".join([f"{s};Pendiente" for s in check_steps])
                                st.download_button(
                                    label="📥 Descargar Plan de Acción",
                                    data=csv_content,
                                    file_name=f"Plan_Accion_{title.replace(' ', '_')}.csv",
                                    mime="text/csv"
                                )
                            st.divider()
                        
                        else:
                             # Debug Fallback
                             with st.expander(f"⚠️ Módulo Desconocido: {m_type}"):
                                 st.write(m)


# --- TAB 4: Quiz ---
with tab_quiz:
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
        # Check Global Memory (Optimized: Count Only)
        gl_count = get_global_file_count_only() # Fast
        # gl_ctx content is now fetched JUST-IN-TIME inside the solver trigger
        
        if gl_count > 0:
            st.success(f"✅ **Memoria Global Activa:** Usando {gl_count} archivos para mayor precisión.")
        
        # RESET BUTTON
        col_up, col_reset = st.columns([0.9, 0.1])
        with col_reset:
             # Use the same 'copy-btn' style or just a clean emoji button
             if st.button("🗑️", key="reset_quiz", help="Borrar todo para empezar de cero"):
                 st.session_state['quiz_results'] = []
                 st.session_state['pasted_images'] = []
                 q_k = st.session_state['quiz_key']
                 
                 # Explicit Nuke of Component Keys
                 if f"q_txt_{q_k}" in st.session_state: del st.session_state[f"q_txt_{q_k}"]
                 if f"up4_{q_k}" in st.session_state: del st.session_state[f"up4_{q_k}"]
                 
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
                    # --- CONFIGURACIÓN DE CONTEXTO (NUEVO V162) ---
                    st.markdown("##### 🧠 Fuente de Conocimiento")
                    st.caption("Selecciona qué información debe estudiar la IA para responderte.")
                    
                    if 'current_course_id' in st.session_state and st.session_state['current_course_id']:
                         from db_handler import get_units
                         # FIX V166: Fetch ALL units (recursive) to allow subfolder selection
                         units_ctx = get_units(st.session_state['current_course_id'], fetch_all=True)
                         
                         # --- HIERARCHY BUILDER ---
                         # 1. Map ID -> Unit
                         u_map = {u['id']: u for u in units_ctx}
                         # 2. Map Parent -> Children
                         p_map = {}
                         for u in units_ctx:
                             pid = u.get('parent_id')
                             if pid not in p_map: p_map[pid] = []
                             p_map[pid].append(u)
                         
                         # 3. Flatten Recursive List with Indentation
                         flat_options = []
                         
                         def add_to_list(parent_id, depth=0):
                             children = p_map.get(parent_id, [])
                             # Sort by name
                             children.sort(key=lambda x: x['name'])
                             
                             for child in children:
                                 # Indent based on depth
                                 prefix = "└─ " * depth if depth > 0 else ""
                                 folder_icon = "📂" if depth > 0 else "📁"
                                 label = f"{prefix}{folder_icon} {child['name']}"
                                 
                                 flat_options.append({"label": label, "id": child['id']})
                                 
                                 # Recurse
                                 add_to_list(child['id'], depth + 1)
                         
                         # Start with Roots (parent_id is None)
                         add_to_list(None)
                         
                         # --- UI ---
                         ctx_options = ["📚 Toda la Biblioteca (Recomendado)"]
                         unit_map_ctx = {}
                         
                         for item in flat_options:
                             ctx_options.append(item['label'])
                             unit_map_ctx[item['label']] = item['id']
                             
                         sel_ctx = st.selectbox("Carpeta de Referencia:", ctx_options, key=f"sel_ctx_{q_key}", help="Si tu quiz es de un tema específico, selecciona su carpeta para mayor precisión.")
                         
                         # Store selection in session state via key, but we need ID for logic
                         st.session_state[f'quiz_ctx_unit_id_{q_key}'] = unit_map_ctx.get(sel_ctx) # None if "Toda"
                    
                    st.divider()

                    # --- MANUAL CONFIG TABLE ---
                    st.markdown("##### ⚙️ Configuración de IA (Opcional)")
                    st.caption("Si la IA se confunde, ayúdale seleccionando el tipo exacto de cada imagen.")
                    
                    # 1. Build Data List
                    current_files = []
                    # Pasted
                    for i, p_img in enumerate(st.session_state['pasted_images']):
                         # Assuming we don't have filenames for pasted, generate IDs
                         current_files.append({"Archivo": f"Imagen Pegada {i+1}", "Tipo": "🤖 Auto (Detectar)", "id": f"paste_{i}"})
                    
                    # Uploaded
                    if files_val:
                        for f in files_val:
                             # V147 Fix: Handle both UploadedFile object and dict (persisted state)
                             fname = getattr(f, 'name', None) or f.get('name') if isinstance(f, dict) else "Archivo sin nombre"
                             current_files.append({"Archivo": fname, "Tipo": "🤖 Auto (Detectar)", "id": fname})
                    
                    if current_files:
                        import pandas as pd
                        df = pd.DataFrame(current_files)
                        
                        # Config Options
                        type_options = ["🤖 Auto (Detectar)", "☑️ Selección Múltiple", "✅❌ Cierto/Falso", "✍🏻 Respuesta Abierta"]
                        
                        edited_df = st.data_editor(
                            df,
                            column_config={
                                "Archivo": st.column_config.TextColumn("Archivo", disabled=True),
                                "Tipo": st.column_config.SelectboxColumn(
                                    "Tipo de Pregunta",
                                    help="Selecciona el formato para mejorar la precisión",
                                    width="medium",
                                    options=type_options,
                                    required=True
                                ),
                                "id": None # Hide ID
                            },
                            hide_index=True,
                            use_container_width=True,
                            key=f"editor_{q_key}" 
                        )
                        
                        # Store Config Mapping (ID -> Type)
                        # We use ID because filenames might be dupe or generic
                        config_map = {row['id']: row['Tipo'] for row in edited_df.to_dict('records')}
                        st.session_state['quiz_file_config'] = config_map
                        
                    
                    st.write("") # Spacer
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
                config_map = st.session_state.get('quiz_file_config', {})
                
                # HYDRATE GLOBAL CONTEXT ALWAYS (RAG V159 + V162 Focus Mode)
                # This ensures we always have the library context available for the AI
                gl_ctx = ""
                try:
                     # Check if specific unit is selected
                     target_unit_id = st.session_state.get(f'quiz_ctx_unit_id_{q_key}')
                     
                     if target_unit_id:
                         # 📁 Focus Mode: Only get text from this unit
                         from db_handler import get_unit_context
                         gl_ctx = get_unit_context(target_unit_id)
                         status.info(f"🧠 Usando CONTEXTO ENFOCADO (Carpeta Seleccionada)")
                     else:
                         # 📚 Global Mode: All text
                         gl_ctx, _ = get_global_context()
                except: pass # Safety fallback
                
                # Collect ALL Images
                all_pil_images = []
                
                # Deduplication logic using dictionary keys (name/id)
                image_map = {} 

                # From Paste
                for i, img in enumerate(st.session_state['pasted_images']):
                     # Use a unique key
                     k = f"paste_{i}"
                     image_map[k] = {"img": img, "id": k, "name": f"Imagen Pegada {i+1}"}

                # From Upload
                if img_files:
                    for f in img_files:
                        try:
                            # FIX V167: Robust handling for dict/object
                            fname = f.get('name') if isinstance(f, dict) else f.name
                            if not fname: fname = "unknown_file"
                            
                            k = fname
                            if k not in image_map:
                                # Start from beginning if possible
                                if not isinstance(f, dict):
                                    f.seek(0)
                                    pil_i = Image.open(f)
                                else:
                                    # If it's a dict, we might not have the file object to open?!
                                    # Actually, streamlit file_uploader state persistence usually keeps objects, 
                                    # BUT if we messed up state it might be a clean dict.
                                    # Assuming 'f' is capable of being opened if it's not a dict.
                                    # If it IS a dict, it usually means we stored metadata but lost the file?
                                    # Wait, st.file_uploader returns UploadedFile. 
                                    # If we manually stored it as dict in session state, we can't open it.
                                    # But let's assume valid object or fail gracefully.
                                    continue 
                                    
                                if pil_i.mode == 'RGBA': pil_i = pil_i.convert('RGB')
                                image_map[k] = {"img": pil_i, "id": k, "name": fname}
                        except Exception as e: 
                            # Safe print
                            safe_name = getattr(f, 'name', 'Unknown')
                            print(f"Error loading {safe_name}: {e}")
                
                # Convert back to list
                image_entries = list(image_map.values())
                
                items_to_process = []
                
                if use_ctx_mode:
                    # LINKED MODE (Improved): Iterate but pass context to EACH
                    # 1. Text Context Handling
                    
                    # HYDRATE GLOBAL CONTEXT HERE (JUST-IN-TIME)
                    if not gl_ctx:
                            gl_ctx, _ = get_global_context()
                    
                    # Process Images Individually (with text as context)
                    for i, entry in enumerate(image_entries):
                            # Get Manual Type
                            manual_type = config_map.get(entry['id'], "🤖 Auto (Detectar)")
                            
                            items_to_process.append({
                                "type": "linked_single", 
                                "text": input_text_quiz, 
                                "image": entry["img"], 
                                "name": entry["name"],
                                "force_type": manual_type 
                            })
                        
                    # If there are NO images but there IS text, just process text
                    if not image_entries and has_text:
                            items_to_process.append({"type": "text", "obj": input_text_quiz, "name": "Consulta de Texto", "force_type": "Auto"})

                else:
                    # SEPARATE MODE (Legacy)
                    if has_text:
                        items_to_process.append({"type": "text", "obj": input_text_quiz, "name": "Pregunta de Texto", "force_type": "Auto"})
                    
                    # Add Images separately
                    for i, entry in enumerate(image_entries):
                            manual_type = config_map.get(entry['id'], "🤖 Auto (Detectar)")
                            items_to_process.append({"type": "image_obj", "obj": entry["img"], "name": entry["name"], "force_type": manual_type})

                for i, item in enumerate(items_to_process):
                    # Calculate percentages
                    current_percent = int((i / len(items_to_process)) * 100)
                    status.markdown(f"**Analizando item {i+1} de {len(items_to_process)}... ({current_percent}%)**")
                    progress_bar.progress(i / len(items_to_process))
                
                    try:
                        full_answer = ""
                        disp_img = None
                        
                        # Extract Force Type (Clean string)
                        raw_type = item.get("force_type", "Auto")
                        # Clean logic: "☑️ Selección Múltiple" -> "Selección Múltiple"
                        ftype = "Auto"
                        if "Selección Múltiple" in raw_type: ftype = "Selección Múltiple"
                        elif "Cierto/Falso" in raw_type: ftype = "Cierto/Falso"
                        elif "Respuesta Abierta" in raw_type: ftype = "Respuesta Abierta"
                    
                        if item["type"] == "text":
                                # Text Only
                                full_answer = assistant.solve_quiz(question_text=item["obj"], global_context=gl_ctx, force_type=ftype)
                                
                        elif item["type"] == "linked_single":
                                # Linked Single Mode
                                full_answer = assistant.solve_quiz(images=[item["image"]], question_text=item["text"], global_context=gl_ctx, force_type=ftype)
                                disp_img = item["image"]
                             
                        elif item["type"] == "linked":
                             # (Deprecated but safely kept for fallback)
                             # Pass list of images
                             full_answer = assistant.solve_quiz(images=item["images"], question_text=item["text"], global_context=gl_ctx, force_type=ftype)
                             # Display first image as thumbnail?
                             disp_img = item["images"][0] if item["images"] else None
                             
                        elif item["type"] == "image_obj":
                            # Image Only
                            disp_img = item["obj"]
                            full_answer = assistant.solve_quiz(images=[disp_img], global_context=gl_ctx, force_type=ftype)

                        # Skip Short Answer Parsing (User Preference: Full Detail)
                        short_answer = "Ver abajo"
                    
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
        res_quiz = st.session_state.get('quiz_results')
        if res_quiz:
            st.divider()
            
            # HEADER + COPY ICON
            c_head, c_copy = st.columns([0.9, 0.1])
            with c_head:
                st.markdown("### 📋 Resultados de Quiz")
            with c_copy:
                # Compile text for copying inside the button action
                full_report_copy = "--- HOJA DE RESPUESTAS ---\n\n"
                for i, res in enumerate(res_quiz):
                     full_report_copy += f"FOTO {i+1}: {res['short']}\n"
                full_report_copy += "\n--- DETALLES ---\n"
                for i, res in enumerate(res_quiz):
                     full_report_copy += f"\n[FOTO {i+1}]\n{res['full']}\n"
                     
                if st.button("📄", key="cp_quiz", help="Copiar Resultados Limpios"):
                    clean_txt = clean_markdown(full_report_copy)
                    if copy_to_clipboard(clean_txt):
                        st.toast("¡Copiado!", icon='📋')
            
            # --- RESULTS DISPLAY ---
            
            # V143: SMART SORTING & PREVIEW
            # 1. Try to detect "Question X" or "Pregunta X" to restore order
            import re
            def extract_q_num(text):
                # V148 Fix: Strict Tag Priority
                # 1. Look for [[NUM:X]]
                tag_match = re.search(r'\[\[NUM:(\d+)\]\]', text)
                if tag_match:
                     return int(tag_match.group(1))
                     
                # 2. Fallback: Headers
                match = re.search(r'(?:^|\n|#|\*)\s*(?:Question|Pregunta|P)\s*(\d+)', text[:300], re.IGNORECASE)
                if match:
                    return int(match.group(1))
                return 9999 # Push to end
            
            # Sort the list in-place
            try:
                # Only sort if we detect numbers in at least one
                if any(extract_q_num(r['full']) != 9999 for r in res_quiz):
                    res_quiz.sort(key=lambda x: extract_q_num(x['full']))
            except Exception as e:
                print(f"Sort Error: {e}")

            for i, res in enumerate(res_quiz):
                # V148: STRICT TAG PARSING (Robust Protocol)
                full_txt = res['full']
                
                # 1. Extract Number tag [[NUM:X]]
                # Heuristic: If we find [[NUM:5]], we trust it explicitly for sorting/display
                # This should be done inside the sort loop actually? 
                # Ideally yes, but let's handle display logic here first.
                
                # 2. Extract Question tag [[PREGUNTA:Text]]
                q_text_match = re.search(r'\[\[PREGUNTA:(.*?)\]\]', full_txt, re.IGNORECASE)
                
                if q_text_match:
                    # New Format: We have exact text!
                    snippet = q_text_match.group(1).strip()[:90] + "..."
                else:
                    # Fallback for old results:
                    # SAFE MODE: Do NOT show random text to avoid spoilers.
                    snippet = "Ver Pregunta y Análisis"

                # 3. Detect Real Number
                num_match = re.search(r'\[\[NUM:(\d+)\]\]', full_txt)
                if num_match:
                    real_num = int(num_match.group(1))
                else:
                    # Legacy fallback
                    real_num = extract_q_num(full_txt)
                
                display_num = str(real_num) if real_num != 9999 and real_num != 0 else str(i+1)
                
                # 4. Clean visible text (Hide tags)
                # We hide the metadata tags from the UI body so it looks clean
                # FIX V160: Use DOTALL to match newlines inside tags
                clean_body = re.sub(r'\[\[.*?\]\]', '', full_txt, flags=re.DOTALL).strip()
                
                # USE EXPANDER (User wants to see structure)
                with st.expander(f"🔹 **P{display_num}:** {snippet}", expanded=True):
                    
                    if 'img_obj' in res and res['img_obj']:
                        c_img, c_ans = st.columns([0.35, 0.65], gap="medium")
                        with c_img:
                             try:
                                 st.image(res['img_obj'], use_container_width=True, caption=res['name'])
                             except:
                                 st.caption("Imagen no disponible")
                        with c_ans:
                             st.markdown(clean_body)
                    else:
                         st.markdown(clean_body)

            # --- DEBATE CHAT ---
            st.divider()
            
            # Header + Action
            c_chat_title, c_chat_act = st.columns([0.6, 0.4])
            with c_chat_title:
                st.markdown("### 💬 Debatir Resultados")
                st.caption("¿Dudas? Habla con el Profesor.")
            
            with c_chat_act:
                 # BUTTON MOVED HERE
                 pass 
        else:
            st.info("👆 **Sube una imagen o pregunta para ver la Zona de Análisis.**")
            # Cleaning debug text

        # MOVED OUTSIDE THE IF to be visible if we want? No, logic requires results.
        # But we keep indentation logic.
        
        if res_quiz:
            if st.button("🔄 ACTUALIZAR RESULTADOS (Corrección de IA)", use_container_width=True, type="primary"):
                with st.spinner("Consolidando cambios..."):
                    try:
                        new_res = assistant.refine_quiz_results(st.session_state['quiz_results'], st.session_state['quiz_chat'])
                        st.session_state['quiz_results'] = new_res
                        st.success("¡Hecho!")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            # Spacer
            st.write("")
            
            if 'quiz_chat' not in st.session_state:
                st.session_state['quiz_chat'] = []
            
            # Display History
            for msg in st.session_state['quiz_chat']:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Input
            # Input
            # (Native Streamlit Input - Reverted custom JS)

            if prompt := st.chat_input("Escribe tu duda o corrección...", key="quiz_chat_input"):
                # Add User Msg
                st.session_state['quiz_chat'].append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Prepare Context (Last Quiz Results)
                ctx_quiz = "SIN DATOS DE QUIZ RECIENTE"
                if res_quiz:
                    ctx_quiz = "--- RESULTADOS DEL QUIZ --- \n"
                    for res in res_quiz:
                        # Truncate text to avoid token explosion
                        short_full = (res['full'][:500] + '..') if len(res['full']) > 500 else res['full']
                        ctx_quiz += f"[Item: {res['name']}]\nAI Dice: {short_full}\n\n"
                
                # Call AI
                with st.chat_message("assistant"):
                    with st.spinner("El profesor está re-analizando las imágenes y tu argumento..."):
                        # Gather Images for Context
                        images_ctx = []
                        if res_quiz:
                            for r in res_quiz:
                                if r.get('img_obj'): images_ctx.append(r['img_obj'])
                        
                        reply = assistant.debate_quiz(
                            history=st.session_state['quiz_chat'][:-1], 
                            latest_input=prompt, 
                            quiz_context=ctx_quiz,
                            images=images_ctx
                        )
                        
                        # Check for Auto-Learning Tag
                        import re
                        match = re.search(r"\|\|APRENDIZAJE: (.*?)\|\|", reply)
                        if match:
                            rule = match.group(1).strip()
                            st.session_state['pending_learning_rule'] = rule
                            reply = reply.replace(match.group(0), "")
                        
                        st.markdown(reply)
                        st.session_state['quiz_chat'].append({"role": "assistant", "content": reply})
                        st.rerun()

            # --- TEACHING / MEMORY UI (SIMPLIFIED) ---
            pending = st.session_state.get('pending_learning_rule')
            # Show ONLY if AI suggests a rule
            if pending and st.session_state.get('quiz_chat') and st.session_state['quiz_chat'][-1]['role'] == 'assistant':
                with st.container(border=True):
                    st.info(f'🤖 **La IA propone aprender:**\n>{pending}')
                    c1, c2 = st.columns([0.3, 0.7])
                    with c1:
                        if st.button('✅ Confirmar', key='btn_conf_auto', type='primary'):
                            cid = st.session_state.get('current_course_id')
                            if database.save_user_memory(cid, f'- {pending}', None):
                                st.toast('¡Aprendido! 🧠')
                                st.session_state['pending_learning_rule'] = None
                                time.sleep(1)
                                st.rerun()
                    with c2:
                        if st.button('❌ Descartar', key='btn_deny_auto'):
                            st.session_state['pending_learning_rule'] = None
                            st.rerun()
# --- TAB 5: Ayudante de Tareas (DISABLED V334 REVERT) ---
if False: # # with tab_tasks:
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
        from db_handler import get_units, get_unit_context
        
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
        res_hw = st.session_state.get('homework_result')
        if res_hw:
            res = res_hw
            
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
                from db_handler import create_chat_session, save_chat_message
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

# with tab_tutor:
if False:
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
    from db_handler import get_chat_messages, save_chat_message
    
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
        # Optimization: Only fetch if we switched session or history not loaded
        if 'tutor_chat_history' not in st.session_state or st.session_state.get('loaded_sess_id') != current_sess['id']:
            db_msgs = get_chat_messages(current_sess['id'])
            st.session_state['tutor_chat_history'] = db_msgs
            st.session_state['loaded_sess_id'] = current_sess['id']
        



        # --- UPLOAD STATUS PLACEHOLDER (Centralized) ---
        upload_status_container = st.empty()

        col_chat, col_info = st.columns([3, 1], gap="large")
        
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
            with st.sidebar:
                st.header("Estudan2 🧠")
                st.caption("Tu asistente de estudio con IA")
                st.caption("v3.3.4 (Visible Folders 👀)")
                
                # --- SIDEBAR AUTH DISPLAY ---
                if st.session_state.get('authenticated'):
                    st.divider()
                    user_name = st.session_state.get('user_nickname', 'Estudiante')
                    st.write(f"Hola, **{user_name}** 👋")
            
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
                # UX FIX: Use central placeholder so it's visible in main chat area
                st.toast("Procesando archivos...", icon="⏳")
                
                with upload_status_container.status("🔄 Procesando archivos...", expanded=True) as status:
                    for up_file in new_uploads:
                        if not any(f['name'] == up_file.name for f in st.session_state['active_context_files']):
                            st.write(f"📖 Leyendo: **{up_file.name}**...")
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
                            st.write(f"✅ ¡{up_file.name} listo!")
                    
                    status.update(label="✅ Carga Completa", state="complete", expanded=True)
                    st.toast("✅ ¡Archivos listos para usar!", icon="🚀")
                    
                    # Small delay to ensure they see it before any potential rerun
                    import time
                    time.sleep(1.5)
        
        # --- HIDDEN PASTE RECEIVER ---
        if 'paste_key' not in st.session_state: st.session_state['paste_key'] = 0
        
        # MOVE TO SIDEBAR to prevent layout issues in main chat
        with st.sidebar:
             # st.markdown('<div class="paste-bin-hidden-wrapper">', unsafe_allow_html=True)
             # paste_bin = st.file_uploader("KILL_ME_NOW", type=['png','jpg','jpeg','pdf'], key=f"paste_bin_{st.session_state['paste_key']}", label_visibility='collapsed')
             # st.markdown('</div>', unsafe_allow_html=True)
             paste_bin = None # Disabled to prevent rendering
        
        if paste_bin:
             # Check for duplicates (Original Name OR Pasted Name)
             # file_data['name'] is what we stored. paste_bin.name is the new file.
             # We stored it as f"Pasted_{paste_bin.name}"
             is_duplicate = any(f['name'] == paste_bin.name or f['name'] == f"Pasted_{paste_bin.name}" for f in st.session_state['active_context_files'])
             
             if not is_duplicate:
                 st.session_state['active_context_files'].append({
                     "name": f"Pasted_{paste_bin.name}",
                     "content": f"[Archivo Pegado: {paste_bin.name}]" 
                 })
                 st.toast("📸 Archivo pegado!")
                 
                 # RESET UPLOADER
                 st.session_state['paste_key'] += 1
                 st.rerun()
             else:
                 # It is a duplicate in the INPUT, but maybe already handled.
                 # If we don't reset, it stays there. 
                 # We should probably reset anyway if it's stale?
                 # But if user pasted same file intentionally?
                 # Let's just reset to be clean.
                 pass

        components.html("""
        <script>
        const observer = new MutationObserver(() => {
            const popovers = window.parent.document.querySelectorAll('div[data-testid="stPopover"]');
            const chatInput = window.parent.document.querySelector('[data-testid="stChatInput"]');
            
            // 1. FOCUS & LAYOUT FIX
            if (chatInput) {
                 // Ensure the whole bar is clickable
                 chatInput.style.cursor = 'text';
                 chatInput.onclick = (e) => {
                     const ta = chatInput.querySelector('textarea');
                     if (ta && e.target !== ta && !e.target.closest('button')) {
                         ta.focus();
                     }
                 };

                 // Inject + Button if needed
                 if (popovers.length > 0) {
                     const targetPopover = popovers[popovers.length - 1]; 
                     const textArea = chatInput.querySelector('textarea');
                     if (textArea && textArea.parentElement) {
                         const capsule = textArea.parentElement;
                     // 1.5. VERTICAL LAYOUT REDESIGN
                     // Request: Text on TOP, Button on BOTTOM.
                     
                     // A. Force Container to Column
                     capsule.style.setProperty('flex-direction', 'column', 'important');
                     capsule.style.setProperty('align-items', 'flex-start', 'important'); // Align left
                     capsule.style.setProperty('gap', '5px', 'important');
                     
                     // B. Ensure Button is at the BOTTOM (Append moves it to end)
                     if (!capsule.contains(targetPopover)) {
                         targetPopover.style.position = 'relative';
                         targetPopover.style.margin = '0px'; 
                         targetPopover.style.zIndex = '10';
                         targetPopover.style.width = '1000%'; // Full width for alignment
                         
                         // Insert at END (Bottom)
                         capsule.appendChild(targetPopover);
                     } else {
                         // Already there, just ensure order if needed (re-append moves to end)
                         // But be careful not to trigger infinite loop if observer reacts to this.
                         // Check if it's already the last child
                         if (capsule.lastElementChild !== targetPopover) {
                             capsule.appendChild(targetPopover);
                         }
                     }
                     
                     // C. Style the Textarea (Top Element)
                     textArea.style.setProperty('width', '100%', 'important');
                     textArea.style.setProperty('text-align', 'left', 'important');
                     textArea.style.setProperty('padding', '10px 0px 0px 0px', 'important'); // Visual tweak
                     
                     // D. ENFORCER (Relaxed to prevent lag)
                     const enforceLayout = () => {
                          if (capsule) {
                              capsule.style.setProperty('flex-direction', 'column', 'important');
                              capsule.style.setProperty('gap', '5px', 'important');
                          }
                          if (textArea) {
                              textArea.style.setProperty('width', '100%', 'important');
                              textArea.style.border = 'none';
                          }
                     };
                     
                     // Run loop (Less aggressive: 1s)
                if (textArea.dataset.layout_v2 === undefined) {
                      setInterval(enforceLayout, 1000);
                      textArea.dataset.layout_v2 = 'active';
                 }
                 
                  const pasteInput = Array.from(window.parent.document.querySelectorAll('input[type="file"]'))
                      .find(i => i.getAttribute('aria-label') === "Paste_Receiver_Hidden_Bin" || i.parentElement.innerText.includes("Paste_Receiver_Hidden_Bin"));
                 
                 if (pasteInput) {
                     // HELPER: Send File to Input
                     const sendFiles = (files) => {
                         const dataTransfer = new DataTransfer();
                         for (let i = 0; i < files.length; i++) {
                              dataTransfer.items.add(files[i]);
                         }
                         pasteInput.files = dataTransfer.files;
                         pasteInput.dispatchEvent(new Event('change', { bubbles: true }));
                     };

                     // A. PASTE Handler
                     if (!window.parent.document.hasPasteHandler) {
                         window.parent.document.addEventListener('paste', (event) => {
                             const items = (event.clipboardData || event.originalEvent.clipboardData).items;
                             const files = [];
                             for (let i=0; i < items.length; i++) {
                                 if (items[i].kind === 'file') files.push(items[i].getAsFile());
                             }
                             if (files.length > 0) sendFiles(files);
                         });
                         window.parent.document.hasPasteHandler = true;
                     }

                    // B. DRAG & DROP Handler (Global)
                    if (!window.parent.document.hasDropHandler) {
                        // Drag Over (Allow drop)
                        window.parent.document.addEventListener('dragover', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            // Optional: Highlight UI
                        });
                        
                        // Drop
                        window.parent.document.addEventListener('drop', (e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                                sendFiles(e.dataTransfer.files);
                            }
                        });
                        window.parent.document.hasDropHandler = true;
                    }
                }
            }
            
        
        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true, attributes: true });
        </script>
        """, height=0)

        with col_chat:
            # Display Chat History (WhatsApp Style)
            import markdown
            chat_html = '<div style="display: flex; flex-direction: column; gap: 15px; padding-bottom: 20px;">'
            
            for msg in st.session_state['tutor_chat_history']:
                is_user = msg['role'] == 'user'
                
                # Styles
                row_style = "display: flex; width: 100%; align-items: flex-end; margin-bottom: 2px;"
                if is_user:
                     row_style += " justify-content: flex-end;"
                else:
                     row_style += " justify-content: flex-start;"
                
                bubble_style = "padding: 10px 14px; border-radius: 12px; max-width: 85%; word-wrap: break-word; font-size: 16px; line-height: 1.5; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-family: inherit;"
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
            
            # Files display removed per user request (handled in sidebar/backend now)
            
            # SCROLL BUTTON (INJECTED INTO PARENT)
            # CLEANUP: NO INJECTION HERE. Global manager handles this.

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
                             from db_handler import get_file_content
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
                            
                            # V142: DEBATE AUTO-CORRECTOR SNIFFER
                            # Checks if the AI admitted a mistake and corrected a quiz answer.
                            if "CORRECCIÓN ACEPTADA" in full_resp or "tienes razón" in full_resp.lower():
                                try:
                                    # Very basic heuristic: Look for "Pregunta X" and "Respuesta: Y"
                                    # Ideally, the AI should output structured data, but we parse text for now.
                                    import re
                                    
                                    # 1. Find Question Index (e.g. "Pregunta 2")
                                    q_match = re.search(r'Pregunta\s+(\d+)', full_resp, re.IGNORECASE)
                                    
                                    # 2. Find Correct Answer (e.g. "respuesta correcta es 'False'")
                                    a_match = re.search(r'correcta\s+es\s+[\'"]?([^\'"\.\n]+)', full_resp, re.IGNORECASE)
                                    
                                    if q_match and a_match and 'quiz_results' in st.session_state:
                                        idx = int(q_match.group(1)) - 1 # 0-indexed
                                        new_ans = a_match.group(1).strip()
                                        
                                        if 0 <= idx < len(st.session_state['quiz_results']):
                                            # UPDATE THE QUIZ STATE
                                            st.session_state['quiz_results'][idx]['correct_answer'] = new_ans
                                            st.session_state['quiz_results'][idx]['user_correct'] = True # Assume user was right since they debated
                                            st.session_state['quiz_results'][idx]['explanation'] += f"\n\n[CORREGIDO EN DEBATE]: {full_resp[:100]}..."
                                            st.toast(f"✅ Quiz corregido: P{idx+1} -> {new_ans}")
                                except Exception as e:
                                    print(f"Debate Auto-Correct Error: {e}")
                 
                 st.session_state['trigger_ai_response'] = False # Safety

        # --- INPUT MOVED OUTSIDE OF COLUMNS (STICKY FOOTER FIX) ---
        if prompt := st.chat_input(f"Pregunta sobre {current_sess['name']}..."):
            
             # 2. Add User Message
            save_chat_message(current_sess['id'], "user", prompt)
            
            # Update UI State
            st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt})
            
            # 3. Trigger Response
            st.session_state['trigger_ai_response'] = True
            st.rerun()

# --- DEFINITIVE SCROLL ANCHOR ---
st.markdown("<div id='end_marker' style='height: 1px; width: 1px; visibility: hidden;'></div>", unsafe_allow_html=True)

# Force Reload Triggered



