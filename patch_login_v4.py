
import os

app_path = 'app.py'

# 1. Login V4: Pixel Perfect Reference Match
refined_login_code_v4 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    
    # --- CUSTOM CSS FOR LOGIN PAGE V4 ---
    st.markdown('''
        <style>
        /* RESET & BACKGROUND */
        .stApp {
            background-color: white;
        }

        /* REMOVE TOP PADDING from Main Container to allow centered layout */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max_width: 1200px;
        }

        /* INPUTS - Reference Style */
        /* Smooth border, light gray bg, approx 8-10px radius */
        .stTextInput > div > div > input {
            border-radius: 8px !important; 
            border: 1px solid #E5E7EB;
            padding: 12px 16px;
            background-color: #FFFFFF; /* Reference looks white/transparent or very light gray */
            color: #333;
            font-size: 1rem;
            height: 48px; /* Fixed height for consistency */
        }
        .stTextInput > div > div > input:focus {
            border-color: #4B0082; /* Deep Indigo/Purple */
            box-shadow: 0 0 0 1px #4B0082;
        }

        /* PRIMARY BUTTON - Reference Style */
        /* Deep Purple, Rectangular-ish with rounded corners */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #31006E !important; /* Deep Purple from ref */
            color: white !important;
            border: none;
            border-radius: 8px !important; 
            padding: 0px 16px;
            height: 48px; /* Match input height */
            font-weight: 600;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
            box-shadow: none; /* Flat look or subtle */
            transition: opacity 0.2s ease;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            opacity: 0.9;
        }

        /* SECONDARY BUTTON - Bottom Text Link */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #1F2937 !important; /* Slate 800 */
            padding: 0 !important;
            font-size: 0.95rem;
        }
        div[data-testid="stButton"] > button[kind="secondary"] p {
            font-weight: 400;
        }
        div[data-testid="stButton"] > button[kind="secondary"] p strong {
            font-weight: 700;
            color: #1F2937; /* Or black */
        }

        /* FORGOT PASSWORD LINK */
        a.forgot-pass {
            color: #31006E;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            display: block;
            text-align: center;
            margin-top: 15px;
        }
        a.forgot-pass:hover {
            text-decoration: underline;
        }

        /* HEADERS */
        h1.login-title {
            font-family: 'Inter', sans-serif;
            color: #111827; /* Near black */
            font-weight: 700;
            font-size: 1.75rem;
            margin-bottom: 0rem;
            margin-top: 1rem;
        }

        /* HIDE DEFAULT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} /* Hide Top bar for clean look */
        </style>
    ''', unsafe_allow_html=True)

    # Note: Using native st.columns for layout
    # Left: Form (35%), Right: Image (65%) - Reference ratio approx
    c_form, c_img = st.columns([1, 1.2], gap="large")

    with c_form:
        # LOGO
        if os.path.exists("assets/logo_main.png"):
             st.image("assets/logo_main.png", width=180) 
        else:
             st.markdown("<h3 style='color:#31006E;'>e-education</h3>", unsafe_allow_html=True)
        
        # TITLE
        st.markdown('<h1 class="login-title">Log in to your account</h1>', unsafe_allow_html=True)
        st.write("") # Spacer
        
        # INPUTS - Using placeholders to match "Email" inside box logic
        # Note: label_visibility="collapsed" removes the label space entirely
        email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="collapsed")
        st.write("") # Small gap
        password = st.text_input("Password", type="password", key="login_pass", placeholder="Password", label_visibility="collapsed")
        
        st.write("") # Gap before button
        
        # PRIMARY BUTTON
        # Using a container to enforce width if needed, but CSS handles it
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
                    st.error("Invalid credentials.")
            else:
                st.warning("Please enter your email and password.")

        # FORGOT PASSWORD
        st.markdown('<a href="#" class="forgot-pass">Forgot password?</a>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 40px; border-top: 1px solid #E5E7EB;'></div>", unsafe_allow_html=True)
        
        # FOOTER: Don't have an account? Sign up
        # We use a button for the "Sign up" action to allow state toggle
        c_foot = st.container()
        with c_foot:
             st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
             # To create the mixed text "Don't have an account? Sign up" where Sign up is clickable:
             # Streamlit buttons are all-or-nothing. 
             # We will use columns to tight-pack them or just a single button that says the whole phrase but styles the "Sign up" part bold.
             
             if st.button("Don't have an account? **Sign up**", type="secondary", key="goto_signup", use_container_width=True):
                 # Toggle logic would go here if we implemented the SignUp form similarly
                 # For now, just a placeholder or toggle state
                 pass

    with c_img:
        # Placeholder for 3D Image - Reference shows it on a white/light bg, floating elements
        # User said "The only exception is the image". So we keep a placeholder.
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%); 
                border-radius: 20px; 
                height: 600px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                color: #5B21B6;
            ">
                (Image Placeholder)
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
    print(f"Replacing Login V4 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v4 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V4 (Reference Match).")
else:
    print("ERROR: Login block not found.")
