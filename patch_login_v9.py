
import os
import base64

app_path = 'app.py'

# 1. Login V9: Compact Professional, Vibrant Purple, High Position
refined_login_code_v9 = """
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
    
    # --- CUSTOM CSS FOR LOGIN PAGE V9 ---
    st.markdown('''
        <style>
        /* 1. AGGRESSIVE LAYOUT RESET */
        .stApp { background-color: white; }
        
        .main .block-container {
            padding-top: 0rem !important; /* Top of screen */
            padding-bottom: 0rem !important;
            max_width: 900px !important; /* Compact width */
            margin: 0 auto;
        }

        /* 2. MOVE CONTENT UP (Negative Margins) */
        div[data-testid="stVerticalBlock"] {
            margin-top: -30px; 
            gap: 0.5rem !important;
        }

        /* 3. INPUTS: REFINED & PROFESSIONAL */
        /* Height 40px, thin border, refined radius */
        .stTextInput {
            margin-bottom: -10px !important; /* Tight spacing */
        }
        .stTextInput > div > div > input {
            border-radius: 6px !important; 
            border: 1px solid #D1D5DB; /* Light gray */
            padding: 8px 12px;
            background-color: #FFFFFF;
            color: #1F2937;
            font-size: 0.9rem;
            height: 40px;
            line-height: 40px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4318FF; /* Vibrant Brand Purple */
            box-shadow: 0 0 0 3px rgba(67, 24, 255, 0.1);
        }

        /* 4. BUTTON: VIBRANT & SLEEK */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #4318FF !important; /* Bright Professional Purple */
            color: white !important;
            border: none;
            border-radius: 6px !important; 
            height: 40px;
            font-weight: 600;
            font-size: 0.95rem;
            margin-top: 15px;
            box-shadow: 0 4px 6px -1px rgba(67, 24, 255, 0.2);
            transition: all 0.2s;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #3300E0 !important;
            box-shadow: 0 10px 15px -3px rgba(67, 24, 255, 0.3);
            transform: translateY(-1px);
        }

        /* 5. TEXT REFINEMENTS */
        .login-super-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.5rem; /* Much smaller than before */
            color: #111827;
            margin-bottom: 4px;
        }
        .login-sub-title {
            font-size: 0.9rem;
            color: #6B7280;
            margin-bottom: 20px;
        }
        .forgot-pass {
            color: #4318FF;
            font-weight: 600;
            font-size: 0.8rem;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 12px;
        }
        
        /* 6. HIDE NAV */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # Layout: Form (Compact) | Image
    # Using columns to center vertical alignment 
    # spacer, form, img, spacer
    
    st.write("") # Trigger top padding strip
    
    c_form, c_img = st.columns([0.8, 1.2], gap="large")

    with c_form:
        # --- HTML HEADER ---
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 180px; margin-bottom: 24px;">' if logo_b64 else '<h2>e-education</h2>'
        
        st.markdown(f'''
            <div style="margin-top: 20px; margin-bottom: 20px;">
                {logo_html}
                <div class="login-super-title">Log in to your account</div>
                <div class="login-sub-title">Welcome back! Please enter your details.</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # --- INPUTS ---
        email = st.text_input("Email", key="login_email", placeholder="Enter your email", label_visibility="collapsed")
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True) # Explicit small gap
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
        
        st.markdown(
            '''<div style='text-align: center; color: #374151; font-size: 0.85rem; margin-top: 30px;'>
            Don't have an account? <b>Sign up</b>
            </div>''', 
            unsafe_allow_html=True
        )
        if st.button("Sign up Toggle", type="secondary", key="goto_signup", use_container_width=True):
             st.session_state['auth_mode'] = 'signup'
             st.rerun()

    with c_img:
        # Placeholder for Image (Right Side)
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
    print(f"Replacing Login V9 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v9 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V9 (Professional/Vibrant).")
else:
    print("ERROR: Login block not found.")
