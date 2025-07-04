import json
import logging
import os
from typing import Dict, Any, List
import openai
from app.core.mcp_server import MCPServer

logger = logging.getLogger("mcp-chatbot")

class MCPChatbot:
    def __init__(self, mcp_server: MCPServer):
        self.mcp_server = mcp_server
        self.conversation_history = []
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def _detect_search_intent_with_openai(self, message: str) -> Dict[str, Any]:
        """Use OpenAI to detect if the message requires a search and extract the query"""
        logger.info(f"Detecting intent for message: '{message[:50]}...' if len(message) > 50 else message")
        
        system_prompt = """
        You are an intent detection system for a chatbot that can search the web.

        Analyze the user's message and determine:
        1. Whether they need current information, facts, or data that would require a web search
        2. What the optimal search query should be

        Return a JSON response with:
        - "needs_search": boolean (true if web search is needed)
        - "search_query": string (the optimized search query, or null if no search needed)
        - "reasoning": string (brief explanation of your decision)

        Examples:
        - "What time/date is it?" → needs_search: true, search_query: "current datetime"
        - "What's the weather like?" → needs_search: true, search_query: "current weather"
        - "Hello, how are you?" → needs_search: false, search_query: null
        - "Tell me about quantum computing" → needs_search: true, search_query: "quantum computing latest developments"
        - "What's 2+2?" → needs_search: false, search_query: null
        - "Latest news about AI" → needs_search: true, search_query: "latest AI news 2024"
        - "How to make coffee" → needs_search: true, search_query: "how to make coffee step by step"

        Focus on detecting when users need current, factual, or specific information that would benefit from a web search.
        """

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
        if hasattr(st := __import__('streamlit', fromlist=['session_state']), 'session_state'):
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
            system_prompt = """
                You are a helpful chatbot that can search the web for information. 
                When users ask questions that don't require current information, provide friendly, helpful responses.
                Keep responses concise and engaging. If appropriate, suggest they can ask you to search for specific information.
                """

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
                temperature=0.3,
                max_tokens=400
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
            for i, result in enumerate(search_data["organic"][:5], 1):
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
            
            system_prompt = """
            You are a helpful AI assistant that summarizes search results.
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