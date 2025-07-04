import streamlit as st
import asyncio
import json
from typing import List, Dict, Any
import httpx
import os
import logging
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import openai
import io

# Custom log handler for Streamlit
class StreamlitLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
        
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': record.getMessage()
        })
        # Keep only the last 100 logs
        if len(self.logs) > 100:
            self.logs.pop(0)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp-chatbot")

# Add Streamlit log handler
streamlit_handler = StreamlitLogHandler()
streamlit_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(streamlit_handler)

# Load environment variables from .env file
load_dotenv()


# MCP Tool Interface
class MCPTool(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass

# Serper Search Tool
class SerperSearchTool(MCPTool):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
    
    async def execute(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Execute a search using Serper API"""
        logger.info(f"Executing search with query: '{query}', num_results: {num_results}")
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            logger.info("Sending request to Serper API")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                logger.info(f"Serper API response received, status code: {response.status_code}")
                return response.json()
        except Exception as e:
            logger.error(f"Serper API search failed: {str(e)}")
            return {"error": f"Search failed: {str(e)}"}
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": "search",
            "description": "Search the web using Serper API",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

# MCP Server
class MCPServer:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, name: str, tool: MCPTool):
        self.tools[name] = tool
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "schema": tool.get_schema()
            }
            for name, tool in self.tools.items()
        ]
    
    async def call_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        if name not in self.tools:
            logger.error(f"Tool '{name}' not found")
            return {"error": f"Tool '{name}' not found"}
        
        try:
            logger.info(f"Calling tool '{name}' with args: {kwargs}")
            result = await self.tools[name].execute(**kwargs)
            logger.info(f"Tool '{name}' executed successfully")
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {str(e)}")
            return {"error": f"Tool execution failed: {str(e)}"}

# Chatbot with MCP Integration
class MCPChatbot:
    def __init__(self, mcp_server: MCPServer):
        self.mcp_server = mcp_server
        self.conversation_history = []
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def _detect_search_intent_with_openai(self, message: str) -> Dict[str, Any]:
        """Use OpenAI to detect if the message requires a search and extract the query"""
        logger.info(f"Detecting intent for message: '{message[:50]}...' if len(message) > 50 else message")
        
        system_prompt = """You are an intent detection system for a chatbot that can search the web.

Analyze the user's message and determine:
1. Whether they need current information, facts, or data that would require a web search
2. What the optimal search query should be

Return a JSON response with:
- "needs_search": boolean (true if web search is needed)
- "search_query": string (the optimized search query, or null if no search needed)
- "reasoning": string (brief explanation of your decision)

Examples:
- "What's the weather like?" → needs_search: true, search_query: "current weather"
- "Hello, how are you?" → needs_search: false, search_query: null
- "Tell me about quantum computing" → needs_search: true, search_query: "quantum computing latest developments"
- "What's 2+2?" → needs_search: false, search_query: null
- "Latest news about AI" → needs_search: true, search_query: "latest AI news 2024"
- "How to make coffee" → needs_search: true, search_query: "how to make coffee step by step"

Focus on detecting when users need current, factual, or specific information that would benefit from a web search."""

        try:
            logger.info("Calling OpenAI API for intent detection")
            
            # Create messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (excluding the current message which will be added separately)
            for msg in self.conversation_history[:-1]:  # Exclude the last message which is the current user message
                messages.append(msg)
                
            # Add the current user message
            messages.append({"role": "user", "content": message})
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                temperature=0.0,
                max_tokens=500
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {content}")
            try:
                # Try to parse as JSON
                result = json.loads(content)
                logger.info(f"Intent detected: needs_search={result.get('needs_search', False)}, query='{result.get('search_query')}'")
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning(f"Failed to parse OpenAI response as JSON: {content}")
                return {
                    "needs_search": False,
                    "search_query": None,
                    "reasoning": "Failed to parse OpenAI response as JSON"
                }
                
        except Exception as e:
            # Return a default response if OpenAI API fails
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "needs_search": False,
                "search_query": None,
                "reasoning": f"OpenAI API error: {str(e)}"
            }
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response"""
        logger.info(f"Processing user message: '{message[:50]}...' if len(message) > 50 else message")
        self.conversation_history.append({"role": "user", "content": message})
        
        # Use OpenAI to detect intent and extract search query
        intent_result = await self._detect_search_intent_with_openai(message)
        
        # Store intent result for debugging
        if hasattr(st, 'session_state'):
            st.session_state.last_intent = intent_result
        
        if intent_result.get("needs_search", False):
            search_query = intent_result.get("search_query", message)
            logger.info(f"Executing search with query: '{search_query}'")
            
            # Call search tool
            result = await self.mcp_server.call_tool("search", query=search_query)
            
            if result.get("success"):
                search_data = result["result"]
                logger.info("Search successful, formatting response")
                
                # Format raw search results
                raw_response = self._format_search_response(search_data)
                
                # Get AI summary of search results
                summary = await self._summarize_search_results(search_data, message)
                
                # Combine summary with raw results
                response = f"{summary}\n\n**Raw Search Results:**\n\n{raw_response}"
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"Search failed: {error}")
                response = f"Sorry, I couldn't search for that. Error: {error}"
        else:
            # Generate conversational response using OpenAI
            logger.info("Generating conversational response with OpenAI")
            response = await self._generate_openai_response(message)
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    async def _generate_openai_response(self, message: str) -> str:
        """Generate a conversational response using OpenAI"""
        try:
            logger.info("Generating response with OpenAI")
            system_prompt = """You are a helpful chatbot that can search the web for information. 
When users ask questions that don't require current information, provide friendly, helpful responses.
Keep responses concise and engaging. If appropriate, suggest they can ask you to search for specific information."""

            # Create messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (excluding the current message which will be added separately)
            for msg in self.conversation_history[:-1]:  # Exclude the last message which is the current user message
                messages.append(msg)
                
            # Add the current user message
            messages.append({"role": "user", "content": message})
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {str(e)}")
            return f"I'm having trouble connecting to my AI services. Please try again in a moment. Error: {str(e)}"
    
    def _format_search_response(self, search_data: Dict[str, Any]) -> str:
        """Format search results into a readable response"""
        if "error" in search_data:
            return f"Search error: {search_data['error']}"
        
        response = "Here's what I found:\n\n"
        
        if "organic" in search_data:
            for i, result in enumerate(search_data["organic"][:3], 1):
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No description")
                link = result.get("link", "")
                
                response += f"**{i}. {title}**\n"
                response += f"{snippet}\n"
                response += f"🔗 {link}\n\n"
        
        if "knowledgeGraph" in search_data:
            kg = search_data["knowledgeGraph"]
            if "description" in kg:
                response += f"**Quick Answer:** {kg['description']}\n\n"
        
        return response
    
    async def _summarize_search_results(self, search_data: Dict[str, Any], user_query: str) -> str:
        """Summarize search results using OpenAI"""
        try:
            logger.info("Summarizing search results with OpenAI")
            
            # Create a simplified version of search results for the prompt
            simplified_results = []
            
            if "organic" in search_data:
                for i, result in enumerate(search_data["organic"][:5], 1):
                    title = result.get("title", "No title")
                    snippet = result.get("snippet", "No description")
                    link = result.get("link", "")
                    
                    simplified_results.append({
                        "title": title,
                        "snippet": snippet,
                        "link": link
                    })
            
            if "knowledgeGraph" in search_data:
                kg = search_data["knowledgeGraph"]
                if "description" in kg:
                    simplified_results.append({
                        "title": kg.get("title", "Knowledge Graph"),
                        "snippet": kg["description"],
                        "link": kg.get("link", "")
                    })
            
            system_prompt = """You are a helpful AI assistant that summarizes search results.
Given a user query and search results, provide a concise, informative summary that directly answers the user's question.
Focus on extracting the most relevant information from the search results.
Your summary should be 2-3 paragraphs at most, highlighting the key points and insights.
"""

            search_results_text = json.dumps(simplified_results, indent=2)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {user_query}\n\nSearch Results: {search_results_text}\n\nPlease provide a concise summary of these search results that answers my query."}
            ]
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Search results summarized successfully")
            return f"**AI Summary:**\n\n{summary}"
            
        except Exception as e:
            logger.error(f"Error summarizing search results: {str(e)}")
            return "I found some search results but couldn't generate a summary. Please see the raw results below."

# Streamlit App
def main():
    st.set_page_config(page_title="MCP Chatbot", page_icon="🤖", layout="wide")
    
    st.title("🤖 MCP Chatbot with OpenAI Intent Detection")
    st.markdown("A smart chatbot using Model Context Protocol (MCP) with OpenAI-powered intent detection and Serper API for web search")
    
    # Get API keys from environment variables
    serper_api_key = os.getenv("SERPER_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Display API key status
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
        show_debug = st.checkbox("Show Debug Info", value=False)
        
        # Log viewer toggle
        show_logs = st.checkbox("Show Logs", value=True)
        
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
        if show_logs and "streamlit_handler" in globals():
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
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
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
                    if show_debug and "last_intent" in st.session_state:
                        with st.sidebar:
                            st.markdown("---")
                            st.markdown("### Debug Info")
                            intent = st.session_state.last_intent
                            st.json(intent)
                            logger.debug(f"Debug info displayed: {intent}")
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    logger.error(f"Error processing message: {str(e)}")
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()