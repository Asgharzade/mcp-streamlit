import logging
from datetime import datetime

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

def setup_logging():
    """Configure logging for the application"""
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
    
    return logger, streamlit_handler 