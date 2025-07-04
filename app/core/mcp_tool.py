from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPTool(ABC):
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        pass 