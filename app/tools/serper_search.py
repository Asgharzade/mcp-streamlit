import httpx
import logging
from typing import Dict, Any
from app.core.mcp_tool import MCPTool

logger = logging.getLogger("mcp-chatbot")

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