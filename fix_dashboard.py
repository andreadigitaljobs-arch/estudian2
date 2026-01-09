
import os

file_path = r"c:\Users\nombr\.gemini\antigravity\playground\hidden-glenn\app.py"

# Clean content for the dashboard section
new_dashboard_content = """        st.markdown(" <br> ", unsafe_allow_html=True)

        # --- MAIN CONTENT ROW ---
        d1, d2 = st.columns([0.5, 0.5])
        
        with d1:
            # --- SMART CONTINUITY CARD ---
            st.markdown("### 🕰️ Continuar donde lo dejaste", unsafe_allow_html=True)
            st.caption("Retoma tu última actividad")
            
            # Load Footprint
            curr_user = st.session_state['user']
            footprint = curr_user.user_metadata.get('smart_footprint') if curr_user.user_metadata else None
            
            # Helper to render the card
            def render_smart_card(icon, title, subtitle, btn_label, on_click_fn):
                 # Styled Container
                 with st.container(border=True):
                     c_icon, c_info, c_btn = st.columns([0.15, 0.6, 0.25])
                     with c_icon:
                         st.markdown(f"<div style='font-size: 30px; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
                     with c_info:
                         st.markdown(f"**{title}**")
                         st.caption(subtitle)
                     with c_btn:
                         st.write("") # Spacer
                         if st.button(btn_label, use_container_width=True, type="primary", key=f"smart_{title[:10]}"):
                             on_click_fn()
                             st.rerun()

            if footprint:
                 ftype = footprint.get('type')
                 ftitle = footprint.get('title', 'Actividad Reciente')
                 fsub = footprint.get('subtitle', 'Retomar actividad')
                 ftarget = footprint.get('target_id')
                 
                 if ftype == 'chat':
                     def go_chat():
                         # Re-fetch session data (mock object minimal)
                         st.session_state['current_chat_session'] = {'id': ftarget, 'name': ftitle}
                         st.session_state['tutor_chat_history'] = []
                         st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                         st.session_state['force_chat_tab'] = True
                         
                         # UPDATE URL
                         try:
                             if hasattr(st, 'query_params'):
                                 st.query_params['chat_id'] = str(ftarget)
                             else:
                                 st.experimental_set_query_params(chat_id=str(ftarget))
                         except: pass
                     
                     render_smart_card("💬", f"Chat: {ftitle}", "Estabas conversando con tu asistente", "Retomar", go_chat)
                     
                 elif ftype == 'unit':
                     def go_unit():
                         st.session_state['redirect_target_name'] = "Biblioteca"
                         st.session_state['force_chat_tab'] = True
                         st.session_state['lib_current_unit_id'] = ftarget
                         st.session_state['lib_current_unit_name'] = ftitle
                         st.session_state['lib_breadcrumbs'] = [{'id': ftarget, 'name': ftitle}]
                         
                     render_smart_card("📂", f"Carpeta: {ftitle}", "Estabas explorando archivos aquí", "Ir", go_unit)
                     
                 else:
                     # Fallback for unknown types
                     st.info(f"Última actividad: {ftitle}")
                     
            else:
                 # Fallback to Recents if no footprint (First run)
                 st.info("Explora la app para generar tu tarjeta de viaje. 🚀")
                 recent_chats = get_recent_chats(st.session_state['user'].id, limit=3)
                 if recent_chats:
                    chat = recent_chats[0]
                    if st.button(f"📝 Último chat: {chat['name']}", key="fallback_rec"):
                         st.session_state['current_chat_session'] = chat
                         st.session_state['tutor_chat_history'] = [] 
                         st.session_state['redirect_target_name'] = "Tutoría 1 a 1"
                         st.session_state['force_chat_tab'] = True
                         st.rerun()

        with d2:
            st.markdown("### 📄 Material Reciente", unsafe_allow_html=True)
            st.caption("Tus últimos archivos")
            
            recent_files = get_recent_files(current_c_id, limit=3)
            
            if recent_files:
                for f in recent_files:
                    with st.container(border=True):
                        col_icon, col_info, col_act = st.columns([0.15, 0.6, 0.25])
                        
                        ftype = f.get('type', 'unknown')
                        icon_emoji = "📄"
                        if ftype == 'transcript': icon_emoji = "📹"
                        elif ftype == 'note': icon_emoji = "📝"
                        elif ftype == 'pdf': icon_emoji = "📕"
                        
                        with col_icon:
                            st.markdown(f"<div style='font-size: 20px; text-align: center;'>{icon_emoji}</div>", unsafe_allow_html=True)
                            
                        with col_info:
                            display_name = f['name'][:30] + "..." if len(f['name']) > 30 else f['name']
                            st.markdown(f"**{display_name}**")
                            date_only = f['created_at'].split('T')[0] if f.get('created_at') else "Reciente"
                            st.caption(f"{date_only}")
                            
                        with col_act:
                            if st.button("▶", key=f"open_file_{f['id']}", use_container_width=True):
                                st.session_state['redirect_target_name'] = "Biblioteca"
                                st.session_state['force_chat_tab'] = True
                                st.rerun()
            else:
                st.info("Sin archivos aún", icon="📂")
            
            st.write("")
            st.markdown("### 🚀 Acciones", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("**Biblioteca**")
                if st.button("📂 Ver Todo", use_container_width=True, type="primary", key="btn_goto_lib"):
                    st.session_state['redirect_target_name'] = "Biblioteca"
                    st.session_state['force_chat_tab'] = True 
                    st.rerun()
            
            with st.container(border=True):
                st.markdown("**Subir**")
                if st.button("➕ Nuevo", use_container_width=True, key="btn_upload_new"):
                    st.session_state['redirect_target_name'] = "Biblioteca"
                    st.session_state['force_chat_tab'] = True
                    st.session_state['lib_auto_open_upload'] = True
                    st.rerun()
"""

# Try to read and fix
try:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # Find start and end indices
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if 'st.markdown(" <br> ", unsafe_allow_html=True)' in line:
            start_idx = i
        if start_idx != -1 and 'st.info("Selecciona o crea un Diplomado' in line:
            end_idx = i - 1 # Line before the else block which contains this info
            # Wait, the else: line itself is needed to define where we stop.
            # The else: is associated with the if current_c_id: block?
            # Let's find "    else:" that matches the outer block.
            pass

    # Better approach: find strictly the block we messed up.
    # We messed up from start_idx to the else block.
    # Let's find the 'else:' line that corresponds to 'elif current_c_id:'
    # It's hard to parse python indentation with simple search, but we know the content.
    
    if start_idx != -1:
        # Find the next 'else:' with 4 spaces indentation after start_idx
        for i in range(start_idx, len(lines)):
            if lines[i].strip() == "else:" and lines[i].startswith("    else:"):
                end_idx = i
                break
        
        if end_idx != -1:
            print(f"Found block: {start_idx} to {end_idx}")
            # Replace lines
            final_lines = lines[:start_idx] + [new_dashboard_content + "\n"] + lines[end_idx:]
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(final_lines)
            print("Successfully fixed app.py")
        else:
             print("Could not find end index (else: block)")
    else:
        print("Could not find start index")

except Exception as e:
    print(f"Error: {e}")
