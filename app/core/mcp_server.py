import logging
from typing import List, Dict, Any
from app.core.mcp_tool import MCPTool

logger = logging.getLogger("mcp-chatbot")

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