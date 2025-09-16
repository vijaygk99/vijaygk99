"""
logging_utils.py - Logging utility functions for Selenium Recorder

This module provides utility functions for setting up and configuring logging.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, List, Dict, Any

def setup_logging(
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        console_level: Logging level for console output
        file_level: Logging level for file output
        log_format: Log message format
        
    Returns:
        Root logger
    """
    # Create default log file if not specified
    if not log_file:
        log_dir = os.path.join(os.path.expanduser("~"), ".selenium_recorder", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"selenium_recorder_{timestamp}.log")
        
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Set default log format if not specified
    if not log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all logs
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Create formatters
    formatter = logging.Formatter(log_format)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Create application logger
    logger = logging.getLogger("SeleniumRecorder")
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger

def add_rotating_file_handler(
    logger: logging.Logger,
    log_file: str,
    max_bytes: int = 10485760,  # 10 MB
    backup_count: int = 5,
    level: int = logging.DEBUG,
    log_format: Optional[str] = None
) -> None:
    """
    Add a rotating file handler to a logger.
    
    Args:
        logger: Logger to add handler to
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        level: Logging level
        log_format: Log message format
    """
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Set default log format if not specified
    if not log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Create rotating file handler
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    logger.info(f"Added rotating file handler: {log_file}")

def get_log_levels() -> Dict[str, int]:
    """
    Get a dictionary of log level names and values.
    
    Returns:
        Dictionary of log level names and values
    """
    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

def set_logger_level(logger_name: str, level: int) -> None:
    """
    Set the level of a logger.
    
    Args:
        logger_name: Name of logger
        level: Logging level
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.info(f"Set logger {logger_name} level to {level}")

def create_log_filter(excluded_loggers: List[str]) -> logging.Filter:
    """
    Create a filter to exclude logs from specified loggers.
    
    Args:
        excluded_loggers: List of logger names to exclude
        
    Returns:
        Logging filter
    """
    class LogFilter(logging.Filter):
        def filter(self, record):
            return not any(record.name.startswith(logger) for logger in excluded_loggers)
            
    return LogFilter()

def log_exception(logger: logging.Logger, exception: Exception, message: str = "An error occurred") -> None:
    """
    Log an exception with traceback.
    
    Args:
        logger: Logger to use
        exception: Exception to log
        message: Message to log
    """
    logger.error(f"{message}: {str(exception)}", exc_info=True)
