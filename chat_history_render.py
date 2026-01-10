import streamlit as st
from db_handler import get_chat_sessions, get_chat_messages, delete_chat_session, rename_chat_session
import markdown

def render_chat_history(assistant):
    """
    Renders the Chat History section - displays all user's chat sessions and messages.
    V328: Initial Implementation
    """
    
    # CSS for Chat History UI
    st.markdown("""
    <style>
    /* Chat History Styles */
    .chat-list-item {
        background: white;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .chat-list-item:hover {
        background: #F5F5F5;
        border-color: #4B22DD;
    }
    .chat-list-item.selected {
        background: #EBF5FF;
        border-color: #4B22DD;
        border-left: 4px solid #4B22DD;
    }
    .chat-message {
        padding: 15px;
        margin: 10px 0;
        border-radius: 12px;
    }
    .chat-message.user {
        background: #EBF5FF;
        border-left: 4px solid #4B22DD;
    }
    .chat-message.assistant {
        background: #F5F5F5;
        border-left: 4px solid #6C757D;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_chat_id' not in st.session_state:
        st.session_state['selected_chat_id'] = None
    
    # Get user
    user = st.session_state.get('user')
    if not user:
        st.warning("⚠️ Debes iniciar sesión para ver el historial de chats")
        return
    
    # Fetch all chat sessions
    chat_sessions = get_chat_sessions(user.id)
    
    if not chat_sessions:
        st.info("📭 No tienes chats aún. Crea uno desde la Biblioteca Digital usando el botón '🤖 Analizar con IA'")
        return
    
    # Layout: Chat List (Left) | Messages (Right)
    col_list, col_messages = st.columns([0.3, 0.7])
    
    with col_list:
        st.markdown("### 💬 Tus Chats")
        st.caption(f"{len(chat_sessions)} conversaciones")
        
        # New Chat Button
        if st.button("➕ Nuevo Chat", use_container_width=True, type="primary"):
            from db_handler import create_chat_session
            new_session_id = create_chat_session(user.id, "Nuevo Chat")
            if new_session_id:
                st.session_state['selected_chat_id'] = new_session_id
                st.rerun()
        
        st.markdown("---")
        
        # Chat List
        for chat in chat_sessions:
            is_selected = st.session_state['selected_chat_id'] == chat['id']
            
            # Chat item button
            chat_name = chat.get('name', 'Sin título')
            created_at = chat.get('created_at', '')
            
            # Format date
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%d/%m/%Y %H:%M")
            except:
                date_str = "Fecha desconocida"
            
            # Create clickable chat item
            button_label = f"{chat_name}\n{date_str}"
            if st.button(button_label, key=f"chat_{chat['id']}", use_container_width=True, 
                        type="secondary" if not is_selected else "primary"):
                st.session_state['selected_chat_id'] = chat['id']
                st.rerun()
    
    with col_messages:
        selected_id = st.session_state['selected_chat_id']
        
        if not selected_id:
            st.info("👈 Selecciona un chat de la lista para ver la conversación")
            return
        
        # Get selected chat details
        selected_chat = next((c for c in chat_sessions if c['id'] == selected_id), None)
        if not selected_chat:
            st.error("❌ Chat no encontrado")
            return
        
        # Chat Header
        col_title, col_actions = st.columns([0.7, 0.3])
        with col_title:
            st.markdown(f"### {selected_chat.get('name', 'Sin título')}")
        
        with col_actions:
            # Delete button
            if st.button("🗑️ Eliminar", key="delete_chat"):
                if delete_chat_session(selected_id):
                    st.session_state['selected_chat_id'] = None
                    st.success("✅ Chat eliminado")
                    st.rerun()
                else:
                    st.error("❌ Error al eliminar")
        
        st.markdown("---")
        
        # Get messages
        messages = get_chat_messages(selected_id)
        
        if not messages:
            st.info("📭 Este chat no tiene mensajes aún")
        else:
            # Display messages
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                if role == 'user':
                    st.markdown(f"""
                    <div class="chat-message user">
                        <strong>👤 Tú:</strong><br>
                        {content[:500]}{'...' if len(content) > 500 else ''}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Render AI response as markdown
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <strong>🤖 Tutor IA:</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Render markdown content
                    st.markdown(content)
        
        # New message input (optional - for future enhancement)
        st.markdown("---")
        st.caption("💡 Tip: Puedes crear nuevos chats desde la Biblioteca Digital")
