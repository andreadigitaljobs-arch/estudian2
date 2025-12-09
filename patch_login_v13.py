
import os
import base64

app_path = 'app.py'

# 1. Login V13: "Final Polish" - Reference Match
# Using TRIPLE SINGLE QUOTES for the main variable to allow TRIPLE DOUBLE QUOTES inside
refined_login_code_v13 = '''
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
    
    # --- CUSTOM CSS FOR LOGIN PAGE V13 ---
    st.markdown("""
        <style>
        /* 1. RESET & CONTAINER */
        .stApp { background-color: white !important; }
        
        .main .block-container {
            max_width: 1000px;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 85vh;
        }

        /* 2. REMOVE GAPS */
        div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }

        /* 3. INPUTS - Reference Style */
        .stTextInput { margin-bottom: -5px !important; }
        .stTextInput > div > div > input {
            background-color: white !important;
            color: #1F2937 !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            height: 45px !important; /* Slightly taller like reference */
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3500D3 !important;
            box-shadow: 0 0 0 3px rgba(53, 0, 211, 0.1) !important;
        }

        /* 4. BUTTONS - Brand Purple */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #3500D3 !important;
            color: white !important;
            border: none;
            border-radius: 8px !important;
            height: 45px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-top: 10px !important;
            width: 100% !important;
            box-shadow: 0 4px 6px -1px rgba(53, 0, 211, 0.2);
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #2900A5 !important;
        }

        /* 5. SECONDARY BUTTON (Sign up) - Refine Alignment */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            color: #3500D3 !important; 
            border: none !important;
            padding: 0 !important;
            height: auto !important;
            font-weight: 700 !important;
            line-height: inherit !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:focus {
            box-shadow: none !important;
        }

        /* 6. TYPOGRAPHY */
        .login-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.8rem;
            color: #111827;
            margin-top: 5px; /* Minimal top margin */
            margin-bottom: 5px;
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
            font-size: 0.9rem;
        }
        
        /* FOOTER ALIGNMENT CLASS */
        .footer-row {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 5px;
            font-size: 0.9rem;
            color: #4B5563;
        }

        /* HIDE UI */
        #MainMenu, header, footer { visibility: hidden !important; }
        </style>
    """, unsafe_allow_html=True)

    # LAYOUT: Use V10 Ratio [0.8, 1.2] as it was "Good" but with Big Logo
    c_form, c_spacer, c_img = st.columns([0.8, 0.1, 1.2])

    with c_form:
        # --- HEADER (BIG LOGO) ---
        # Logo Width: 300px (Requested "Huge")
        img_tag = f'<img src="data:image/png;base64,{logo_b64}" width="300">' if logo_b64 else '<h2>e-education</h2>'
        
        st.markdown(f"""
            <div style="text-align: left; margin-bottom: 10px;">
                {img_tag}
                <div class="login-title">Log in to your account</div>
                <div class="login-subtitle">Welcome back! Please enter your details.</div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- INPUTS ---
        email = st.text_input("Email", key="login_email", placeholder="Enter your email", label_visibility="collapsed")
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••", label_visibility="collapsed")
        
        # --- LOGIN BUTTON ---
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
        
        # --- FOOTER (Manual Flex Alignment Trick) ---
        st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
        
        # Use Columns to approximate "Sentences"
        # "Don't have an account?" (Col 1) | "Sign up" (Col 2)
        # We push Col 1 right, and Col 2 left to make them touch.
        c_f1, c_f2 = st.columns([0.65, 0.35])
        with c_f1:
             st.markdown("""<div style="text-align: right; color: #4B5563; font-size: 0.9rem; padding-top: 2px;">Don't have an account?</div>""", unsafe_allow_html=True)
        with c_f2:
             if st.button("Sign up", type="secondary", key="goto_signup"):
                  st.session_state['auth_mode'] = 'signup'
                  st.rerun()

    with c_img:
        st.markdown("""
            <div style="
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                border-radius: 20px;
                height: 550px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #9CA3AF;
                font-weight: 500;
            ">
                (Imagen 3D)
            </div>
        """, unsafe_allow_html=True)

    st.stop()
'''

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Locate Login Block (Rebuilt one)
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if "if not st.session_state['user']" in line and "force_logout" in line:
        start_line = i
    if "st.stop()" in line and i > start_line + 50:
        end_line = i + 1
        break

if start_line != -1 and end_line != -1:
    print(f"Applying Login V13 to lines {start_line+1}-{end_line}...")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_line])
    # New Code
    new_lines.append(refined_login_code_v13 + '\\n')
    # Lines after
    new_lines.extend(lines[end_line:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS: Login V13 Applied (Big Logo, Clean Ref).")
else:
    print("ERROR: Login block not found.")
