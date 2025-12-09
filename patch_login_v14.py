
import os
import base64

app_path = 'app.py'

# 1. Login V14: "Aggressive" HTML Structure
# - Single Block for Logo + Title (Zero Spacing)
# - New Hero Image
# - Footer as Text Link
refined_login_code_v14 = '''
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    import base64
    
    # --- HELPER: ASSETS TO BASE64 ---
    def get_b64_image(image_path):
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    logo_b64 = get_b64_image("assets/logo_main.png")
    hero_b64 = get_b64_image("assets/login_hero_v14.jpg")
    
    # --- CUSTOM CSS FOR LOGIN PAGE V14 ---
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

        /* 2. REMOVE GAPS & DEBUG RED */
        div[data-testid="stVerticalBlock"] { gap: 0rem !important; }

        /* 3. INPUTS - Reference Style */
        .stTextInput { margin-bottom: 0px !important; }
        .stTextInput > div > div > input {
            background-color: white !important;
            color: #1F2937 !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            height: 48px !important; /* Standard Taller */
            padding-left: 12px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3500D3 !important;
            box-shadow: 0 0 0 2px rgba(53, 0, 211, 0.1) !important;
        }
        
        /* Label spacing hack */
        div[data-testid="stTextInput"] label {
            display: none;
        }

        /* 4. BUTTONS - Brand Purple */
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #3500D3 !important;
            color: white !important;
            border: none;
            border-radius: 8px !important;
            height: 48px !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            margin-top: 20px !important;
            width: 100% !important;
            box-shadow: 0 4px 6px -1px rgba(53, 0, 211, 0.2);
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #2900A5 !important;
        }

        /* 5. SECONDARY BUTTON (Sign up) - LINK STYLE */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            color: #111827 !important;
            border: none !important;
            padding: 0 !important;
            height: auto !important;
            font-weight: 700 !important; /* BOLD */
            text-decoration: none !important;
            display: inline !important;
            width: auto !important;
            margin: 0 !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline !important;
            color: #3500D3 !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:focus {
            box-shadow: none !important;
        }
        
        /* 6. TYPOGRAPHY & HEADER BLOCK */
        /* We handle Header in HTML, but these defaults help */
        .header-container {
            margin-bottom: 25px;
        }
        .login-logo {
            width: 100%;
            max-width: 380px; /* BIG LOGO LIMIT */
            display: block;
            margin-bottom: 0px !important; /* ZERO SPACING */
        }
        .login-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 2rem;
            color: #111827;
            margin-top: -5px; /* NEGATIVE MARGIN TO PULL UP */
            margin-bottom: 0px;
            line-height: 1.2;
        }
        .login-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #6B7280;
            margin-top: 8px;
            margin-bottom: 20px;
        }

        /* 7. HERO IMAGE CONTAINER */
        .hero-container {
            width: 100%;
            height: 100%;
            min-height: 600px;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.08);
        }
        .hero-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        /* HIDE UI */
        #MainMenu, header, footer { visibility: hidden !important; }
        </style>
    """, unsafe_allow_html=True)

    # LAYOUT
    c_form, c_spacer, c_img = st.columns([0.85, 0.05, 1.1])

    with c_form:
        # --- AGGRESSIVE COMPACT HEADER ---
        # Using a single HTML block for Logo + Title to guarantee 0px spacing
        img_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
        
        st.markdown(f"""
            <div class="header-container">
                <img src="{img_src}" class="login-logo">
                <div class="login-title">Log in to your account</div>
                <div class="login-subtitle">Welcome back! Please enter your details.</div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- INPUTS ---
        # Spacers are handled by CSS margin-bottom: 0 on inputs
        email = st.text_input("Email", key="login_email", placeholder="Enter your email", label_visibility="collapsed")
        
        # Tiny manual spacer for visual breathing room between inputs (15px)
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
        
        # Forgot Password
        st.markdown('<div style="text-align: center; margin-top: 15px;"><a href="#" style="color: #3500D3; text-decoration: none; font-weight: 600; font-size: 0.9rem;">Forgot password?</a></div>', unsafe_allow_html=True)
        
        # --- FOOTER (TEXT + LINK) ---
        st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
        
        # Using a flexbox container in HTML might be safer, but Streamlit button needs to be clickable.
        # Let's use the col trick again but with aligned text.
        c_f1, c_f2 = st.columns([0.6, 0.4])
        with c_f1:
             st.markdown("""<div style="text-align: right; color: #1F2937; font-size: 0.95rem; margin-top: 2px;">Don't have an account?</div>""", unsafe_allow_html=True)
        with c_f2:
             # The button is styled as a link via CSS
             if st.button("Sign up", type="secondary", key="goto_signup"):
                  st.session_state['auth_mode'] = 'signup'
                  st.rerun()

    with c_img:
        # --- HERO IMAGE ---
        if hero_b64:
            st.markdown(f"""
                <div class="hero-container">
                    <img src="data:image/jpeg;base64,{hero_b64}" class="hero-img">
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Hero image not found")

    st.stop()
'''

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
    print(f"Applying Login V14 to lines {start_line+1}-{end_line}...")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_line])
    # New Code
    new_lines.append(refined_login_code_v14 + '\\n')
    # Lines after
    new_lines.extend(lines[end_line:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS: Login V14 Applied (Aggressive HTML + New Hero).")
else:
    print("ERROR: Login block not found.")
