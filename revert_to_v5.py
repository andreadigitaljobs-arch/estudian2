
import os
import base64

app_path = 'app.py'

# 1. Login V5: RESTORING "PERFECT MATCH" VERSION
# - Centered layouts, Deep Purple colors.
# - Rounded inputs.
# - Using the NEW Hero Image instead of the old gradient placeholder.
refined_login_code_v5 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    import datetime
    
    # --- CUSTOM CSS FOR LOGIN PAGE V5 ---
    st.markdown('''
        <style>
        /* RESET & BACKGROUND */
        .stApp {
            background-color: white;
        }

        /* REMOVE PADDING */
        .main .block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            max_width: 1100px;
        }

        /* CENTER CONTENT IN FORM COLUMN */
        div[data-testid="column"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        /* INPUTS - Rounded (12px), Light Border */
        .stTextInput > div > div > input {
            border-radius: 12px !important; 
            border: 1px solid #E2E8F0;
            padding: 12px 16px;
            background-color: #FFFFFF;
            color: #333;
            font-size: 1rem;
            height: 50px;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3C096C; /* Deep Purple Focus */
            box-shadow: 0 0 0 2px rgba(60, 9, 108, 0.1);
        }

        /* PRIMARY BUTTON - Deep Purple, Rounded 12px */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #240046 !important; /* Very Deep Purple to match "Log in" button in image */
            color: white !important;
            border: none;
            border-radius: 12px !important; 
            height: 50px;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.3px;
            margin-top: 10px;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.95;
            background-color: #3C096C !important;
        }

        /* SECONDARY BUTTON - Bottom Text */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #333 !important;
            padding: 0 !important;
            margin-top: 5px;
        }

        /* LINKS & TEXT */
        .login-title {
            font-family: 'Inter', sans-serif;
            color: #101828;
            font-weight: 800;
            font-size: 1.8rem;
            text-align: center;
            margin-bottom: 1.5rem;
            margin-top: 0.5rem;
        }
        
        .forgot-pass {
            color: #240046;
            font-weight: 700;
            font-size: 0.9rem;
            text-decoration: none;
            display: block;
            text-align: center;
            margin-top: 15px;
            margin-bottom: 25px;
        }

        /* DIVIDER */
        .divider {
            border-top: 1px solid #F2F4F7;
            margin-bottom: 20px;
        }

        /* HIDE DEFAULT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # Note: Column Ratio 0.8 : 1.2
    c_form, c_img = st.columns([0.9, 1.1], gap="large")

    with c_form:
        # LOGO - CENTERED & LARGER
        # Use a centered column for the logo specifically to guarantee it
        c_l, c_logo, c_r = st.columns([0.1, 0.8, 0.1])
        with c_logo:
             if os.path.exists("assets/logo_main.png"):
                 st.image("assets/logo_main.png", use_container_width=True) # Full width of the centered column
             else:
                 st.markdown("<h2 style='text-align:center; color:#240046;'>e-education</h2>", unsafe_allow_html=True)
        
        # TITLE
        st.markdown('<h1 class="login-title">Log in to your account</h1>', unsafe_allow_html=True)
        
        # FORM INPUTS
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
        st.write("") 
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
                    st.error("Credenciales incorrectas.")
            else:
                st.warning("Ingresa tus datos.")

        # FORGOT PASS
        st.markdown('<a href="#" class="forgot-pass">Forgot password?</a>', unsafe_allow_html=True)

        # DIVIDER
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # SIGN UP LINK - CENTERED
        st.markdown("<div style='text-align: center; color: #333; margin-bottom: 5px;'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Sign up", type="secondary", key="goto_signup", use_container_width=True):
             st.session_state['auth_mode'] = 'signup'
             st.rerun()

    with c_img:
        # HERO IMAGE (Restored V5 Layout but with NEW image)
        hero_path = "assets/login_hero_final.png"
        hero_b64 = None
        if os.path.exists(hero_path):
             import base64
             with open(hero_path, "rb") as f:
                  hero_b64 = base64.b64encode(f.read()).decode()
        
        if hero_b64:
             st.markdown(f'''
                <div style="
                    border-radius: 20px; 
                    height: 650px; 
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.05);
                ">
                    <img src="data:image/png;base64,{hero_b64}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
             ''', unsafe_allow_html=True)
        else:
             # Fallback V5 Gradient if image missing
             st.markdown('''
                <div style="
                    background: linear-gradient(135deg, #F9F5FF 0%, #F3E8FF 100%); 
                    border-radius: 20px; 
                    height: 650px; 
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
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if "if not st.session_state['user']" in line and "force_logout" in line:
        start_line = i
    if "st.stop()" in line and i > start_line + 50:
        end_line = i + 1
        break

if start_line != -1 and end_line != -1:
    print(f"Applying REVERT V5 to lines {start_line+1}-{end_line}...")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_line])
    # New Code
    new_lines.append(refined_login_code_v5 + '\\n')
    # Lines after
    new_lines.extend(lines[end_line:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS: REVERTED TO LOGIN V5 (The Good One).")
else:
    print("ERROR: Login block not found.")
