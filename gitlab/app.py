"""
app.py - Main entry point for Selenium Recorder

This module initializes the application, sets up logging,
and creates the main window.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core components
from selenium_recorder.core.config_manager import ConfigManager
from selenium_recorder.core.browser_manager import BrowserManager
from selenium_recorder.core.recorder import Recorder
from selenium_recorder.core.playback_engine import PlaybackEngine
from selenium_recorder.core.script_generator import ScriptGenerator
from selenium_recorder.core.screenshot_manager import ScreenshotManager

# Import UI components
from selenium_recorder.ui.main_window import MainWindow

def setup_logging():
    """
    Set up logging configuration.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("selenium_recorder.log")
        ]
    )
    
    # Create logger
    logger = logging.getLogger("SeleniumRecorder")
    logger.info("Starting Selenium Recorder")
    
    return logger

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Selenium Recorder")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--browser", help="Browser type (chrome, firefox, edge, safari)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    return parser.parse_args()

def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging()
    
    try:
        # Initialize configuration manager
        config_file = args.config if args.config else "config.json"
        config_manager = ConfigManager(config_file)
        
        # Override config with command line arguments
        if args.browser:
            config_manager.set_value("browser.type", args.browser)
        if args.headless:
            config_manager.set_value("browser.headless", True)
        
        # Get configuration
        config = config_manager.get_config()
        
        # Initialize managers
        screenshot_manager = ScreenshotManager(config.get("screenshot_dir", "screenshots"))
        browser_manager = BrowserManager(config)
        
        # Initialize core components
        script_generator = ScriptGenerator()
        recorder = Recorder(browser_manager, screenshot_manager)
        playback_engine = PlaybackEngine(browser_manager, screenshot_manager)
        
        # Create main window
        app = MainWindow(
            config_manager=config_manager,
            browser_manager=browser_manager,
            recorder=recorder,
            playback_engine=playback_engine,
            script_generator=script_generator,
            screenshot_manager=screenshot_manager
        )
        
        # Start application
        app.run()
        
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
