import logging
import sys
import os

def setup_logging(level=logging.INFO):
    os.makedirs("data", exist_ok=True)
    
    log_format = '[%(levelname)s] %(name)s: %(message)s'
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/execution.log", encoding="utf-8")
        ]
    )
    
    for lib_name in ["selenium", "urllib3", "requests", "undetected_chromedriver", "hpack", "httpcore", "google_genai.models", "httpx"]:
        logging.getLogger(lib_name).setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("AI-DE-S")
