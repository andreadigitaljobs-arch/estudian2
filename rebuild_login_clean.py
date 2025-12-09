
import os
import base64

app_path = 'app.py'

# 1. NEW CLEAN LOGIN LOGIC (No patching, full block replacement)
clean_login_code = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    import base64
    
    # --- HELPER: LOGO TO BASE64 ---
    def get_logo_b64():
        path = "assets/logo_main.png"
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    logo_b64 = get_logo_b64()
    
    # --- CUSTOM CSS FOR LOGIN PAGE (REBUILT) ---
    st.markdown('''
        <style>
        /* 1. RESET BACKGROUND */
        .stApp {
            background-color: white !important;
        }
        
        /* 2. MAIN CONTAINER - Vertically Centered & Compact */
        .main .block-container {
            max_width: 1000px;
            padding-top: 3rem !important; /* Fixed top buffer */
            padding-bottom: 2rem !important;
            margin: 0 auto;
            /* Flex center vertical */
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 85vh; /* Occupy most of screen height */
        }
        
        /* 3. REMOVE DEFAULT GAPS */
        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        
        /* 4. TITLE & LOGO STYLING (Handled via HTML, but global text reset) */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif !important;
            color: #111827 !important;
        }
        
        /* 5. INPUT FIELDS - Clean Standard */
        div[data-testid="stTextInput"] {
            margin-bottom: 5px !important; /* Minimal gap between inputs */
        }
        .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 6px !important;
            height: 42px !important;
            font-size: 0.95rem !important;
            padding: 0 12px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3500D3 !important;
            box-shadow: 0 0 0 2px rgba(53, 0, 211, 0.1) !important;
        }
        
        /* 6. BUTTONS - Brand Purple */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #3500D3 !important;
            color: white !important;
            border: none;
            border-radius: 6px !important;
            height: 42px !important;
            margin-top: 15px !important;
            font-weight: 600 !important;
            width: 100% !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #2900A5 !important;
            transform: translateY(-1px);
        }
        
        /* Secondary Button (Link Style) */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            color: #3500D3 !important;
            border: none !important;
            padding: 0 !important;
            height: auto !important;
            font-weight: 700 !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:focus {
            box-shadow: none !important;
        }

        /* 7. HIDE DEFAULT UI */
        #MainMenu, header, footer { visibility: hidden !important; }
        
        /* 8. Text Utilities */
        .login-title {
            font-size: 1.8rem;
            font-weight: 700;
            color: #111827;
            margin: 5px 0 5px 0; /* Tight margins */
            letter-spacing: -0.5px;
        }
        .login-subtitle {
            font-size: 0.95rem;
            color: #6B7280;
            margin-bottom: 25px;
        }
        .forgot-pass {
            text-align: center;
            display: block;
            margin-top: 15px;
            color: #3500D3;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .footer-text {
            color: #4B5563;
            font-size: 0.9rem;
            text-align: right;
            padding-right: 5px;
        }
        </style>
    ''', unsafe_allow_html=True)

    # LAYOUT GRID
    # Left: Form (0.45) | Right: Image (0.55)
    c_form, c_spacer, c_img = st.columns([1, 0.1, 1.2]) 

    with c_form:
        # --- HEADER BLOCK (Pure HTML for pixel-perfect spacing) ---
        img_tag = f'<img src="data:image/png;base64,{logo_b64}" width="240">' if logo_b64 else '<h2>e-education</h2>'
        
        st.markdown(f'''
            <div style="text-align: left; margin-bottom: 10px;">
                {img_tag}
                <div class="login-title">Log in to your account</div>
                <div class="login-subtitle">Welcome back! Please enter your details.</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # --- INPUTS ---
        email = st.text_input("Email", key="login_email", placeholder="Enter your email", label_visibility="collapsed")
        
        # Using a minimal spacer div instead of st.write("") to avoid Streamlit's huge margins
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••", label_visibility="collapsed")
        
        # --- ACTION ---
        if st.button("Log in", type="primary", key="btn_login"):
            if email and password:
                from database import sign_in
                user = sign_in(email, password)
                if user:
                    st.session_state['user'] = user
                    if 'supabase_session' in st.session_state:
                         try:
                             sess = st.session_state['supabase_session']
                             cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                         except: pass
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
        
        st.markdown('<a href="#" class="forgot-pass">Forgot password?</a>', unsafe_allow_html=True)
        
        # --- FOOTER ---
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        
        # Footer Columns: Text + Link Button
        c_f1, c_f2 = st.columns([1.5, 1])
        with c_f1:
            st.markdown('<div class="footer-text">Don\'t have an account?</div>', unsafe_allow_html=True)
        with c_f2:
            if st.button("Sign up", type="secondary", key="goto_signup"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

    with c_img:
        # Placeholder for 3D Image
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                border-radius: 16px;
                height: 550px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #9CA3AF;
                font-weight: 500;
            ">
                (Imagen 3D)
            </div>
        ''', unsafe_allow_html=True)

    st.stop()
"""

# APPLY THE REBUILD TO APP.PY
with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Scan for the login block boundaries
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if "if not st.session_state['user']" in line and "force_logout" in line:
        start_line = i
    if "st.stop()" in line and i > start_line + 50: # Ensure we capture the block end
        end_line = i + 1
        break

if start_line != -1 and end_line != -1:
    print(f"Replacing Login Block (Lines {start_line+1} to {end_line}) with Rebuild...")
    
    new_content = []
    new_content.extend(lines[:start_line])
    new_content.append(clean_login_code + "\n")
    new_content.extend(lines[end_line:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    print("SUCCESS: Full Login Rebuild Applied.")
else:
    print("ERROR: Could not locate login block for replacement.")
