import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import settings

def setup_logging():
    # Create a custom logger
    logger = logging.getLogger("project_nexus")
    logger.setLevel(logging.INFO)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler and set level to info
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler and set level to info
    file_handler = RotatingFileHandler("app.log", maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also redirect uvicorn and fastapi logs to our file
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        l = logging.getLogger(name)
        l.addHandler(file_handler)
        l.addHandler(console_handler)

    return logger

logger = setup_logging()
