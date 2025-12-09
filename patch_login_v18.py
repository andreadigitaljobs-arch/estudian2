
import os
import base64

app_path = 'app.py'

# 1. Login V18: "Messimo Style"
# - Split Layout: Hero Image Left | Form Right (typical modern split).
# - "Pill" Shapes: Border-radius 30px+ for inputs and buttons.
# - Clean, spacious, minimalist.
refined_login_code_v18 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    import datetime
    
    # --- HELPER: ASSETS ---
    def get_b64_image(image_path):
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    logo_b64 = get_b64_image("assets/logo_main.png")
    hero_b64 = get_b64_image("assets/messimo_hero.jpg") # The new Purple Hoodie image

    # --- CUSTOM CSS FOR MESSIMO STYLE ---
    st.markdown('''
        <style>
        /* 1. RESET */
        .stApp { background-color: white; }
        
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max_width: 1200px !important;
            margin: 0 auto;
        }

        /* 2. PILL SHAPED INPUTS */
        .stTextInput > div > div > input {
            border-radius: 50px !important; /* Full Pill */
            border: 1px solid #E5E7EB;
            padding: 12px 20px;
            background-color: white;
            color: #374151;
            height: 50px;
            font-size: 0.95rem;
        }
        .stTextInput > div > div > input:focus {
            border-color: #3500D3;
            box-shadow: 0 0 0 2px rgba(53, 0, 211, 0.1);
        }

        /* 3. PILL SHAPED BUTTON (Primary) */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #3500D3 !important; /* Keeping Brand Purple */
            color: white !important;
            border: none;
            border-radius: 50px !important; /* Full Pill */
            height: 50px;
            font-weight: 700;
            font-size: 1rem;
            margin-top: 10px;
            box-shadow: 0 4px 12px rgba(53, 0, 211, 0.2);
            transition: transform 0.1s;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            transform: translateY(-1px);
            background-color: #2900A5 !important;
        }

        /* 4. SECONDARY BUTTON (Link Style for Footer) */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #3500D3 !important;
            padding: 0 !important;
            font-weight: 700 !important;
            height: auto !important;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline;
        }

        /* 5. TYPOGRAPHY */
        .messimo-title {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 2.2rem;
            color: #111827;
            text-align: center;
            margin-bottom: 0.5rem;
            line-height: 1.1;
        }
        .messimo-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            font-weight: 800;
            font-size: 1.5rem;
            color: #374151;
            gap: 10px;
        }

        /* 6. SOCIAL BUTTONS (Visual Only) */
        .social-row {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            margin-bottom: 30px;
        }
        .social-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            border: 1px solid #E5E7EB;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 1.2rem;
            color: #374151;
            background: white;
            transition: background 0.2s;
        }
        .social-btn:hover {
            background-color: #F9FAFB;
        }

        /* 7. HERO IMAGE CONTAINER */
        .hero-col {
            border-radius: 30px;
            overflow: hidden;
            height: 650px;
            position: relative;
        }
        .hero-img-fill {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        /* HIDE UI */
        #MainMenu, header, footer { visibility: hidden !important; }
        </style>
    ''', unsafe_allow_html=True)

    # LAYOUT: Image Left (Purple) | Form Right (White) 
    # Reference "Messimo" has Visual Left, Form Right (implied by reading order or common pattern, though reference image 0 cropped it tightly).
    # Wait, reference image 0 has the "Messimo" guy on the LEFT in the GREEN background.
    # So we will do: Col 1 (Image), Col 2 (Form).
    
    c_img, c_spacer, c_form = st.columns([1.1, 0.1, 0.9])

    with c_img:
        # HERO IMAGE
        if hero_b64:
             st.markdown(f'''
                <div class="hero-col">
                    <img src="data:image/jpeg;base64,{hero_b64}" class="hero-img-fill">
                </div>
             ''', unsafe_allow_html=True)
        else:
             st.error("Hero image asset missing.")

    with c_form:
        # SPACER TOP
        st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
        
        # LOGO "messimo" style (Icon + Text)
        if logo_b64:
            logo_src = f"data:image/png;base64,{logo_b64}"
            st.markdown(f'''
                <div class="messimo-logo">
                    <img src="{logo_src}" style="height: 40px; width: auto;">
                    <span>e-education</span>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="messimo-logo">e-education</div>', unsafe_allow_html=True)
        
        # HEADING
        st.markdown('<div class="messimo-title">Log in</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #6B7280; margin-bottom: 30px;">Welcome back to your account</div>', unsafe_allow_html=True)
        
        # FORM
        email = st.text_input("Email address", key="login_email", placeholder="Email address", label_visibility="collapsed")
        st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)
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
        
        # OR SIGN UP WITH (Visual Placeholder)
        st.markdown('''
            <div style="text-align: center; color: #9CA3AF; font-size: 0.85rem; margin-top: 25px; margin-bottom: 20px;">
                or log in with
            </div>
            <div class="social-row">
                <div class="social-btn">G</div> <!-- Google Placeholder -->
                <div class="social-btn">Microsoft</div> <!-- Windows Placeholder -->
                <div class="social-btn">Apple</div> <!-- Apple/Github Placeholder -->
            </div>
            
            <div style="text-align: center; font-size: 0.8rem; color: #6B7280; margin-top: 40px;">
                By logging in you agree to our <b>Terms of Services</b> and <b>Privacy Policy</b>.
            </div>
        ''', unsafe_allow_html=True)
        
        # FOOTER LINK
        st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True)
        c_f1, c_f2 = st.columns([1.5, 1])
        with c_f1:
            st.markdown('<div style="text-align: right; color: #1F2937; margin-top: 5px;">Don\'t have an account?</div>', unsafe_allow_html=True)
        with c_f2:
            if st.button("Sign up", type="secondary", key="goto_signup"):
                st.session_state['auth_mode'] = 'signup'
                st.rerun()

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
    print(f"Applying Login V18 (Messimo) to lines {start_line+1}-{end_line}...")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_line])
    # New Code
    new_lines.append(refined_login_code_v18 + '\\n')
    # Lines after
    new_lines.extend(lines[end_line:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("SUCCESS: Login V18 Applied (Messimo Style).")
else:
    print("ERROR: Login block not found.")
