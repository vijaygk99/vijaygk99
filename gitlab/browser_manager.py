"""
browser_manager.py - Browser session management for Selenium Recorder

This module handles browser initialization, configuration, and session management
with comprehensive error handling and recovery mechanisms.
"""

import os
import time
import logging
from typing import Dict, Optional, Tuple, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

class BrowserManager:
    """
    Manages browser sessions for the Selenium recorder with robust error handling
    and recovery mechanisms.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the browser manager with optional configuration.
        
        Args:
            config: Dictionary containing configuration options:
                - chromedriver_path: Path to ChromeDriver executable
                - download_dir: Directory for downloaded files
                - headless: Boolean to run browser in headless mode
                - user_agent: Custom user agent string
                - proxy: Proxy configuration
                - extensions: List of extension paths to load
        """
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[WebDriver] = None
        self.config = config or {}
        self.is_recording = False
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        
    def start_browser(self) -> Tuple[bool, str]:
        """
        Start a new browser session with configured options.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.driver:
            self.logger.warning("Browser session already exists. Closing existing session.")
            self.stop_browser()
            
        try:
            options = self._configure_chrome_options()
            driver_path = self._get_driver_path()
            
            self.logger.info(f"Starting Chrome with driver at: {driver_path}")
            
            service = Service(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set default timeout
            self.driver.implicitly_wait(10)
            self.driver.set_script_timeout(30)
            self.driver.set_page_load_timeout(30)
            
            # Test browser is responsive
            self.driver.get("about:blank")
            
            self.logger.info("Browser started successfully")
            return True, "Browser started successfully"
            
        except SessionNotCreatedException as e:
            error_msg = f"Failed to create browser session: {str(e)}"
            self.logger.error(error_msg)
            
            # Check if this is a ChromeDriver version mismatch
            if "This version of ChromeDriver only supports Chrome version" in str(e):
                try:
                    self.logger.info("Attempting to download compatible ChromeDriver...")
                    driver_path = ChromeDriverManager().install()
                    self.config["chromedriver_path"] = driver_path
                    return self.start_browser()  # Retry with new driver
                except Exception as download_error:
                    self.logger.error(f"Failed to download compatible driver: {str(download_error)}")
                    
            return False, error_msg
            
        except WebDriverException as e:
            error_msg = f"WebDriver error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error starting browser: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def stop_browser(self) -> Tuple[bool, str]:
        """
        Stop the current browser session safely.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.driver:
            return True, "No browser session to stop"
            
        try:
            # Execute any cleanup JavaScript if needed
            try:
                self.driver.execute_script("return window.name;")  # Simple test if browser responsive
                # Remove any injected scripts or listeners
                self.driver.execute_script("""
                    if (window._seleniumRecorderCleanup) {
                        window._seleniumRecorderCleanup();
                    }
                """)
            except Exception as js_error:
                self.logger.warning(f"Could not execute cleanup script: {str(js_error)}")
                
            # Close browser
            self.driver.quit()
            self.driver = None
            self.is_recording = False
            self.recovery_attempts = 0
            
            self.logger.info("Browser stopped successfully")
            return True, "Browser stopped successfully"
            
        except Exception as e:
            error_msg = f"Error stopping browser: {str(e)}"
            self.logger.error(error_msg)
            
            # Force cleanup if normal quit fails
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
                
            self.driver = None
            self.is_recording = False
            
            return False, error_msg
    
    def navigate_to(self, url: str) -> Tuple[bool, str]:
        """
        Navigate browser to specified URL with error handling.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.driver:
            return False, "No active browser session"
            
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            self._wait_for_page_load()
            
            return True, f"Successfully navigated to {url}"
            
        except Exception as e:
            error_msg = f"Error navigating to {url}: {str(e)}"
            self.logger.error(error_msg)
            
            # Attempt recovery if browser crashed
            if self._is_browser_crashed():
                return self._attempt_recovery(lambda: self.navigate_to(url))
                
            return False, error_msg
    
    def inject_recorder_scripts(self) -> Tuple[bool, str]:
        """
        Inject JavaScript needed for recording user actions.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.driver:
            return False, "No active browser session"
            
        try:
            # Basic recorder script - will be expanded in recorder.py
            recorder_js = """
            (function() {
                // Store original functions to avoid multiple wrapping
                if (window._seleniumRecorderInjected) {
                    return "Recorder already injected";
                }
                
                window._seleniumRecorderInjected = true;
                window._seleniumRecorderEvents = [];
                
                // Setup cleanup function
                window._seleniumRecorderCleanup = function() {
                    window._seleniumRecorderInjected = false;
                    window._seleniumRecorderEvents = [];
                    // Additional cleanup will be added
                };
                
                // Basic event capture - will be expanded
                function captureEvent(e) {
                    var target = e.target;
                    window._seleniumRecorderEvents.push({
                        type: e.type,
                        timestamp: Date.now(),
                        target: {
                            tagName: target.tagName,
                            id: target.id,
                            className: target.className,
                            name: target.name,
                            type: target.type,
                            value: target.value,
                            checked: target.checked,
                            href: target.href,
                            innerText: target.innerText ? target.innerText.substring(0, 50) : '',
                            xpath: ''  // Will be filled by backend
                        },
                        x: e.clientX,
                        y: e.clientY
                    });
                    return true;
                }
                
                // Add basic event listeners - more will be added in recorder.py
                document.addEventListener('click', captureEvent, true);
                document.addEventListener('change', captureEvent, true);
                document.addEventListener('input', captureEvent, true);
                
                return "Recorder scripts injected successfully";
            })();
            """
            
            result = self.driver.execute_script(recorder_js)
            self.logger.info(f"Injected recorder scripts: {result}")
            self.is_recording = True
            
            return True, "Recorder scripts injected successfully"
            
        except Exception as e:
            error_msg = f"Error injecting recorder scripts: {str(e)}"
            self.logger.error(error_msg)
            
            # Attempt recovery if browser crashed
            if self._is_browser_crashed():
                return self._attempt_recovery(self.inject_recorder_scripts)
                
            return False, error_msg
    
    def get_recorded_events(self) -> Tuple[bool, List, str]:
        """
        Retrieve recorded events from the browser.
        
        Returns:
            Tuple of (success: bool, events: List, message: str)
        """
        if not self.driver:
            return False, [], "No active browser session"
            
        if not self.is_recording:
            return False, [], "Recording not started"
            
        try:
            events = self.driver.execute_script("return window._seleniumRecorderEvents;")
            self.driver.execute_script("window._seleniumRecorderEvents = [];")
            
            return True, events, f"Retrieved {len(events)} events"
            
        except Exception as e:
            error_msg = f"Error retrieving recorded events: {str(e)}"
            self.logger.error(error_msg)
            
            # Attempt recovery if browser crashed
            if self._is_browser_crashed():
                return self._attempt_recovery(self.get_recorded_events)
                
            return False, [], error_msg
    
    def take_screenshot(self, filename: Optional[str] = None) -> Tuple[bool, str]:
        """
        Take a screenshot of the current browser window.
        
        Args:
            filename: Optional filename for the screenshot
            
        Returns:
            Tuple of (success: bool, filepath or error message: str)
        """
        if not self.driver:
            return False, "No active browser session"
            
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                screenshots_dir = self.config.get("screenshot_dir", "screenshots")
                
                # Ensure directory exists
                os.makedirs(screenshots_dir, exist_ok=True)
                
                filename = f"{screenshots_dir}/screenshot_{timestamp}.png"
                
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved to {filename}")
            
            return True, filename
            
        except Exception as e:
            error_msg = f"Error taking screenshot: {str(e)}"
            self.logger.error(error_msg)
            
            # Attempt recovery if browser crashed
            if self._is_browser_crashed():
                return self._attempt_recovery(lambda: self.take_screenshot(filename))
                
            return False, error_msg
    
    def _configure_chrome_options(self) -> Options:
        """
        Configure Chrome options based on user settings.
        
        Returns:
            Configured Chrome options object
        """
        options = Options()
        
        # Set download directory
        if "download_dir" in self.config:
            download_dir = os.path.abspath(self.config["download_dir"])
            os.makedirs(download_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
        
        # Headless mode
        if self.config.get("headless", False):
            options.add_argument("--headless=new")
        
        # User agent
        if "user_agent" in self.config:
            options.add_argument(f"--user-agent={self.config['user_agent']}")
        
        # Proxy settings
        if "proxy" in self.config:
            options.add_argument(f"--proxy-server={self.config['proxy']}")
        
        # Extensions
        if "extensions" in self.config and isinstance(self.config["extensions"], list):
            for extension_path in self.config["extensions"]:
                if os.path.exists(extension_path):
                    options.add_extension(extension_path)
                else:
                    self.logger.warning(f"Extension not found: {extension_path}")
        
        # Additional Chrome flags for stability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--start-maximized")
        
        # Disable automation info bar
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        return options
    
    def _get_driver_path(self) -> str:
        """
        Get the ChromeDriver path, downloading if necessary.
        
        Returns:
            Path to ChromeDriver executable
        """
        # Use provided path if available
        if "chromedriver_path" in self.config and os.path.exists(self.config["chromedriver_path"]):
            return self.config["chromedriver_path"]
            
        # Otherwise, use webdriver-manager to download appropriate driver
        try:
            self.logger.info("No ChromeDriver specified, downloading compatible version...")
            driver_path = ChromeDriverManager().install()
            self.config["chromedriver_path"] = driver_path
            return driver_path
        except Exception as e:
            self.logger.error(f"Error downloading ChromeDriver: {str(e)}")
            raise ValueError(f"ChromeDriver not found and could not be downloaded: {str(e)}")
    
    def _wait_for_page_load(self, timeout: int = 30) -> None:
        """
        Wait for page to fully load.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        try:
            # Wait for document ready state
            wait_script = """
                let callback = arguments[arguments.length - 1];
                if (document.readyState === 'complete') {
                    callback('complete');
                    return;
                }
                
                let timeout = setTimeout(() => {
                    window.removeEventListener('load', loaded);
                    callback('timeout');
                }, 30000);
                
                function loaded() {
                    clearTimeout(timeout);
                    callback('complete');
                }
                
                window.addEventListener('load', loaded);
            """
            self.driver.execute_async_script(wait_script)
            
            # Additional wait for any AJAX requests
            ajax_script = """
                let callback = arguments[arguments.length - 1];
                if (typeof jQuery !== 'undefined') {
                    let active = jQuery.active;
                    if (active === 0) {
                        callback(true);
                        return;
                    }
                    
                    let timeout = setTimeout(() => {
                        $(document).unbind('ajaxStop', ajaxStop);
                        callback(false);
                    }, 5000);
                    
                    function ajaxStop() {
                        clearTimeout(timeout);
                        callback(true);
                    }
                    
                    $(document).ajaxStop(ajaxStop);
                } else {
                    callback(true);
                }
            """
            try:
                self.driver.execute_async_script(ajax_script)
            except:
                # jQuery might not be available, ignore errors
                pass
                
        except Exception as e:
            self.logger.warning(f"Error waiting for page load: {str(e)}")
    
    def _is_browser_crashed(self) -> bool:
        """
        Check if browser has crashed or lost connection.
        
        Returns:
            True if browser appears to be crashed
        """
        if not self.driver:
            return False
            
        try:
            # Simple test to see if browser is responsive
            self.driver.execute_script("return navigator.userAgent;")
            return False
        except:
            return True
    
    def _attempt_recovery(self, callback):
        """
        Attempt to recover from browser crash.
        
        Args:
            callback: Function to call after recovery attempt
            
        Returns:
            Result of callback or error tuple
        """
        self.recovery_attempts += 1
        
        if self.recovery_attempts > self.max_recovery_attempts:
            self.logger.error("Maximum recovery attempts reached")
            self.stop_browser()
            return False, "Browser recovery failed after multiple attempts"
            
        self.logger.warning(f"Attempting browser recovery ({self.recovery_attempts}/{self.max_recovery_attempts})")
        
        # Stop and restart browser
        self.stop_browser()
        success, message = self.start_browser()
        
        if success:
            self.logger.info("Browser recovered successfully")
            return callback()
        else:
            return False, f"Browser recovery failed: {message}"
