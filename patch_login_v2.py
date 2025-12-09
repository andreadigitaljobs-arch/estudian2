
import os

app_path = 'app.py'

# 1. Improved Login CSS and Logic
# Includes Spanish translation, correct Logo, and fixes for Button Styling.
refined_login_code = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    
    # --- CUSTOM CSS FOR LOGIN PAGE ---
    st.markdown('''
        <style>
        /* RESET & BACKGROUND */
        .stApp {
            background-color: #F3F0FF;
            background-image: linear-gradient(135deg, #F3F0FF 0%, #E8FFF0 100%);
        }
        
        /* CARD STYLE targeting the 2nd column */
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div {
            background-color: white;
            padding: 3rem;
            border-radius: 24px;
            box-shadow: 0 20px 50px rgba(75, 34, 221, 0.1);
        }
        
        /* INPUTS - Rounded Pill Shape */
        .stTextInput > div > div > input {
            border-radius: 50px; 
            border: 1px solid #E2E8F0;
            padding: 10px 20px;
            background-color: #FAFAFA;
            color: #333;
        }
        .stTextInput > div > div > input:focus {
            border-color: #6CC04A;
            box-shadow: 0 0 0 2px rgba(108, 192, 74, 0.2);
        }

        /* PRIMARY BUTTON (Action) */
        /* Targets st.button with type="primary" */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #6CC04A !important;
            color: white !important;
            border: none;
            border-radius: 50px;
            padding: 0.6rem 1rem;
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 5px 15px rgba(108, 192, 74, 0.3);
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #5ab03e !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(108, 192, 74, 0.4);
        }

        /* SECONDARY BUTTON (Toggle Link) */
        /* Targets st.button with type="secondary" */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            color: #4B22DD !important;
            font-weight: 600;
            font-size: 0.9rem;
            padding: 0 !important;
            margin-top: 5px;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            text-decoration: underline;
            color: #3617a6 !important;
            border-color: transparent !important;
        }
        
        /* HEADERS */
        h2 {
            font-family: 'Inter', sans-serif;
            color: #1e293b;
            text-align: center;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        p { text-align: center; color: #64748b; }

        /* HIDE DEFAULT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # State for Toggle
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login' # Default to Login for better UX

    # Layout: Image (Left) | Login Card (Right)
    col_bg, col_login = st.columns([1.5, 1])

    with col_bg:
        st.empty() 

    with col_login:
        # LOGO
        if os.path.exists("assets/logo_main.png"):
             st.image("assets/logo_main.png", width=180) 
        else:
             st.markdown("<h3 style='color:#4B22DD; text-align:center;'>e-education</h3>", unsafe_allow_html=True)

        st.write("") # Spacer

        if st.session_state['auth_mode'] == 'signup':
            st.markdown("<h2>Crear Cuenta</h2>", unsafe_allow_html=True)
            st.markdown("<p>Únete a la plataforma de aprendizaje.</p>", unsafe_allow_html=True)
            
            new_email = st.text_input("Correo electrónico", key="reg_email", placeholder="nombre@ejemplo.com")
            new_pass = st.text_input("Contraseña", type="password", key="reg_pass", placeholder="********")
            
            st.write("") 
            # PRIMARY BUTTON
            if st.button("Registrarse", type="primary", key="btn_reg"):
                if new_email and new_pass:
                    from database import sign_up
                    user = sign_up(new_email, new_pass)
                    if user:
                        st.success("¡Cuenta creada! Ingresando...")
                        time.sleep(1.5)
                        st.session_state['auth_mode'] = 'login'
                        st.rerun()
                    else:
                        st.error("Error al crear cuenta.")
                else:
                    st.warning("Completa todos los campos.")

            st.markdown("___")
            c_link_1, c_link_2 = st.columns([1.2, 0.8])
            with c_link_1: 
                st.markdown("<div style='text-align:right; font-size:0.9rem; padding-top:5px;'>¿Ya tienes cuenta?</div>", unsafe_allow_html=True)
            with c_link_2: 
                # SECONDARY BUTTON
                if st.button("Inicia Sesión", type="secondary", key="goto_login"):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()

        else: # LOGIN MODE
            st.markdown("<h2>¡Hola de nuevo!</h2>", unsafe_allow_html=True)
            st.markdown("<p>Ingresa tus credenciales para continuar.</p>", unsafe_allow_html=True)
            
            email = st.text_input("Correo electrónico", key="login_email", placeholder="nombre@ejemplo.com")
            password = st.text_input("Contraseña", type="password", key="login_pass", placeholder="********")
            
            st.write("") 
            # PRIMARY BUTTON
            if st.button("Entrar", type="primary", key="btn_login"):
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
                    st.warning("Ingresa tu correo y contraseña.")

            st.markdown("___")
            c_link_1, c_link_2 = st.columns([1.2, 0.8])
            with c_link_1: 
                st.markdown("<div style='text-align:right; font-size:0.9rem; padding-top:5px;'>¿Eres nuevo?</div>", unsafe_allow_html=True)
            with c_link_2: 
                # SECONDARY BUTTON
                if st.button("Crea una cuenta", type="secondary", key="goto_signup"):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()

    st.stop()
"""

with open(app_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Locate the login block (lines 66-150 roughly)
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    # We look for the start of the login block
    if "if not st.session_state['user']" in line and "force_logout" in line: # Logic from previous patch
        start_idx = i
    if "if not st.session_state['user']:" in line: # Logic if previous patch failed or slightly different
        start_idx = i
        
    if "st.stop() # Stop execution here" in line:
        end_idx = i + 1
        break
    if "st.stop()" in line and i > start_idx + 10: # Generic stop at end of login block
        end_idx = i + 1
        break

if start_idx != -1 and end_idx != -1:
    print(f"Replacing Login Block v2 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined.")
else:
    print("ERROR: Login block not found for replacement.")
    # Debug
    # for i, line in enumerate(lines):
    #    if "st.stop()" in line: print(f"Stop found at {i}")
