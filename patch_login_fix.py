
import os
import base64

app_path = 'app.py'

# 1. Login V8 + FIX: Added import base64
refined_login_code_v8_fix = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    import base64 # FIX: Ensure base64 is imported locally
    
    # --- HELPER: LOGO TO BASE64 ---
    def get_logo_b64():
        path = "assets/logo_main.png"
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    logo_b64 = get_logo_b64()
    
    # --- CUSTOM CSS FOR LOGIN PAGE V8 ---
    st.markdown('''
        <style>
        /* 1. FORCE TOP POSITION */
        .main .block-container {
            padding-top: 1.5rem !important; /* Extremely high up */
            padding-bottom: 2rem;
            max_width: 1000px;
        }

        /* 2. REMOVE STREAMLIT GAPS */
        div[data-testid="stVerticalBlock"] > div {
            gap: 0rem !important;
        }
        
        /* 3. INPUT STYLING */
        .stTextInput {
            margin-bottom: -15px !important;
        }
        .stTextInput > div > div > input {
            border-radius: 10px !important; 
            border: 1px solid #E2E8F0;
            padding: 10px 14px;
            background-color: #FFFFFF;
            color: #333;
            font-size: 0.95rem;
            height: 48px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #240046;
            box-shadow: 0 0 0 1px #240046;
        }

        /* 4. BUTTON STYLING */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #240046 !important; 
            color: white !important;
            border: none;
            border-radius: 10px !important; 
            height: 48px;
            font-weight: 700;
            font-size: 1rem;
            margin-top: 20px;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.95;
            background-color: #3C096C !important;
        }

        /* 5. TEXT LINKS */
        .forgot-pass {
            color: #240046;
            font-weight: 700;
            font-size: 0.85rem;
            text-align: center;
            display: block;
            margin-top: 15px;
            text-decoration: none;
        }
        
        /* HIDE UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # Layout: Form | Image
    c_form, c_img = st.columns([0.9, 1.3], gap="large")

    with c_form:
        # --- HTML BLOCK FOR LOGO & TITLE ---
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 250px; margin-bottom: 20px;">' if logo_b64 else '<h2>e-education</h2>'
        
        st.markdown(f'''
            <div style="text-align: center; margin-bottom: 30px; margin-top: 0px;">
                {logo_html}
                <div style="
                    font-family: 'Inter', sans-serif; 
                    font-weight: 800; 
                    font-size: 1.8rem; 
                    color: #101828; 
                    line-height: 1.2;
                ">
                    Log in to your account
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # --- INPUTS ---
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
        
        st.markdown("<div style='margin-bottom: 12px'></div>", unsafe_allow_html=True) 
        
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Password", label_visibility="collapsed")
        
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
            '''<div style='text-align: center; color: #333; font-size: 0.9rem; margin-top: 25px;'>
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
                background: linear-gradient(135deg, #F9F5FF 0%, #EDE9FE 100%); 
                border-radius: 24px; 
                height: 600px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                color: #5B21B6;
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
    print(f"Replacing Login V8 Fix at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v8_fix + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V8 Fix (Import Added).")
else:
    print("ERROR: Login block not found.")
