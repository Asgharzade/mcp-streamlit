import streamlit as st
from datetime import datetime
import io
from app.utils.logging import StreamlitLogHandler

def setup_sidebar(streamlit_handler: StreamlitLogHandler, show_logs: bool = True, show_debug: bool = False):
    """Set up the sidebar with configuration options"""
    with st.sidebar:
        st.header("Configuration")
        
        # Display API key status
        serper_api_key = st.session_state.get("serper_api_key_loaded", False)
        openai_api_key = st.session_state.get("openai_api_key_loaded", False)
        
        if serper_api_key:
            st.success("✅ Serper API Key loaded from environment")
        else:
            st.error("❌ SERPER_API_KEY environment variable not found")
            st.info("Please set the SERPER_API_KEY environment variable")
        
        if openai_api_key:
            st.success("✅ OpenAI API Key loaded from environment")
        else:
            st.error("❌ OPENAI_API_KEY environment variable not found")
            st.info("Please set the OPENAI_API_KEY environment variable")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        # Debug toggle
        show_debug = st.checkbox("Show Debug Info", value=show_debug)
        
        # Log viewer toggle
        show_logs = st.checkbox("Show Logs", value=show_logs)
        
        # Admin link (only show for admin users)
        if st.session_state.get("username") == "admin":
            st.markdown("---")
            st.markdown("### Admin")
            st.markdown("[🔐 Admin Panel](/admin)", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This chatbot uses:
        - **OpenAI GPT-4.1-mini** for intelligent intent detection
        - **MCP (Model Context Protocol)** for tool integration
        - **Serper API** for web search
        - **Streamlit** for the frontend
        
        The AI intelligently determines when to search vs. when to chat conversationally.
        
        Try asking:
        - "What's the weather like today?"
        - "Hello, how are you?"
        - "Tell me about quantum computing"
        - "What's 2+2?"
        - "Latest news about AI"
        """)
        
        # Display logs if enabled
        if show_logs and streamlit_handler:
            st.markdown("---")
            st.markdown("### Logs")
            
            # Add download logs button
            if streamlit_handler.logs:
                log_text = "\n".join([f"{log['timestamp']} - {log['level']}: {log['message']}" for log in streamlit_handler.logs])
                log_bytes = log_text.encode()
                st.download_button(
                    label="Download Logs",
                    data=log_bytes,
                    file_name=f"mcp_chatbot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            log_container = st.container()
            with log_container:
                for log in streamlit_handler.logs:
                    level = log['level']
                    if level == 'ERROR':
                        st.error(f"{log['timestamp']} - {log['message']}")
                    elif level == 'WARNING':
                        st.warning(f"{log['timestamp']} - {log['message']}")
                    elif level == 'INFO':
                        st.info(f"{log['timestamp']} - {log['message']}")
                    else:
                        st.text(f"{log['timestamp']} - {level}: {log['message']}")
    
    return show_debug, show_logs

def display_chat_messages():
    """Display chat messages from session state"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def display_debug_info():
    """Display debug information in the sidebar"""
    if "last_intent" in st.session_state:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Debug Info")
            intent = st.session_state.last_intent
            st.json(intent) 