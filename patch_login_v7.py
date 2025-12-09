
import os

app_path = 'app.py'

# 1. Login V7: Tighter Spacing, Higher Position
refined_login_code_v7 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    
    # --- CUSTOM CSS FOR LOGIN PAGE V7 ---
    st.markdown('''
        <style>
        /* 1. BACKGROUND */
        .stApp {
            background-color: white;
        }

        /* 2. MAIN CONTAINER POSITIONING */
        /* "Sube todo": We use a fixed top padding instead of centering */
        .main .block-container {
            padding-top: 3rem; /* Higher position */
            padding-bottom: 2rem;
            max_width: 950px;
        }

        /* 3. TIGHTEN ELEMENTS */
        /* Target the gaps Streamlit puts between elements */
        div[data-testid="element-container"] {
            margin-bottom: 0px !important; /* Force tighter stacking */
        }
        
        /* 4. TITLE POSITIONING */
        /* "Quita ese tremendo espacio": Pull title up towards logo */
        .login-title {
            font-family: 'Inter', sans-serif;
            color: #101828;
            font-weight: 700;
            font-size: 1.6rem;
            text-align: center;
            margin-bottom: 1rem;
            margin-top: -10px; /* Negative margin to pull up */
            padding-top: 0px;
        }

        /* 5. INPUTS - Clean & Compact */
        .stTextInput > div > div > input {
            border-radius: 8px !important; 
            border: 1px solid #E2E8F0;
            padding: 10px 14px;
            background-color: #FFFFFF;
            color: #333;
            font-size: 0.95rem;
            height: 45px;
            margin-bottom: 0px; /* Remove default margins */
        }
        .stTextInput > div > div > input:focus {
            border-color: #240046;
            box-shadow: 0 0 0 1px #240046;
        }
        /* Fix input spacing */
        div[data-testid="stTextInput"] {
            margin-bottom: 10px;
        }

        /* 6. BUTTON */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #240046 !important; 
            color: white !important;
            border: none;
            border-radius: 8px !important; 
            height: 45px;
            font-weight: 600;
            font-size: 1rem;
            margin-top: 10px;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.95;
            background-color: #3C096C !important;
        }

        /* 7. SECONDARY ELEMENTS */
        .forgot-pass {
            color: #240046;
            font-weight: 600;
            font-size: 0.85rem;
            text-align: center;
            display: block;
            margin-top: 15px;
            margin-bottom: 20px;
            text-decoration: none;
        }

        div[data-testid="stButton"] > button[kind="secondary"] {
            padding: 0px !important;
            border: none;
            background: none;
            color: #333;
        }

        /* HIDE UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        </style>
    ''', unsafe_allow_html=True)

    # Layout
    c_form, c_img = st.columns([1, 1.2], gap="large")

    with c_form:
        # LOGO
        # Ensure it's centered without standard columns if possible to reduce gap
        # Or use a very clean column structure
        c_l, c_logo, c_r = st.columns([0.15, 0.7, 0.15])
        with c_logo:
             if os.path.exists("assets/logo_main.png"):
                 st.image("assets/logo_main.png", use_container_width=True) 
             else:
                 st.header("e-education")
        
        # TITLE
        # Directly below, CSS pulls it up
        st.markdown('<h1 class="login-title">Log in to your account</h1>', unsafe_allow_html=True)
        
        # FORM ELEMENTS
        # Removed st.write("") spacers to close gap
        
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
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
            '''<div style='text-align: center; color: #333; font-size: 0.9rem; margin-top: 10px;'>
            Don't have an account? <b>Sign up</b>
            </div>''', 
            unsafe_allow_html=True
        )
        # Hidden clickable trigger for signup
        if st.button("Sign up Toggle", type="secondary", key="goto_signup", use_container_width=True):
             st.session_state['auth_mode'] = 'signup'
             st.rerun()

    with c_img:
        # Placeholder for Image (Right Side)
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F9F5FF 0%, #EDE9FE 100%); 
                border-radius: 16px; 
                height: 550px; 
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
    print(f"Replacing Login V7 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v7 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V7 (Tighter & Higher).")
else:
    print("ERROR: Login block not found.")
