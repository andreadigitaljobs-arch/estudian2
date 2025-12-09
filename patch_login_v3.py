
import os

app_path = 'app.py'

# 1. Login V3: Purple Theme, Form Left, Image Right
refined_login_code_v3 = """
# If not logged in, show Login Screen and STOP
if not st.session_state['user'] and not st.session_state.get('force_logout'):
    
    # --- CUSTOM CSS FOR LOGIN PAGE V3 ---
    st.markdown('''
        <style>
        /* RESET & BACKGROUND */
        .stApp {
            background-color: white; /* Clean white background like reference */
        }
        
        /* CARD CONTAINER (Vertical Center optimization) */
        div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stHorizontalBlock"]) {
            align-items: center;
        }

        /* INPUTS - Rounded Rect (12px) */
        .stTextInput > div > div > input {
            border-radius: 12px; 
            border: 1px solid #E2E8F0;
            padding: 12px 15px;
            background-color: #FAFAFA;
            color: #333;
            font-size: 1rem;
        }
        .stTextInput > div > div > input:focus {
            border-color: #4B22DD; /* Purple focus */
            box-shadow: 0 0 0 2px rgba(75, 34, 221, 0.1);
        }

        /* PRIMARY BUTTON (Purple) */
        /* Targets st.button with type="primary" */
        div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            background-color: #4B22DD !important; /* Brand Purple */
            color: white !important;
            border: none;
            border-radius: 12px; /* Matching inputs */
            padding: 0.75rem 1rem;
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 5px 15px rgba(75, 34, 221, 0.2);
            transition: all 0.2s ease;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #3819a6 !important;
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(75, 34, 221, 0.3);
        }

        /* SECONDARY BUTTON (Link Style) */
        div[data-testid="stButton"] > button[kind="secondary"] {
            background: transparent !important;
            border: none !important;
            color: #1E293B !important; /* Darker text */
            font-weight: 600;
        }
        div[data-testid="stButton"] > button[kind="secondary"]:hover {
            color: #4B22DD !important;
            text-decoration: none;
        }
        
        /* HEADERS */
        h2 {
            font-family: 'Inter', sans-serif;
            color: #0f172a;
            font-weight: 800;
            margin-bottom: 0.5rem;
            font-size: 1.8rem;
        }
        p { color: #64748b; font-size: 1rem;}

        /* HIDE DEFAULT ELEMENTS */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    ''', unsafe_allow_html=True)

    # State for Toggle
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    # Layout: Form (Left) | Image (Right)
    # Using columns with a gap
    c_spacer_l, c_form, c_img, c_spacer_r = st.columns([0.5, 4, 5, 0.5], gap="large")

    with c_form:
        st.write("") # Top spacing
        st.write("") 
        
        # LOGO (Centered or Left? Reference is Left-ish but contained)
        if os.path.exists("assets/logo_main.png"):
             st.image("assets/logo_main.png", width=200) 
        else:
             st.markdown("<h3 style='color:#4B22DD;'>e-education</h3>", unsafe_allow_html=True)

        st.write("") 

        if st.session_state['auth_mode'] == 'signup':
            st.markdown("<h2>Crear cuenta</h2>", unsafe_allow_html=True)
            # st.markdown("<p>Empieza tu aprendizaje hoy.</p>", unsafe_allow_html=True)
            
            new_email = st.text_input("Email", key="reg_email", placeholder="nombre@ejemplo.com", label_visibility="hidden")
            new_pass = st.text_input("Contraseña", type="password", key="reg_pass", placeholder="Contraseña", label_visibility="hidden")
            
            st.write("") 
            if st.button("Registrarse", type="primary", key="btn_reg"):
                if new_email and new_pass:
                    from database import sign_up
                    user = sign_up(new_email, new_pass)
                    if user:
                        st.success("Cuenta creada. Redirigiendo...")
                        time.sleep(1.5)
                        st.session_state['auth_mode'] = 'login'
                        st.rerun()
                    else:
                        st.error("Error al crear cuenta.")
                else:
                    st.warning("Completa los campos.")

            st.write("")
            st.write("")
            
            c_txt, c_btn = st.columns([1.5, 1])
            with c_txt: 
                 st.markdown("<div style='padding-top:7px; color:#64748b;'>¿Ya tienes cuenta?</div>", unsafe_allow_html=True)
            with c_btn:
                 if st.button("Inicia Sesión", type="secondary", key="goto_login"):
                    st.session_state['auth_mode'] = 'login'
                    st.rerun()

        else: # LOGIN MODE
            st.markdown("<h2>Log in to your account</h2>", unsafe_allow_html=True)
            # Using English header per reference? User said "hazlo igual". 
            # But earlier asked for Spanish. I will use Spanish but MATCH THE FONT WEIGHT "Inicia sesión en tu cuenta".
            
            email = st.text_input("Email", key="login_email", placeholder="Email", label_visibility="hidden")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Password", label_visibility="hidden")
            
            st.write("") 
            if st.button("Log in", type="primary", key="btn_login"):
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
                    st.warning("Ingresa tus datos.")

            # Forgot Password Mockup
            st.markdown("<div style='text-align:center; margin-top:10px; margin-bottom:20px;'><a href='#' style='color:#4B22DD; text-decoration:none; font-weight:600; font-size:0.9rem;'>Forgot password?</a></div>", unsafe_allow_html=True)

            st.markdown("___")
            
            # Bottom Toggle
            c_txt, c_btn = st.columns([1.5, 1])
            with c_txt: 
                 st.markdown("<div style='padding-top:7px; color:#64748b; text-align:right;'>Don't have an account?</div>", unsafe_allow_html=True)
            with c_btn:
                 if st.button("Sign up", type="secondary", key="goto_signup"):
                    st.session_state['auth_mode'] = 'signup'
                    st.rerun()

    with c_img:
        # Placeholder for 3D Image
        # To make it look like the reference, I'll try to use a placeholder colored box or the logo again if no image provided yet
        # User said "te la voy a dar al final". So I leave it empty or put a gray placeholder.
        st.markdown('''
            <div style="
                background: linear-gradient(135deg, #F3F0FF 0%, #E0D4FC 100%); 
                border-radius: 24px; 
                height: 500px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                color: #4B22DD;
                font-weight: bold;
                opacity: 0.5;
            ">
                (Imagen 3D aquí)
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
    print(f"Replacing Login V3 at lines {start_idx+1}-{end_idx}")
    
    new_lines = []
    # Lines before
    new_lines.extend(lines[:start_idx])
    # New Code
    new_lines.append(refined_login_code_v3 + '\n')
    # Lines after
    new_lines.extend(lines[end_idx:])
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print("SUCCESS: Login Page Refined V3.")
else:
    print("ERROR: Login block not found.")
