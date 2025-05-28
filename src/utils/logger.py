# src/utils/logger.py
import logging
import sys
from config import config # Import config to get log level

def setup_logger(name='app_logger', level_str=None):
    """
    Configures and returns a logger.
    Uses log level from config if available, otherwise defaults to INFO.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers: # Avoid adding multiple handlers
        default_level_str = config['default'].LOG_LEVEL if hasattr(config['default'], 'LOG_LEVEL') else 'INFO'
        level_to_use_str = level_str or default_level_str
        
        try:
            level = getattr(logging, level_to_use_str.upper())
        except AttributeError:
            level = logging.INFO # Default to INFO if config level is invalid
            print(f"Warning: Invalid LOG_LEVEL '{level_to_use_str}'. Defaulting to INFO.")

        logger.setLevel(level)
        
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
        ch.setFormatter(formatter)
        
        logger.addHandler(ch)
        
    return logger

# Default application logger instance
app_logger = setup_logger() 