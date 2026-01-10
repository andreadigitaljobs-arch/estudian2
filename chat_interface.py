import streamlit as st
import time
import markdown
from db_handler import (
    get_chat_sessions, create_chat_session, get_chat_messages, 
    save_chat_message, update_user_footprint, get_file_content
)

def render_chat_interface(assistant, get_global_context):
    """
    Renders the main Tutor Chat Interface.
    Args:
        assistant: Instance of StudyAssistant
        get_global_context: Function to retrieve global app context
    """
    
    # --- 1. SESSION MANAGEMENT ---
    if 'current_chat_session' not in st.session_state:
        st.session_state['current_chat_session'] = None

    current_sess = st.session_state.get('current_chat_session')
    user_id = st.session_state['user'].id

    # If no session active, show "Start New" screen
    if not current_sess:
        render_new_chat_screen(user_id)
        return

    # --- 2. LOAD & SYNC HISTORY ---
    # Sync with DB if needed (or first load)
    if 'tutor_chat_history' not in st.session_state:
        st.session_state['tutor_chat_history'] = []
        
    # Always refresh on initial render of a session to ensure consistency
    if st.session_state.get('loaded_sess_id') != current_sess['id']:
        st.session_state['tutor_chat_history'] = get_chat_messages(current_sess['id'])
        st.session_state['loaded_sess_id'] = current_sess['id']

    # --- 3. HEADER & CONTEXT INFO ---
    render_chat_header(current_sess)

    # --- 4. MESSAGE HISTORY (The "WhatsApp" look) ---
    render_message_history(st.session_state['tutor_chat_history'])

    # --- 5. INPUT AREA & LOGIC ---
    handle_input_and_response(current_sess, assistant, get_global_context)


def render_new_chat_screen(user_id):
    """Renders the initial screen to start a new chat."""
    st.markdown("### ¿En qué te ayudo hoy? 🎓")
    st.caption("Tu profesor particular con IA. Pregunta lo que quieras.")
    
    # Input for new chat creation
    init_prompt = st.chat_input("Escribe tu pregunta para empezar...", key="new_chat_init")
    
    if init_prompt:
        short_title = (init_prompt[:30] + "...") if len(init_prompt) > 30 else init_prompt
        new_id = create_chat_session(user_id, short_title)
        
        if new_id:
            # Re-fetch full object to be safe
            sessions = get_chat_sessions(user_id)
            new_sess = next((s for s in sessions if s['id'] == new_id), None)
            
            if new_sess:
                st.session_state['current_chat_session'] = new_sess
                st.session_state['tutor_chat_history'] = []
                
                # Save first message
                save_chat_message(new_id, "user", init_prompt)
                st.session_state['tutor_chat_history'].append({"role": "user", "content": init_prompt})
                
                # Update Footprint
                update_user_footprint(user_id, {
                    "type": "chat", "title": short_title, 
                    "target_id": new_id, "subtitle": "Nueva consulta"
                })
                
                # Trigger Response Next Run
                st.session_state['trigger_ai_response'] = True
                st.rerun()

def render_chat_header(current_sess):
    """Renders the chat header and active context files."""
    col_info, col_actions = st.columns([0.8, 0.2])
    with col_info:
        st.caption(f"📝 Clase Actual: **{current_sess['name']}**")
    
    # Active Files Display
    if st.session_state.get('active_context_files'):
        with st.expander(f"📎 Archivos en contexto ({len(st.session_state['active_context_files'])})", expanded=False):
            for idx, f in enumerate(st.session_state['active_context_files']):
                c1, c2 = st.columns([0.85, 0.15])
                c1.markdown(f"📄 `{f['name']}`")
                if c2.button("✖️", key=f"del_ctx_{idx}"):
                    st.session_state['active_context_files'].pop(idx)
                    st.rerun()

def render_message_history(history):
    """Renders the list of messages with styled bubbles."""
    chat_html = '<div style="display: flex; flex-direction: column; gap: 15px; padding-bottom: 20px;">'
    
    for msg in history:
        is_user = msg['role'] == 'user'
        
        # Styles
        row_style = "display: flex; width: 100%; margin-bottom: 2px;"
        row_style += " justify-content: flex-end;" if is_user else " justify-content: flex-start;"
        
        bubble_style = "padding: 10px 14px; border-radius: 12px; max-width: 85%; word-wrap: break-word; font-size: 16px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.1);"
        if is_user:
            bubble_style += " background-color: #d9fdd3; color: #111; border-bottom-right-radius: 2px; margin-right: 8px;"
        else:
            bubble_style += " background-color: #ffffff; color: #111; border-bottom-left-radius: 2px; border: 1px solid #f0f0f0; margin-left: 8px;"
            
        # Icon
        avatar = "👤" if is_user else "🎓"
        avatar_html = f'''
        <div style="width: 35px; height: 35px; min-width: 35px; border-radius: 50%; background-color: {'#eee' if is_user else '#e6f3ff'}; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 20px;">
            {avatar}
        </div>
        '''
        
        # Content Parsing
        raw = msg.get('content', '') or ''
        try:
            content_html = markdown.markdown(raw, extensions=['fenced_code', 'tables'])
        except:
            content_html = raw

        if is_user:
            chat_html += f'<div style="{row_style}"><div style="{bubble_style}">{content_html}</div>{avatar_html}</div>'
        else:
            chat_html += f'<div style="{row_style}">{avatar_html}<div style="{bubble_style}">{content_html}</div></div>'

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)
    # Anchor for auto-scroll logic (handled by global JS usually, but we keep the marker)
    st.markdown("<div id='end_marker' style='height: 1px;'></div>", unsafe_allow_html=True)


def handle_input_and_response(current_sess, assistant, get_global_context):
    """Handles user input and AI response generation."""
    
    # 1. CHECK PENDING RESPONSE FIRST
    if st.session_state.get('trigger_ai_response'):
        generate_ai_response(current_sess, assistant, get_global_context)
        return

    # 2. CHAT INPUT
    prompt = st.chat_input(f"Pregunta sobre {current_sess['name']}...", key="main_chat_input")
    
    if prompt:
        # Save User Message
        save_chat_message(current_sess['id'], "user", prompt)
        st.session_state['tutor_chat_history'].append({"role": "user", "content": prompt})
        
        # Trigger AI
        st.session_state['trigger_ai_response'] = True
        st.rerun()

def generate_ai_response(current_sess, assistant, get_global_context):
    """Generates the AI response using the assistant instance."""
    
    hist = st.session_state['tutor_chat_history']
    if not hist or hist[-1]['role'] != 'user':
        # Safety: Should only trigger if last msg was user
        st.session_state['trigger_ai_response'] = False
        return

    last_msg = hist[-1]['content']
    
    # Prepare Context
    gl_ctx, _ = get_global_context()
    context_files = st.session_state.get('active_context_files', [])
    
    # UI Placeholder for Streaming/Loading
    with st.chat_message("assistant"):
        with st.spinner("Analizando y pensando..."):
            try:
                # CALL AI ENGINE
                response_text = assistant.chat_tutor(
                    last_msg,
                    chat_history=hist[:-1],
                    context_files=context_files,
                    global_context=gl_ctx
                )
                
                # SAVE & UPDATE
                save_chat_message(current_sess['id'], "assistant", response_text)
                st.session_state['tutor_chat_history'].append({"role": "assistant", "content": response_text})
                
                # Reset Trigger
                st.session_state['trigger_ai_response'] = False
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generando respuesta: {e}")
                st.session_state['trigger_ai_response'] = False
