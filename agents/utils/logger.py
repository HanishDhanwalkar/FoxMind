# agents/utils/logger.py
import logging
import os
from typing import Optional

def get_logger(name: str, 
               level: str = None, 
               log_file: str = None) -> logging.Logger:
    """Get configured logger instance."""
    
    # Get log level from environment or default
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Get log file from environment or default
    if log_file is None:
        log_file = os.getenv("LOG_FILE")
    
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger