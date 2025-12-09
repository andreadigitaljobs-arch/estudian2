
import os

app_path = 'app.py'

# 1. New Login CSS and Logic
new_login_code = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user']:
    
    # --- CUSTOM CSS FOR LOGIN PAGE ---
    st.markdown('''
        <style>
        /* General Page Background (Light Purple Tint for "E-Education" feel) */
        .stApp {
            background-color: #F3F0FF;
            background-image: linear-gradient(135deg, #F3F0FF 0%, #E8FFF0 100%);
        }

        /* CARD STYLE targeting the RIGHT COLUMN */
        /* Note: This selector targets the 2nd column in the horizontal layout */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div {
            background-color: white;
            padding: 3rem;
            border-radius: 24px;
            box-shadow: 0 20px 50px rgba(75, 34, 221, 0.1); /* Soft purple shadow */
        }
        
        /* Input Fields - Rounded & Clean */
        .stTextInput > div > div > input {
            border-radius: 50px; /* Pillow shape like reference */
            border: 1px solid #E2E8F0;
            padding: 10px 20px;
            background-color: #FAFAFA;
            color: #333;
        }
        .stTextInput > div > div > input:focus {
            border-color: #6CC04A; /* Green focus */
            box-shadow: 0 0 0 2px rgba(108, 192, 74, 0.2);
        }

        /* Main Button (Green "Create Account" style) */
        div[data-testid="stButton"] > button {
            width: 100%;
            background-color: #6CC04A;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 0.75rem 1rem;
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 5px 15px rgba(108, 192, 74, 0.3);
            transition: all 0.3s ease;
        }
        div[data-testid="stButton"] > button:hover {
            background-color: #5ab03e;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(108, 192, 74, 0.4);
            color: white;
        }

        /* Toggle Button (Link Style) */
        button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #4B22DD !important; /* Brand Purple */
            text-decoration: underline;
            padding: 0 !important;
            font-weight: 600;
        }
        button[kind="secondary"]:hover {
            color: #3617a6 !important;
            text-decoration: none;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #1e293b;
            text-align: center;
        }
        p {
             text-align: center;
        }

        /* Hide Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # State for Toggle (Login vs Signup)
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'signup' # Default to match reference (Create Account)

    # Layout: Image (Left) | Login Card (Right)
    col_bg, col_login = st.columns([1.5, 1])

    with col_bg:
        # Placeholder for future Background Image
        # User said: "En cuanto a la imagen del fondo no genere ninguna... te la voy a dar al final"
        st.empty() 

    with col_login:
        # LOGO
        # Assuming we have the logo in assets, otherwise text
        if os.path.exists("assets/logo.png"):
             st.image("assets/logo.png", width=150) # You can adjust this later
        else:
             st.markdown("<h3 style='color:#4B22DD; text-align:center;'>e-education</h3>", unsafe_allow_html=True)

        if st.session_state['auth_mode'] == 'signup':
            st.markdown("<h2>Create account</h2>", unsafe_allow_html=True)
            
            new_email = st.text_input("Email address", key="reg_email", placeholder="name@example.com")
            
            # Custom Eye Icon Logic is hard in native Streamlit, standard password input adds it automatically now
            new_pass = st.text_input("Password", type="password", key="reg_pass", placeholder="********")
            
            st.write("") # Spacer
            if st.button("Create account", key="btn_reg"):
                if new_email and new_pass:
                    from database import sign_up
                    user = sign_up(new_email, new_pass)
                    if user:
                        st.success("Cuenta creada. Iniciando sesión...")
                        time.sleep(1.5)
                        st.session_state['auth_mode'] = 'login' # Switch to login or auto-login?
                        st.rerun()
                    else:
                        st.error("Error al crear cuenta.")
                else:
                    st.warning("Por favor completa los campos.")

            # Toggle Link
            st.markdown("___")
            c_link_1, c_link_2 = st.columns([1.5, 1])
            with c_link_1: st.write("Already have an account?")
            with c_link_2: 
                if st.button("Log in", type="secondary", key="goto_login"):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()

        else: # LOGIN MODE
            st.markdown("<h2>Welcome Back</h2>", unsafe_allow_html=True)
            
            email = st.text_input("Email address", key="login_email", placeholder="name@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="********")
            
            st.write("") # Spacer
            if st.button("Log in", key="btn_login"):
                if email and password:
                    from database import sign_in
                    user = sign_in(email, password)
                    if user:
                        st.session_state['user'] = user
                        if 'supabase_session' in st.session_state:
                             sess = st.session_state['supabase_session']
                             cookie_manager.set("supabase_refresh_token", sess.refresh_token, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas.")
                else:
                    st.warning("Por favor ingresa tus datos.")

            # Toggle Link
            st.markdown("___")
            c_link_1, c_link_2 = st.columns([1.5, 1])
            with c_link_1: st.write("New here?")
            with c_link_2: 
                if st.button("Create account", type="secondary", key="goto_signup"):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()

    st.stop()
"""

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Locate the login block (lines 66-107 roughly)
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "if not st.session_state['user']:" in line:
        start_idx = i
    if "st.stop() # Stop execution here if not logged in" in line:
        end_idx = i + 1 # Include this line
        break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Login Block at lines {start_idx+1}-{end_idx}")
    
    # Remove old block and insert new one
    # Note: We need to ensure indentation of the new block matches (0 indentation for the `if` statement)
    
    # The new_login_code string already has the 'if' at the start.
    # We just need to make sure we don't mess up the rest of the file.
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(new_login_code + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Redesigned.")
else:
    print("ERROR: Login block not found.")
