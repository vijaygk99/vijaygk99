"""
playback_engine.py - Playback engine for Selenium Recorder

This module handles executing recorded steps during playback,
including element location, action execution, and error handling.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    WebDriverException, 
    TimeoutException, 
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

class PlaybackEngine:
    """
    Engine for executing recorded steps during playback.
    """
    
    def __init__(self, browser_manager, screenshot_manager=None):
        """
        Initialize the playback engine.
        
        Args:
            browser_manager: BrowserManager instance
            screenshot_manager: ScreenshotManager instance (optional)
        """
        self.browser_manager = browser_manager
        self.screenshot_manager = screenshot_manager
        self.logger = logging.getLogger("PlaybackEngine")
        
        # Playback state
        self.is_playing = False
        self.current_step_index = -1
        self.steps = []
        
        # Callbacks
        self.on_step_start = None
        self.on_step_complete = None
        self.on_step_error = None
        self.on_playback_complete = None
        
        # Step handlers
        self.step_handlers = {
            "navigate": self._handle_navigate,
            "click": self._handle_click,
            "double_click": self._handle_double_click,
            "right_click": self._handle_right_click,
            "hover": self._handle_hover,
            "input": self._handle_input,
            "select": self._handle_select,
            "check": self._handle_check,
            "uncheck": self._handle_uncheck,
            "press_key": self._handle_press_key,
            "drag_and_drop": self._handle_drag_and_drop,
            "switch_to_frame": self._handle_switch_to_frame,
            "switch_to_default_content": self._handle_switch_to_default_content,
            "accept_alert": self._handle_accept_alert,
            "dismiss_alert": self._handle_dismiss_alert,
            "execute_script": self._handle_execute_script,
            "wait": self._handle_wait
        }
        
    def set_steps(self, steps: List[Dict[str, Any]]):
        """
        Set the steps to play back.
        
        Args:
            steps: List of steps to play back
        """
        self.steps = steps
        self.current_step_index = -1
        
    def play(self, 
             on_step_start: Optional[Callable[[Dict[str, Any], int], None]] = None,
             on_step_complete: Optional[Callable[[Dict[str, Any], int, bool], None]] = None,
             on_step_error: Optional[Callable[[Dict[str, Any], int, Exception], None]] = None,
             on_playback_complete: Optional[Callable[[bool], None]] = None):
        """
        Play back the steps.
        
        Args:
            on_step_start: Callback when a step starts
            on_step_complete: Callback when a step completes
            on_step_error: Callback when a step encounters an error
            on_playback_complete: Callback when playback completes
        """
        if not self.steps:
            self.logger.warning("No steps to play back")
            if on_playback_complete:
                on_playback_complete(True)
            return
            
        # Set callbacks
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_step_error = on_step_error
        self.on_playback_complete = on_playback_complete
        
        # Start playback
        self.is_playing = True
        self.current_step_index = -1
        self._play_next_step()
        
    def stop(self):
        """
        Stop playback.
        """
        self.is_playing = False
        self.logger.info("Playback stopped")
        
    def pause(self):
        """
        Pause playback.
        """
        self.is_playing = False
        self.logger.info("Playback paused")
        
    def resume(self):
        """
        Resume playback.
        """
        if self.current_step_index >= 0 and self.current_step_index < len(self.steps):
            self.is_playing = True
            self._play_next_step()
            self.logger.info("Playback resumed")
        else:
            self.logger.warning("Cannot resume playback: no current step")
            
    def _play_next_step(self):
        """
        Play the next step.
        """
        if not self.is_playing:
            return
            
        # Move to next step
        self.current_step_index += 1
        
        # Check if we're done
        if self.current_step_index >= len(self.steps):
            self.is_playing = False
            self.logger.info("Playback completed successfully")
            if self.on_playback_complete:
                self.on_playback_complete(True)
            return
            
        # Get current step
        step = self.steps[self.current_step_index]
        
        # Notify step start
        if self.on_step_start:
            self.on_step_start(step, self.current_step_index)
            
        # Get step action
        action = step.get("action", "")
        
        # Get handler for action
        handler = self.step_handlers.get(action)
        
        if not handler:
            error = ValueError(f"Unsupported action: {action}")
            self._handle_step_error(step, error)
            return
            
        try:
            # Execute step with delay
            delay = self.browser_manager.config.get("playback_delay", 0.5)
            time.sleep(delay)
            
            # Execute step
            handler(step)
            
            # Take screenshot if needed
            if self.screenshot_manager and self.browser_manager.driver:
                screenshot_id = f"playback_{self.current_step_index}"
                screenshot_path = self.browser_manager.take_screenshot(screenshot_id)
                if screenshot_path:
                    step["playback_screenshot"] = screenshot_id
                    
            # Notify step complete
            if self.on_step_complete:
                self.on_step_complete(step, self.current_step_index, True)
                
            # Play next step
            self._play_next_step()
            
        except Exception as e:
            self._handle_step_error(step, e)
    def _handle_step_error(self, step: Dict[str, Any], error: Exception):
        """
        Handle an error during step execution.
        
        Args:
            step: Step that encountered an error
            error: Exception that occurred
        """
        self.logger.error(f"Error executing step {self.current_step_index}: {str(error)}")
        
        # Notify step error
        if self.on_step_error:
            self.on_step_error(step, self.current_step_index, error)
            
        # Stop playback
        self.is_playing = False
        
        # Notify playback complete with error
        if self.on_playback_complete:
            self.on_playback_complete(False)
            
    def _find_element(self, step: Dict[str, Any], locators_key: str = "locators") -> Any:
        """
        Find an element using the locators in a step.
        
        Args:
            step: Step data
            locators_key: Key for locators in step data
            
        Returns:
            WebElement if found
            
        Raises:
            NoSuchElementException: If element not found
        """
        locators = step.get(locators_key, {})
        wait_timeout = self.browser_manager.config.get("playback", {}).get("wait_timeout", 30)
        
        # Try ID locator (most reliable)
        if locators.get("id"):
            try:
                return WebDriverWait(self.browser_manager.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.ID, locators["id"]))
                )
            except (TimeoutException, NoSuchElementException):
                pass
                
        # Try name locator
        if locators.get("name"):
            try:
                return WebDriverWait(self.browser_manager.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.NAME, locators["name"]))
                )
            except (TimeoutException, NoSuchElementException):
                pass
                
        # Try CSS selector
        if locators.get("css"):
            try:
                return WebDriverWait(self.browser_manager.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, locators["css"]))
                )
            except (TimeoutException, NoSuchElementException):
                pass
                
        # Try XPath
        xpath_types = ["id_based", "attributes", "text", "full"]
        for xpath_type in xpath_types:
            if locators.get("xpath", {}).get(xpath_type):
                try:
                    return WebDriverWait(self.browser_manager.driver, wait_timeout).until(
                        EC.presence_of_element_located((By.XPATH, locators["xpath"][xpath_type]))
                    )
                except (TimeoutException, NoSuchElementException):
                    pass
                    
        # Try link text
        if locators.get("link_text"):
            try:
                return WebDriverWait(self.browser_manager.driver, wait_timeout).until(
                    EC.presence_of_element_located((By.LINK_TEXT, locators["link_text"]))
                )
            except (TimeoutException, NoSuchElementException):
                pass
                
        # If we get here, element not found
        raise NoSuchElementException(f"Element not found with locators: {locators}")
        
    def _handle_navigate(self, step: Dict[str, Any]):
        """
        Handle navigate action.
        
        Args:
            step: Step data
        """
        url = step.get("url", "")
        if not url:
            raise ValueError("URL not specified for navigate action")
            
        self.browser_manager.navigate(url)
        
        # Wait for page to load if configured
        wait_for_page_load = self.browser_manager.config.get("playback", {}).get("wait_for_page_load", True)
        if wait_for_page_load:
            WebDriverWait(self.browser_manager.driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
    def _handle_click(self, step: Dict[str, Any]):
        """
        Handle click action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Click element
        element.click()

    def _handle_double_click(self, step: Dict[str, Any]):
        """
        Handle double click action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Double click element
        ActionChains(self.browser_manager.driver).double_click(element).perform()
        
    def _handle_right_click(self, step: Dict[str, Any]):
        """
        Handle right click action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Right click element
        ActionChains(self.browser_manager.driver).context_click(element).perform()
        
    def _handle_hover(self, step: Dict[str, Any]):
        """
        Handle hover action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Hover over element
        ActionChains(self.browser_manager.driver).move_to_element(element).perform()
        
    def _handle_input(self, step: Dict[str, Any]):
        """
        Handle input action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        value = step.get("value", "")
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Clear and input value
        element.clear()
        element.send_keys(value)
        
    def _handle_select(self, step: Dict[str, Any]):
        """
        Handle select action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        selected_options = step.get("selected_options", [])
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Create select object
        select = Select(element)
        
        # Select options
        for option in selected_options:
            value = option.get("value")
            text = option.get("text")
            
            if value:
                select.select_by_value(value)
            elif text:
                select.select_by_visible_text(text)
                
    def _handle_check(self, step: Dict[str, Any]):
        """
        Handle check action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Check if not already checked
        if not element.is_selected():
            element.click()
    def _handle_uncheck(self, step: Dict[str, Any]):
        """
        Handle uncheck action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Uncheck if checked
        if element.is_selected():
            element.click()
            
    def _handle_press_key(self, step: Dict[str, Any]):
        """
        Handle press key action.
        
        Args:
            step: Step data
        """
        element = self._find_element(step)
        key = step.get("key", "")
        
        # Highlight element if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(element)
            
        # Map key string to Keys constant
        key_mapping = {
            "ENTER": Keys.ENTER,
            "TAB": Keys.TAB,
            "ESCAPE": Keys.ESCAPE,
            "ARROW_UP": Keys.UP,
            "ARROW_DOWN": Keys.DOWN,
            "ARROW_LEFT": Keys.LEFT,
            "ARROW_RIGHT": Keys.RIGHT,
            "BACK_SPACE": Keys.BACK_SPACE,
            "DELETE": Keys.DELETE,
            "HOME": Keys.HOME,
            "END": Keys.END,
            "PAGE_UP": Keys.PAGE_UP,
            "PAGE_DOWN": Keys.PAGE_DOWN
        }
        
        # Get key to press
        selenium_key = key_mapping.get(key, key)
        
        # Press key
        element.send_keys(selenium_key)
        
    def _handle_drag_and_drop(self, step: Dict[str, Any]):
        """
        Handle drag and drop action.
        
        Args:
            step: Step data
        """
        source = self._find_element(step, "source_locators")
        target = self._find_element(step, "target_locators")
        
        # Highlight elements if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(source)
            self.browser_manager.highlight_element(target)
            
        # Perform drag and drop
        ActionChains(self.browser_manager.driver).drag_and_drop(source, target).perform()
        
    def _handle_switch_to_frame(self, step: Dict[str, Any]):
        """
        Handle switch to frame action.
        
        Args:
            step: Step data
        """
        frame = self._find_element(step)
        
        # Highlight frame if configured
        highlight_elements = self.browser_manager.config.get("playback", {}).get("highlight_elements", True)
        if highlight_elements:
            self.browser_manager.highlight_element(frame)
            
        # Switch to frame
        self.browser_manager.driver.switch_to.frame(frame)

    def _handle_switch_to_default_content(self, step: Dict[str, Any]):
        """
        Handle switch to default content action.
        
        Args:
            step: Step data
        """
        # Switch to default content
        self.browser_manager.driver.switch_to.default_content()
        
    def _handle_accept_alert(self, step: Dict[str, Any]):
        """
        Handle accept alert action.
        
        Args:
            step: Step data
        """
        # Wait for alert to be present
        WebDriverWait(self.browser_manager.driver, 10).until(EC.alert_is_present())
        
        # Accept alert
        alert = self.browser_manager.driver.switch_to.alert
        alert.accept()
        
    def _handle_dismiss_alert(self, step: Dict[str, Any]):
        """
        Handle dismiss alert action.
        
        Args:
            step: Step data
        """
        # Wait for alert to be present
        WebDriverWait(self.browser_manager.driver, 10).until(EC.alert_is_present())
        
        # Dismiss alert
        alert = self.browser_manager.driver.switch_to.alert
        alert.dismiss()
        
    def _handle_execute_script(self, step: Dict[str, Any]):
        """
        Handle execute script action.
        
        Args:
            step: Step data
        """
        script = step.get("script", "")
        arguments = step.get("arguments", [])
        
        if not script:
            raise ValueError("Script not specified for execute_script action")
            
        # Execute script
        result = self.browser_manager.execute_script(script, *arguments)
        
        # Store result if needed
        if "result_variable" in step:
            step["result"] = result
            
    def _handle_wait(self, step: Dict[str, Any]):
        """
        Handle wait action.
        
        Args:
            step: Step data
        """
        wait_type = step.get("wait_type", "time")
        wait_value = step.get("wait_value", 1)
        
        if wait_type == "time":
            # Wait for specified time
            time.sleep(float(wait_value))
        elif wait_type == "element":
            # Wait for element to be present
            self._find_element(step)
        elif wait_type == "page_load":
            # Wait for page to load
            WebDriverWait(self.browser_manager.driver, float(wait_value)).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        else:
            raise ValueError(f"Unsupported wait type: {wait_type}")
