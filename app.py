import streamlit as st
import asyncio
import os
import logging
from datetime import datetime
import io

# Import our modules
from app.utils.logging import setup_logging
from app.utils.env import load_environment_variables
from app.utils.streamlit_ui import setup_sidebar, display_chat_messages, display_debug_info
from app.core.mcp_server import MCPServer
from app.tools.serper_search import SerperSearchTool
from app.services.chatbot import MCPChatbot

# Streamlit App
def main():
    st.set_page_config(page_title="MCP Chatbot", page_icon="🤖", layout="wide")
    
    st.title("🤖 MCP Chatbot with OpenAI Intent Detection")
    st.markdown("A smart chatbot using Model Context Protocol (MCP) with OpenAI-powered intent detection and Serper API for web search")
    
    # Set up logging
    logger, streamlit_handler = setup_logging()
    
    # Load environment variables
    env_loaded, env_message = load_environment_variables()
    if not env_loaded:
        logger.error(env_message)
        st.error(f"❌ {env_message}")
    
    # Get API keys from environment variables
    serper_api_key = os.getenv("SERPER_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Store API key status in session state for UI
    st.session_state.serper_api_key_loaded = bool(serper_api_key)
    st.session_state.openai_api_key_loaded = bool(openai_api_key)
    
    # Sidebar for configuration
    show_debug, show_logs = setup_sidebar(streamlit_handler)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "mcp_server" not in st.session_state:
        st.session_state.mcp_server = None
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    
    # Initialize MCP server and chatbot if API keys are provided
    if serper_api_key and openai_api_key and st.session_state.mcp_server is None:
        try:
            # Initialize MCP server
            mcp_server = MCPServer()
            
            # Register Serper search tool
            search_tool = SerperSearchTool(serper_api_key)
            mcp_server.register_tool("search", search_tool)
            
            # Initialize chatbot
            chatbot = MCPChatbot(mcp_server)
            
            st.session_state.mcp_server = mcp_server
            st.session_state.chatbot = chatbot
            
            logger.info("MCP Server initialized with OpenAI intent detection and Serper search tool")
            st.success("✅ MCP Server initialized with OpenAI intent detection and Serper search tool!")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {str(e)}")
            st.error(f"❌ Failed to initialize MCP server: {str(e)}")
    elif not serper_api_key or not openai_api_key:
        logger.warning("Missing API keys: SERPER_API_KEY or OPENAI_API_KEY")
        st.warning("⚠️ Please set both SERPER_API_KEY and OPENAI_API_KEY environment variables to use the chatbot.")
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask me anything or request a search..."):
        if not serper_api_key or not openai_api_key:
            logger.error("API keys missing, cannot process message")
            st.error("Please set both SERPER_API_KEY and OPENAI_API_KEY environment variables first!")
            return
        
        if st.session_state.chatbot is None:
            logger.error("Chatbot not initialized")
            st.error("Chatbot not initialized. Please check your environment variables.")
            return
        
        # Add user message to chat history
        logger.info(f"User input: {prompt}")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate bot response
        with st.chat_message("assistant"):
            with st.spinner("..."):
                try:
                    # Process message asynchronously
                    logger.info("Processing message asynchronously")
                    response = asyncio.run(
                        st.session_state.chatbot.process_message(prompt)
                    )
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    logger.info("Response added to chat history")
                    
                    # Show debug info in sidebar if enabled
                    if show_debug:
                        display_debug_info()
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    logger.error(f"Error processing message: {str(e)}")
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()