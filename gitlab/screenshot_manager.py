"""
screenshot_manager.py - Screenshot manager for Selenium Recorder

This module handles the storage, retrieval, and management of screenshots
taken during recording and playback.
"""

import os
import shutil
import glob
from datetime import datetime
from typing import Dict, List, Optional, Set
import logging

class ScreenshotManager:
    """
    Manager for handling screenshots.
    """
    
    def __init__(self, screenshot_dir: str = "screenshots"):
        """
        Initialize the screenshot manager.
        
        Args:
            screenshot_dir: Directory to store screenshots
        """
        self.screenshot_dir = screenshot_dir
        self.current_session_dir = None
        self.screenshots = {}  # Map of screenshot_id to filename
        self.logger = logging.getLogger("ScreenshotManager")
        
        # Create screenshot directory if it doesn't exist
        self._ensure_directory(self.screenshot_dir)
        
    def start_session(self, session_id: Optional[str] = None) -> str:
        """
        Start a new screenshot session.
        
        Args:
            session_id: Optional session ID, generated if not provided
            
        Returns:
            Session ID
        """
        # Generate session ID if not provided
        if not session_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}"
            
        # Create session directory
        self.current_session_dir = os.path.join(self.screenshot_dir, session_id)
        self._ensure_directory(self.current_session_dir)
        
        # Clear screenshots map
        self.screenshots = {}
        
        self.logger.info(f"Started screenshot session: {session_id}")
        return session_id
        
    def end_session(self):
        """
        End the current screenshot session.
        """
        self.current_session_dir = None
        self.logger.info("Ended screenshot session")
        
    def save_screenshot(self, image_data: bytes, step_id: str) -> Optional[str]:
        """
        Save a screenshot from image data.
        
        Args:
            image_data: Screenshot image data
            step_id: ID of the step associated with the screenshot
            
        Returns:
            Screenshot ID if successful, None otherwise
        """
        if not self.current_session_dir:
            self.logger.error("No active screenshot session")
            return None
            
        try:
            # Generate screenshot ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            screenshot_id = f"screenshot_{timestamp}"
            
            # Create filename
            filename = f"{screenshot_id}.png"
            path = os.path.join(self.current_session_dir, filename)
            
            # Save image data
            with open(path, "wb") as f:
                f.write(image_data)
                
            # Store in map
            self.screenshots[screenshot_id] = filename
            
            self.logger.info(f"Saved screenshot {screenshot_id} for step {step_id}")
            return screenshot_id
            
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {str(e)}")
            return None
            
    def save_screenshot_file(self, file_path: str, step_id: str) -> Optional[str]:
        """
        Save a screenshot from an existing file.
        
        Args:
            file_path: Path to screenshot file
            step_id: ID of the step associated with the screenshot
            
        Returns:
            Screenshot ID if successful, None otherwise
        """
        if not self.current_session_dir:
            self.logger.error("No active screenshot session")
            return None
            
        if not os.path.exists(file_path):
            self.logger.error(f"Screenshot file not found: {file_path}")
            return None
            
        try:
            # Generate screenshot ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            screenshot_id = f"screenshot_{timestamp}"
            
            # Create filename
            filename = f"{screenshot_id}.png"
            dest_path = os.path.join(self.current_session_dir, filename)
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            
            # Store in map
            self.screenshots[screenshot_id] = filename
            
            self.logger.info(f"Saved screenshot {screenshot_id} for step {step_id}")
            return screenshot_id
            
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {str(e)}")
            return None
            
    def get_screenshot_path(self, screenshot_id: str) -> Optional[str]:
        """
        Get the path to a screenshot.
        
        Args:
            screenshot_id: ID of the screenshot
            
        Returns:
            Path to the screenshot file, or None if not found
        """
        if not self.current_session_dir:
            self.logger.error("No active screenshot session")
            return None
            
        filename = self.screenshots.get(screenshot_id)
        if not filename:
            self.logger.error(f"Screenshot not found: {screenshot_id}")
            return None
            
        path = os.path.join(self.current_session_dir, filename)
        if not os.path.exists(path):
            self.logger.error(f"Screenshot file not found: {path}")
            return None
            
        return path
        
    def load_session(self, session_id: str) -> bool:
        """
        Load an existing screenshot session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            True if session loaded successfully, False otherwise
        """
        session_dir = os.path.join(self.screenshot_dir, session_id)
        if not os.path.exists(session_dir):
            self.logger.error(f"Session directory not found: {session_dir}")
            return False
            
        try:
            # Set session directory
            self.current_session_dir = session_dir
            
            # Clear screenshots map
            self.screenshots = {}
            
            # Load screenshots
            pattern = os.path.join(session_dir, "screenshot_*.png")
            for path in glob.glob(pattern):
                filename = os.path.basename(path)
                screenshot_id = os.path.splitext(filename)[0]
                self.screenshots[screenshot_id] = filename
                
            self.logger.info(f"Loaded screenshot session: {session_id} with {len(self.screenshots)} screenshots")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading session: {str(e)}")
            return False
            
    def delete_screenshot(self, screenshot_id: str) -> bool:
        """
        Delete a screenshot.
        
        Args:
            screenshot_id: ID of the screenshot to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.current_session_dir:
            self.logger.error("No active screenshot session")
            return False
            
        filename = self.screenshots.get(screenshot_id)
        if not filename:
            self.logger.error(f"Screenshot not found: {screenshot_id}")
            return False
            
        path = os.path.join(self.current_session_dir, filename)
        if not os.path.exists(path):
            self.logger.error(f"Screenshot file not found: {path}")
            return False
            
        try:
            # Delete file
            os.remove(path)
            
            # Remove from map
            del self.screenshots[screenshot_id]
            
            self.logger.info(f"Deleted screenshot: {screenshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting screenshot: {str(e)}")
            return False
            
    def cleanup_unused_screenshots(self, used_ids: Set[str]) -> int:
        """
        Delete screenshots that are not used by any step.
        
        Args:
            used_ids: Set of screenshot IDs that are in use
            
        Returns:
            Number of screenshots deleted
        """
        if not self.current_session_dir:
            self.logger.error("No active screenshot session")
            return 0
            
        count = 0
        unused_ids = set(self.screenshots.keys()) - used_ids
        
        for screenshot_id in unused_ids:
            if self.delete_screenshot(screenshot_id):
                count += 1
                
        self.logger.info(f"Cleaned up {count} unused screenshots")
        return count
        
    def get_all_screenshots(self) -> Dict[str, str]:
        """
        Get all screenshots in the current session.
        
        Returns:
            Dictionary mapping screenshot IDs to file paths
        """
        if not self.current_session_dir:
            return {}
            
        result = {}
        for screenshot_id, filename in self.screenshots.items():
            path = os.path.join(self.current_session_dir, filename)
            if os.path.exists(path):
                result[screenshot_id] = path
                
        return result
        
    def _ensure_directory(self, directory: str):
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"Created directory: {directory}")
