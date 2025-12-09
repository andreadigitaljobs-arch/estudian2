
import os
import base64

app_path = 'app.py'

# 1. Login V11: Larger Logo, Closer Title
refined_login_code_v11 = """
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
    
    # --- CUSTOM CSS FOR LOGIN PAGE V11 ---
    st.markdown('''
        <style>
        /* 1. LAYOUT RESET */
        .stApp { background-color: white; }
        
        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            max_width: 900px !important;
            margin: 0 auto;
        }

        /* 2. MOVE CONTENT UP */
        div[data-testid="stVerticalBlock"] {
            margin-top: -30px; 
            gap: 0.5rem !important;
        }

        /* 3. INPUTS */
        .stTextInput { margin-bottom: -10px !important; }
        .stTextInput > div > div > input {
            border-radius: 6px !important; 
            border: 1px solid #D1D5DB; 
            padding: 8px 12px;
            background-color: #FFFFFF;
            color: #1F2937;
            font-size: 0.9rem;
            height: 40px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3500D3; 
            box-shadow: 0 0 0 3px rgba(53, 0, 211, 0.1);
        }

        /* 4. PRIMARY BUTTON */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #3500D3 !important;
            color: white !important;
            border: none;
            border-radius: 6px !important; 
            height: 40px;
            font-weight: 600;
            font-size: 0.95rem;
            margin-top: 15px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.2s;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #2900A5 !important;
            transform: translateY(-1px);
        }

        /* 5. SECONDARY BUTTON */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background-color: transparent !important;
            color: #3500D3 !important;
            border: none !important;
            padding: 0px !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            height: auto !important;
            margin-top: 2px !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline;
            color: #2900A5 !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:focus {
            box-shadow: none !important;
            border-color: transparent !important;
        }

        /* 6. TEXT STYLES */
        .login-super-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.6rem; /* Slightly larger to match Logo scale */
            color: #111827;
            margin-bottom: 5px;
            letter-spacing: -0.5px;
        }
        .login-sub-title {
            font-size: 0.9rem;
            color: #6B7280;
            margin-bottom: 25px; /* Spacer before inputs */
        }
        .forgot-pass {
            color: #3500D3;
            font-weight: 600;
            font-size: 0.8rem;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 12px;
        }
        .signup-text {
            color: #374151;
            font-size: 0.9rem;
            text-align: right;
            margin-right: 5px;
        }
        
        /* HIDE NAV */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    st.write("") 
    
    c_form, c_img = st.columns([0.8, 1.2], gap="large")

    with c_form:
        # --- HEADER V11: BIG LOGO & CLOSE TITLE ---
        # Width increased to 260px. Margin bottom reduced to 8px.
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 260px; margin-bottom: 8px;">' if logo_b64 else '<h2>e-education</h2>'
        
        st.markdown(f'''
            <div style="margin-top: 20px; margin-bottom: 5px;">
                {logo_html}
                <div class="login-super-title">Log in to your account</div>
                <div class="login-sub-title">Welcome back! Please enter your details.</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # --- FORM ---
        email = st.text_input("Email", key="login_email", placeholder="Enter your email", label_visibility="collapsed")
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True) 
        password = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••", label_visibility="collapsed")
        
        if st.button("Log in", type="primary", key="btn_login", use_container_width=True):
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
        st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
        
        c_foot_1, c_foot_2 = st.columns([1.5, 1])
        with c_foot_1:
             st.markdown('<div class="signup-text">Don\'t have an account?</div>', unsafe_allow_html=True)
        with c_foot_2:
             if st.button("Sign up", type="secondary", key="goto_signup"):
                  st.session_state['auth_mode'] = 'signup'
                  st.rerun()

    with c_img:
        # Placeholder for Image
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%); 
                border-radius: 12px; 
                height: 500px; 
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

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Locate Login Block
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "if not st.session_state['user']" in line and "force_logout" in line:
        start_idx = i
    if "st.stop()" in line and i > start_idx + 10:
        end_idx = i + 1
        break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Login V11 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v11 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V11 (Larger Logo, Closer Title).")
else:
    print("ERROR: Login block not found.")
