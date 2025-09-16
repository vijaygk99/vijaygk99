"""
file_utils.py - File utility functions for Selenium Recorder

This module provides utility functions for file operations,
including saving/loading files and managing file paths.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger("FileUtils")

def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
        
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False

def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation level
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # Save to temporary file first to prevent corruption
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            json.dump(data, temp_file, indent=indent)
            temp_path = temp_file.name
            
        # Replace target file with temporary file
        shutil.move(temp_path, file_path)
        
        logger.info(f"Saved JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {str(e)}")
        return False

def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data, or None if error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        logger.info(f"Loaded JSON from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {str(e)}")
        return None

def save_text(text: str, file_path: str) -> bool:
    """
    Save text to a file.
    
    Args:
        text: Text to save
        file_path: Path to save file
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # Save to temporary file first to prevent corruption
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(text)
            temp_path = temp_file.name
            
        # Replace target file with temporary file
        shutil.move(temp_path, file_path)
        
        logger.info(f"Saved text to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving text to {file_path}: {str(e)}")
        return False

def load_text(file_path: str) -> Optional[str]:
    """
    Load text from a file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Loaded text, or None if error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r') as f:
            text = f.read()
            
        logger.info(f"Loaded text from {file_path}")
        return text
    except Exception as e:
        logger.error(f"Error loading text from {file_path}: {str(e)}")
        return None

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File extension (without dot)
    """
    return os.path.splitext(file_path)[1][1:]

def get_recent_files(max_files: int = 10) -> List[str]:
    """
    Get list of recent files from recent files list.
    
    Args:
        max_files: Maximum number of files to return
        
    Returns:
        List of recent file paths
    """
    try:
        recent_files_path = os.path.join(os.path.expanduser("~"), ".selenium_recorder", "recent_files.json")
        
        if not os.path.exists(recent_files_path):
            return []
            
        with open(recent_files_path, 'r') as f:
            recent_files = json.load(f)
            
        # Return only existing files
        return [f for f in recent_files[:max_files] if os.path.exists(f)]
    except Exception as e:
        logger.error(f"Error getting recent files: {str(e)}")
        return []

def add_recent_file(file_path: str, max_files: int = 10) -> bool:
    """
    Add a file to the recent files list.
    
    Args:
        file_path: Path to file
        max_files: Maximum number of files to keep
        
    Returns:
        True if added successfully, False otherwise
    """
    try:
        # Get absolute path
        file_path = os.path.abspath(file_path)
        
        # Get recent files
        recent_files = get_recent_files(max_files=100)  # Get all recent files
        
        # Remove file if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add file to beginning of list
        recent_files.insert(0, file_path)
        
        # Trim list to max_files
        recent_files = recent_files[:max_files]
        
        # Save recent files
        recent_files_dir = os.path.join(os.path.expanduser("~"), ".selenium_recorder")
        if not os.path.exists(recent_files_dir):
            os.makedirs(recent_files_dir)
            
        recent_files_path = os.path.join(recent_files_dir, "recent_files.json")
        
        with open(recent_files_path, 'w') as f:
            json.dump(recent_files, f, indent=2)
            
        logger.info(f"Added {file_path} to recent files")
        return True
    except Exception as e:
        logger.error(f"Error adding recent file: {str(e)}")
        return False
