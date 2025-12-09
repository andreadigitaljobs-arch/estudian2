
import os

app_path = 'app.py'

# 1. Login V6: Compact, Vertically Centered, Fixed Alignment
refined_login_code_v6 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    
    # --- CUSTOM CSS FOR LOGIN PAGE V6 ---
    st.markdown('''
        <style>
        /* 1. RESET & BACKGROUND */
        .stApp {
            background-color: white;
        }

        /* 2. COMPACT MAIN CONTAINER */
        /* Center everything vertically and limit width */
        .main .block-container {
            padding-top: 1rem; /* minimal padding */
            padding-bottom: 1rem;
            max-width: 900px; /* Reduced from 1200px to keep elements closer */
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-height: 90vh; /* Force full height centering */
        }

        /* 3. INPUTS - Compact & Clean */
        .stTextInput > div > div > input {
            border-radius: 8px !important; 
            border: 1px solid #E2E8F0;
            padding: 8px 12px; /* Smaller padding */
            background-color: #FFFFFF;
            color: #333;
            font-size: 0.95rem; /* Slightly smaller text */
            height: 42px; /* Reduced height from 50px */
        }
        .stTextInput > div > div > input:focus {
            border-color: #240046;
            box-shadow: 0 0 0 1px #240046;
        }

        /* 4. PRIMARY BUTTON - Compact */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #240046 !important; 
            color: white !important;
            border: none;
            border-radius: 8px !important; 
            height: 42px; /* Match input height */
            font-weight: 600;
            font-size: 1rem;
            margin-top: 5px;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.95;
            background-color: #3C096C !important;
        }

        /* 5. SECONDARY BUTTON */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #333 !important;
            padding: 0 !important;
            font-size: 0.9rem;
        }

        /* 6. TYPOGRAPHY */
        .login-title {
            font-family: 'Inter', sans-serif;
            color: #101828;
            font-weight: 700;
            font-size: 1.5rem; /* Reduced from 1.8 */
            text-align: center;
            margin-bottom: 1rem;
            margin-top: 0.5rem;
        }
        
        .forgot-pass {
            color: #240046;
            font-weight: 600;
            font-size: 0.85rem;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 10px;
            margin-bottom: 15px;
        }
        
        /* 7. HIDE STREAMLIT UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 8. ALIGNMENT FIX FOR COLUMNS */
        /* This ensures columns align to middle vertically */
        [data-testid="stHorizontalBlock"] {
            align-items: center;
        }
        </style>
    ''', unsafe_allow_html=True)

    # Note: Column Ratio 0.8 : 1.2
    # We use st.container with a restricted width implicitly via max-width CSS above
    c_form, c_img = st.columns([1, 1.2], gap="large")

    with c_form:
        # LOGO - Centered, Smaller
        c_l, c_logo, c_r = st.columns([0.2, 0.6, 0.2])
        with c_logo:
             if os.path.exists("assets/logo_main.png"):
                 st.image("assets/logo_main.png", use_container_width=True) 
             else:
                 st.markdown("<h3 style='text-align:center; color:#240046;'>e-education</h3>", unsafe_allow_html=True)
        
        # TITLE
        st.markdown('<h1 class="login-title">Log in to your account</h1>', unsafe_allow_html=True)
        
        # FORM (Compact)
        # Using label_visibility="collapsed" to match design tightly
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
        st.write("") # Minimal spacer (approx 10px due to markdown margin)
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Password", label_visibility="collapsed")
        
        # BUTTON
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
                    st.error("Error de credenciales.")
            else:
                st.warning("Ingresa tus datos.")

        # FORGOT PASS
        st.markdown('<a href="#" class="forgot-pass">Forgot password?</a>', unsafe_allow_html=True)

        # SIGN UP LINK - CENTERED
        # Using a single markdown line for tightness
        st.markdown(
            '''<div style='text-align: center; color: #333; font-size: 0.9rem;'>
            Don't have an account? <b>Sign up</b> Below
            </div>''', 
            unsafe_allow_html=True
        )
        
        # Using a secondary button that looks like a link or just a standard secondary button
        if st.button("Sign up Here", type="secondary", key="goto_signup", use_container_width=True):
             st.session_state['auth_mode'] = 'signup'
             st.rerun()

    with c_img:
        # Placeholder for Image (Right Side)
        # Fixed height to match form height roughly
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F9F5FF 0%, #EDE9FE 100%); 
                border-radius: 16px; 
                height: 500px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                color: #5B21B6;
                box-shadow: inset 0 0 20px rgba(0,0,0,0.02);
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
    print(f"Replacing Login V6 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v6 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V6 (Compact & Aligned).")
else:
    print("ERROR: Login block not found.")
