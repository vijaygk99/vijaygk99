"""
recorder.py - Core recording engine for Selenium Recorder

This module captures browser interactions, processes them into structured steps,
and handles complex scenarios like iframes, shadow DOM, and alerts.
"""

import time
import logging
import json
import base64
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementNotInteractableException,
    JavascriptException,
    NoAlertPresentException,
    WebDriverException
)

class ActionRecorder:
    """
    Records user actions in the browser and processes them into structured steps.
    Handles complex scenarios like iframes, shadow DOM, and alerts.
    """
    
    def __init__(self, browser_manager, locator_engine, screenshot_manager=None):
        """
        Initialize the action recorder.
        
        Args:
            browser_manager: BrowserManager instance
            locator_engine: LocatorEngine instance
            screenshot_manager: Optional ScreenshotManager instance
        """
        self.logger = logging.getLogger(__name__)
        self.browser_manager = browser_manager
        self.locator_engine = locator_engine
        self.screenshot_manager = screenshot_manager
        
        self.driver = None
        self.is_recording = False
        self.recorded_steps = []
        self.current_frame_path = []
        self.shadow_root_path = []
        self.last_event_time = 0
        self.event_buffer = []
        self.step_callback = None
        self.polling_interval = 0.5  # seconds
        
        # Action type mapping
        self.action_types = {
            "click": self._process_click,
            "dblclick": self._process_double_click,
            "contextmenu": self._process_right_click,
            "mouseover": self._process_hover,
            "change": self._process_change,
            "input": self._process_input,
            "keydown": self._process_keydown,
            "dragstart": self._process_drag_start,
            "drop": self._process_drop,
            "select": self._process_select,
            "submit": self._process_submit,
            "focus": self._process_focus,
            "blur": self._process_blur
        }
        
    def start_recording(self, step_callback: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        Start recording user actions.
        
        Args:
            step_callback: Optional callback function to call when a step is recorded
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if self.is_recording:
            return False, "Recording already in progress"
            
        # Get driver from browser manager
        self.driver = self.browser_manager.driver
        if not self.driver:
            return False, "No active browser session"
            
        # Set driver in locator engine
        self.locator_engine.set_driver(self.driver)
        
        # Set callback
        self.step_callback = step_callback
        
        # Reset state
        self.recorded_steps = []
        self.current_frame_path = []
        self.shadow_root_path = []
        self.event_buffer = []
        self.last_event_time = time.time()
        
        try:
            # Inject recorder scripts
            success, message = self.browser_manager.inject_recorder_scripts()
            if not success:
                return False, f"Failed to inject recorder scripts: {message}"
                
            # Inject additional event listeners
            self._inject_additional_listeners()
            
            # Start polling for events
            self.is_recording = True
            self._start_event_polling()
            
            self.logger.info("Recording started successfully")
            return True, "Recording started successfully"
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {str(e)}")
            return False, f"Error starting recording: {str(e)}"
    
    def stop_recording(self) -> Tuple[bool, str]:
        """
        Stop recording user actions.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_recording:
            return False, "No recording in progress"
            
        try:
            # Stop polling
            self.is_recording = False
            
            # Process any remaining events
            self._poll_events()
            
            # Clean up
            self.driver = None
            self.step_callback = None
            
            self.logger.info(f"Recording stopped. {len(self.recorded_steps)} steps recorded.")
            return True, f"Recording stopped. {len(self.recorded_steps)} steps recorded."
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {str(e)}")
            return False, f"Error stopping recording: {str(e)}"
    
    def get_recorded_steps(self) -> List[Dict[str, Any]]:
        """
        Get the list of recorded steps.
        
        Returns:
            List of recorded steps
        """
        return self.recorded_steps
    
    def clear_recorded_steps(self) -> None:
        """
        Clear the list of recorded steps.
        """
        self.recorded_steps = []
        
    def _inject_additional_listeners(self) -> None:
        """
        Inject additional event listeners for complex interactions.
        """
        script = """
        (function() {
            if (window._seleniumRecorderExtendedInjected) {
                return "Extended listeners already injected";
            }
            
            window._seleniumRecorderExtendedInjected = true;
            
            // Extend cleanup function
            var originalCleanup = window._seleniumRecorderCleanup;
            window._seleniumRecorderCleanup = function() {
                window._seleniumRecorderExtendedInjected = false;
                if (originalCleanup) originalCleanup();
            };
            
            // Add more event listeners
            document.addEventListener('dblclick', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'dblclick',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    },
                    x: e.clientX,
                    y: e.clientY
                });
            }, true);
            
            document.addEventListener('contextmenu', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'contextmenu',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    },
                    x: e.clientX,
                    y: e.clientY
                });
            }, true);

            document.addEventListener('mouseover', function(e) {
                // Only record mouseover events that stay on an element for a while
                var target = e.target;
                var timestamp = Date.now();
                
                setTimeout(function() {
                    // Check if mouse is still over the element after delay
                    var currentElement = document.elementFromPoint(e.clientX, e.clientY);
                    if (currentElement === target) {
                        window._seleniumRecorderEvents.push({
                            type: 'mouseover',
                            timestamp: timestamp,
                            target: {
                                tagName: target.tagName,
                                id: target.id,
                                className: target.className,
                                name: target.name,
                                type: target.type,
                                value: target.value,
                                checked: target.checked,
                                href: target.href,
                                innerText: target.innerText ? target.innerText.substring(0, 50) : ''
                            },
                            x: e.clientX,
                            y: e.clientY
                        });
                    }
                }, 500); // 500ms delay to avoid recording accidental hovers
            }, true);
            
            document.addEventListener('keydown', function(e) {
                // Only record special keys like Enter, Tab, Escape, etc.
                var specialKeys = [
                    'Enter', 'Tab', 'Escape', 'ArrowUp', 'ArrowDown', 
                    'ArrowLeft', 'ArrowRight', 'Backspace', 'Delete', 
                    'Home', 'End', 'PageUp', 'PageDown'
                ];
                
                if (specialKeys.includes(e.key)) {
                    window._seleniumRecorderEvents.push({
                        type: 'keydown',
                        timestamp: Date.now(),
                        target: {
                            tagName: e.target.tagName,
                            id: e.target.id,
                            className: e.target.className,
                            name: e.target.name,
                            type: e.target.type,
                            value: e.target.value,
                            checked: e.target.checked,
                            href: e.target.href,
                            innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                        },
                        key: e.key
                    });
                }
            }, true);
            
            // Drag and drop events
            document.addEventListener('dragstart', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'dragstart',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    },
                    x: e.clientX,
                    y: e.clientY
                });
            }, true);
            
            document.addEventListener('drop', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'drop',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    },
                    x: e.clientX,
                    y: e.clientY
                });
            }, true);
            
            // Form submission
            document.addEventListener('submit', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'submit',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        action: e.target.action,
                        method: e.target.method
                    }
                });
            }, true);
            
            // Focus and blur events for tracking field interactions
            document.addEventListener('focus', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'focus',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    }
                });
            }, true);
            
            document.addEventListener('blur', function(e) {
                window._seleniumRecorderEvents.push({
                    type: 'blur',
                    timestamp: Date.now(),
                    target: {
                        tagName: e.target.tagName,
                        id: e.target.id,
                        className: e.target.className,
                        name: e.target.name,
                        type: e.target.type,
                        value: e.target.value,
                        checked: e.target.checked,
                        href: e.target.href,
                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                    }
                });
            }, true);
            
            // Monitor iframe navigation
            window._seleniumRecorderOriginalFrames = [];
            
            // Store original frame references
            try {
                var frames = document.querySelectorAll('iframe');
                for (var i = 0; i < frames.length; i++) {
                    window._seleniumRecorderOriginalFrames.push(frames[i]);
                    
                    // Try to add listeners to iframe content if same origin
                    try {
                        var frameDoc = frames[i].contentDocument;
                        if (frameDoc) {
                            // Add same listeners to iframe document
                            // (simplified for brevity - would repeat all listeners)
                            frameDoc.addEventListener('click', function(e) {
                                window._seleniumRecorderEvents.push({
                                    type: 'click',
                                    timestamp: Date.now(),
                                    inFrame: true,
                                    frameId: frames[i].id,
                                    frameName: frames[i].name,
                                    frameSrc: frames[i].src,
                                    target: {
                                        tagName: e.target.tagName,
                                        id: e.target.id,
                                        className: e.target.className,
                                        name: e.target.name,
                                        type: e.target.type,
                                        value: e.target.value,
                                        checked: e.target.checked,
                                        href: e.target.href,
                                        innerText: e.target.innerText ? e.target.innerText.substring(0, 50) : ''
                                    },
                                    x: e.clientX,
                                    y: e.clientY
                                });
                            }, true);
                        }
                    } catch (frameError) {
                        // Cross-origin iframe - can't access content directly
                        console.log("Could not access iframe content: " + frameError);
                    }
                }
            } catch (e) {
                console.log("Error setting up iframe monitoring: " + e);
            }
            
            // Monitor for alerts, confirms, and prompts
            window._seleniumRecorderOriginalAlert = window.alert;
            window.alert = function(message) {
                window._seleniumRecorderEvents.push({
                    type: 'alert',
                    timestamp: Date.now(),
                    message: message
                });
                return window._seleniumRecorderOriginalAlert.apply(this, arguments);
            };
            
            window._seleniumRecorderOriginalConfirm = window.confirm;
            window.confirm = function(message) {
                var result = window._seleniumRecorderOriginalConfirm.apply(this, arguments);
                window._seleniumRecorderEvents.push({
                    type: 'confirm',
                    timestamp: Date.now(),
                    message: message,
                    result: result
                });
                return result;
            };
            
            window._seleniumRecorderOriginalPrompt = window.prompt;
            window.prompt = function(message, defaultValue) {
                var result = window._seleniumRecorderOriginalPrompt.apply(this, arguments);
                window._seleniumRecorderEvents.push({
                    type: 'prompt',
                    timestamp: Date.now(),
                    message: message,
                    defaultValue: defaultValue,
                    result: result
                });
                return result;
            };
            
            return "Extended listeners injected successfully";
        })();
        """
        
        try:
            result = self.driver.execute_script(script)
            self.logger.info(f"Injected additional listeners: {result}")
        except Exception as e:
            self.logger.error(f"Error injecting additional listeners: {str(e)}")
            
    def _start_event_polling(self) -> None:
        """
        Start polling for events in a separate thread.
        """
        import threading
        
        def polling_thread():
            while self.is_recording:
                try:
                    self._poll_events()
                except Exception as e:
                    self.logger.error(f"Error polling events: {str(e)}")
                time.sleep(self.polling_interval)
                
        thread = threading.Thread(target=polling_thread)
        thread.daemon = True
        thread.start()

    def _poll_events(self) -> None:
        """
        Poll for events from the browser and process them.
        """
        if not self.driver or not self.is_recording:
            return
            
        try:
            # Check for alerts first
            self._check_for_alerts()
            
            # Get events from browser
            success, events, message = self.browser_manager.get_recorded_events()
            
            if not success:
                self.logger.warning(f"Failed to get events: {message}")
                return
                
            if not events:
                return
                
            # Process events
            for event in events:
                self._process_event(event)
                
        except Exception as e:
            self.logger.error(f"Error polling events: {str(e)}")
    
    def _check_for_alerts(self) -> None:
        """
        Check for and handle any browser alerts.
        """
        try:
            alert = self.driver.switch_to.alert
            
            # Alert exists, record it
            alert_text = alert.text
            
            # Accept the alert
            alert.accept()
            
            # Create alert step
            step = {
                'action': 'accept_alert',
                'alert_text': alert_text,
                'timestamp': datetime.now().isoformat(),
                'screenshot': self._take_screenshot()
            }
            
            self._add_step(step)
            
        except NoAlertPresentException:
            # No alert present, continue
            pass
        except Exception as e:
            self.logger.error(f"Error handling alert: {str(e)}")
    
    def _process_event(self, event: Dict[str, Any]) -> None:
        """
        Process a single event and convert it to a step if applicable.
        
        Args:
            event: Event data from browser
        """
        try:
            event_type = event.get('type')
            
            # Skip events that are too close together (debounce)
            current_time = time.time()
            if current_time - self.last_event_time < 0.1:
                self.event_buffer.append(event)
                return
                
            self.last_event_time = current_time
            
            # Process buffered events first
            for buffered_event in self.event_buffer:
                self._process_single_event(buffered_event)
                
            self.event_buffer = []
            
            # Process current event
            self._process_single_event(event)
            
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
    
    def _process_single_event(self, event: Dict[str, Any]) -> None:
        """
        Process a single event and convert it to a step.
        
        Args:
            event: Event data from browser
        """
        event_type = event.get('type')
        
        # Check if we have a handler for this event type
        if event_type in self.action_types:
            handler = self.action_types[event_type]
            handler(event)
        else:
            self.logger.debug(f"No handler for event type: {event_type}")
    
    def _process_click(self, event: Dict[str, Any]) -> None:
        """
        Process a click event.
        
        Args:
            event: Click event data
        """
        try:
            # Check if click is in an iframe
            if event.get('inFrame'):
                self._handle_iframe_navigation(event)
                
            # Find the element
            element = self._find_element_from_event(event)
            if not element:
                self.logger.warning("Could not find element for click event")
                return
                
            # Take screenshot before action
            screenshot = self._take_screenshot()
            
            # Generate locators
            locators = self.locator_engine.generate_locators(element)
            
            # Create step data
            step = {
                'action': 'click',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            # Special handling for different element types
            tag_name = element.tag_name.lower()
            element_type = element.get_attribute('type')
            
            if tag_name == 'input' and element_type in ['checkbox', 'radio']:
                step['action'] = 'check' if element.is_selected() else 'uncheck'
                
            elif tag_name == 'select':
                # This is handled by change event, not click
                return
                
            elif tag_name == 'a':
                step['href'] = element.get_attribute('href')
                
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing click event: {str(e)}")
    
    def _process_double_click(self, event: Dict[str, Any]) -> None:
        """
        Process a double-click event.
        
        Args:
            event: Double-click event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            step = {
                'action': 'double_click',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing double-click event: {str(e)}")
    
    def _process_right_click(self, event: Dict[str, Any]) -> None:
        """
        Process a right-click (context menu) event.
        
        Args:
            event: Right-click event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            step = {
                'action': 'right_click',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing right-click event: {str(e)}")
    
    def _process_hover(self, event: Dict[str, Any]) -> None:
        """
        Process a hover (mouseover) event.
        
        Args:
            event: Hover event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            step = {
                'action': 'hover',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing hover event: {str(e)}")
    
    def _process_change(self, event: Dict[str, Any]) -> None:
        """
        Process a change event (select, checkbox, radio).
        
        Args:
            event: Change event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            tag_name = element.tag_name.lower()
            element_type = element.get_attribute('type')
            
            if tag_name == 'select':
                # Get selected option(s)
                selected_options = []
                for option in element.find_elements(By.TAG_NAME, 'option'):
                    if option.is_selected():
                        selected_options.append({
                            'text': option.text,
                            'value': option.get_attribute('value')
                        })
                
                step = {
                    'action': 'select',
                    'locators': locators,
                    'element_info': self._get_element_info(element),
                    'selected_options': selected_options,
                    'timestamp': datetime.now().isoformat(),
                    'frame_path': self.current_frame_path.copy(),
                    'shadow_path': self.shadow_root_path.copy(),
                    'screenshot': screenshot
                }
                
            elif tag_name == 'input' and element_type in ['checkbox', 'radio']:
                step = {
                    'action': 'check' if element.is_selected() else 'uncheck',
                    'locators': locators,
                    'element_info': self._get_element_info(element),
                    'timestamp': datetime.now().isoformat(),
                    'frame_path': self.current_frame_path.copy(),
                    'shadow_path': self.shadow_root_path.copy(),
                    'screenshot': screenshot
                }
                
            else:
                # Other change events are handled by input event
                return
                
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing change event: {str(e)}")
    def _process_input(self, event: Dict[str, Any]) -> None:
        """
        Process an input event (text input, file upload).
        
        Args:
            event: Input event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            tag_name = element.tag_name.lower()
            element_type = element.get_attribute('type')
            
            # Get current value
            value = element.get_attribute('value')
            
            if tag_name == 'input' and element_type == 'file':
                # File upload - value will be a fake path for security reasons
                # We'll need to handle this specially in the UI
                step = {
                    'action': 'upload_file',
                    'locators': locators,
                    'element_info': self._get_element_info(element),
                    'timestamp': datetime.now().isoformat(),
                    'frame_path': self.current_frame_path.copy(),
                    'shadow_path': self.shadow_root_path.copy(),
                    'screenshot': screenshot
                }
                
            elif tag_name in ['input', 'textarea'] or (tag_name == 'div' and element.get_attribute('contenteditable') == 'true'):
                # Text input
                step = {
                    'action': 'input',
                    'locators': locators,
                    'element_info': self._get_element_info(element),
                    'value': value,
                    'timestamp': datetime.now().isoformat(),
                    'frame_path': self.current_frame_path.copy(),
                    'shadow_path': self.shadow_root_path.copy(),
                    'screenshot': screenshot
                }
                
            else:
                # Other input events
                return
                
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing input event: {str(e)}")
    
    def _process_keydown(self, event: Dict[str, Any]) -> None:
        """
        Process a keydown event for special keys.
        
        Args:
            event: Keydown event data
        """
        try:
            key = event.get('key')
            if not key:
                return
                
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            # Map keys to Selenium Keys constants
            key_mapping = {
                'Enter': 'ENTER',
                'Tab': 'TAB',
                'Escape': 'ESCAPE',
                'ArrowUp': 'ARROW_UP',
                'ArrowDown': 'ARROW_DOWN',
                'ArrowLeft': 'ARROW_LEFT',
                'ArrowRight': 'ARROW_RIGHT',
                'Backspace': 'BACK_SPACE',
                'Delete': 'DELETE',
                'Home': 'HOME',
                'End': 'END',
                'PageUp': 'PAGE_UP',
                'PageDown': 'PAGE_DOWN'
            }
            
            selenium_key = key_mapping.get(key)
            if not selenium_key:
                return
                
            step = {
                'action': 'press_key',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'key': selenium_key,
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing keydown event: {str(e)}")
    
    def _process_drag_start(self, event: Dict[str, Any]) -> None:
        """
        Process a drag start event.
        
        Args:
            event: Drag start event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            # Store the source element for later use in drop event
            self.drag_source = {
                'element': element,
                'locators': self.locator_engine.generate_locators(element),
                'element_info': self._get_element_info(element)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing drag start event: {str(e)}")
    
    def _process_drop(self, event: Dict[str, Any]) -> None:
        """
        Process a drop event.
        
        Args:
            event: Drop event data
        """
        try:
            if not hasattr(self, 'drag_source') or not self.drag_source:
                return
                
            target_element = self._find_element_from_event(event)
            if not target_element:
                return
                
            screenshot = self._take_screenshot()
            target_locators = self.locator_engine.generate_locators(target_element)
            
            step = {
                'action': 'drag_and_drop',
                'source_locators': self.drag_source['locators'],
                'source_element_info': self.drag_source['element_info'],
                'target_locators': target_locators,
                'target_element_info': self._get_element_info(target_element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
            # Clear drag source
            self.drag_source = None
            
        except Exception as e:
            self.logger.error(f"Error processing drop event: {str(e)}")
    
    def _process_select(self, event: Dict[str, Any]) -> None:
        """
        Process a select event.
        
        Args:
            event: Select event data
        """
        # This is handled by the change event
        pass
    
    def _process_submit(self, event: Dict[str, Any]) -> None:
        """
        Process a form submit event.
        
        Args:
            event: Submit event data
        """
        try:
            element = self._find_element_from_event(event)
            if not element:
                return
                
            screenshot = self._take_screenshot()
            locators = self.locator_engine.generate_locators(element)
            
            step = {
                'action': 'submit',
                'locators': locators,
                'element_info': self._get_element_info(element),
                'timestamp': datetime.now().isoformat(),
                'frame_path': self.current_frame_path.copy(),
                'shadow_path': self.shadow_root_path.copy(),
                'screenshot': screenshot
            }
            
            self._add_step(step)
            
        except Exception as e:
            self.logger.error(f"Error processing submit event: {str(e)}")
    
    def _process_focus(self, event: Dict[str, Any]) -> None:
        """
        Process a focus event.
        
        Args:
            event: Focus event data
        """
        # We don't create steps for focus events, but we could use this
        # to track the currently focused element if needed
        pass
    
    def _process_blur(self, event: Dict[str, Any]) -> None:
        """
        Process a blur event.
        
        Args:
            event: Blur event data
        """
        # We don't create steps for blur events, but we could use this
        # to finalize input steps if needed
        pass
    
    def _find_element_from_event(self, event: Dict[str, Any]) -> Optional[WebElement]:
        """
        Find the WebElement corresponding to an event.
        
        Args:
            event: Event data
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            # Handle iframe navigation if needed
            if event.get('inFrame'):
                self._handle_iframe_navigation(event)
                
            # Try to find element by coordinates first
            x = event.get('x')
            y = event.get('y')
            
            if x is not None and y is not None:
                try:
                    element = self.driver.execute_script(
                        "return document.elementFromPoint(arguments[0], arguments[1]);",
                        x, y
                    )
                    if element:
                        return element
                except:
                    pass
                    
            # Fall back to target info
            target = event.get('target', {})
            
            # Try ID first
            element_id = target.get('id')
            if element_id:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    return element
                except NoSuchElementException:
                    pass
                    
            # Try other attributes
            tag_name = target.get('tagName', '').lower()
            if not tag_name:
                return None
                
            # Build XPath based on available attributes
            xpath_parts = [f"//{tag_name}"]
            constraints = []
            
            if target.get('id'):
                constraints.append(f"@id='{target['id']}'")
                
            if target.get('name'):
                constraints.append(f"@name='{target['name']}'")
                
            if target.get('className'):
                classes = target['className'].split()
                for cls in classes:
                    constraints.append(f"contains(@class,'{cls}')")
                    
            if target.get('type'):
                constraints.append(f"@type='{target['type']}'")
                
            if target.get('innerText') and len(target['innerText']) < 50:
                # Escape quotes in text
                text = target['innerText'].replace("'", "\\'")
                constraints.append(f"contains(text(),'{text}')")
                
            # Add constraints to XPath
            if constraints:
                xpath_parts.append("[" + " and ".join(constraints) + "]")
                
            xpath = "".join(xpath_parts)
            
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                return element
            except NoSuchElementException:
                pass
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding element from event: {str(e)}")
            return None
    def _handle_iframe_navigation(self, event: Dict[str, Any]) -> None:
        """
        Handle navigation to an iframe.
        
        Args:
            event: Event data with iframe information
        """
        try:
            # Switch back to default content first
            self.driver.switch_to.default_content()
            self.current_frame_path = []
            
            # Get iframe identifiers
            frame_id = event.get('frameId')
            frame_name = event.get('frameName')
            frame_src = event.get('frameSrc')
            
            # Try to find the iframe
            iframe = None
            
            if frame_id:
                try:
                    iframe = self.driver.find_element(By.ID, frame_id)
                except NoSuchElementException:
                    pass
                    
            if not iframe and frame_name:
                try:
                    iframe = self.driver.find_element(By.NAME, frame_name)
                except NoSuchElementException:
                    pass
                    
            if not iframe and frame_src:
                try:
                    iframe = self.driver.find_element(By.XPATH, f"//iframe[@src='{frame_src}']")
                except NoSuchElementException:
                    pass
                    
            if not iframe:
                # Try to find by index
                iframes = self.driver.find_elements(By.TAG_NAME, 'iframe')
                if iframes:
                    iframe = iframes[0]  # Default to first iframe
                    
            if iframe:
                # Generate locators for the iframe
                iframe_locators = self.locator_engine.generate_locators(iframe)
                
                # Switch to the iframe
                self.driver.switch_to.frame(iframe)
                
                # Update frame path
                self.current_frame_path.append({
                    'locators': iframe_locators,
                    'element_info': self._get_element_info(iframe)
                })
                
                # Create a step for iframe navigation
                step = {
                    'action': 'switch_to_frame',
                    'locators': iframe_locators,
                    'element_info': self._get_element_info(iframe),
                    'timestamp': datetime.now().isoformat(),
                    'frame_path': self.current_frame_path.copy()[:-1],  # Exclude current frame
                    'shadow_path': self.shadow_root_path.copy(),
                    'screenshot': self._take_screenshot()
                }
                
                self._add_step(step)
                
        except Exception as e:
            self.logger.error(f"Error handling iframe navigation: {str(e)}")
            # Reset frame path and switch to default content
            self.current_frame_path = []
            try:
                self.driver.switch_to.default_content()
            except:
                pass
    
    def _get_element_info(self, element: WebElement) -> Dict[str, Any]:
        """
        Get detailed information about an element.
        
        Args:
            element: WebElement to get info for
            
        Returns:
            Dictionary with element information
        """
        try:
            # Get basic attributes
            info = {
                'tag_name': element.tag_name.lower(),
                'id': element.get_attribute('id'),
                'name': element.get_attribute('name'),
                'class': element.get_attribute('class'),
                'type': element.get_attribute('type'),
                'value': element.get_attribute('value'),
                'text': element.text,
                'is_displayed': element.is_displayed(),
                'is_enabled': element.is_enabled()
            }
            
            # Get element dimensions and position
            try:
                rect = element.rect
                info['position'] = {
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height']
                }
            except:
                pass
                
            # Get additional attributes based on element type
            if info['tag_name'] == 'a':
                info['href'] = element.get_attribute('href')
                
            elif info['tag_name'] == 'img':
                info['src'] = element.get_attribute('src')
                info['alt'] = element.get_attribute('alt')
                
            elif info['tag_name'] == 'input' and info['type'] in ['checkbox', 'radio']:
                info['checked'] = element.is_selected()
                
            elif info['tag_name'] == 'select':
                options = []
                for option in element.find_elements(By.TAG_NAME, 'option'):
                    options.append({
                        'text': option.text,
                        'value': option.get_attribute('value'),
                        'selected': option.is_selected()
                    })
                info['options'] = options
                
            # Clean up None values
            info = {k: v for k, v in info.items() if v is not None}
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting element info: {str(e)}")
            return {'tag_name': element.tag_name.lower()}
    
    def _take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot of the current browser window.
        
        Returns:
            Base64-encoded screenshot or None if failed
        """
        if not self.driver or not self.screenshot_manager:
            return None
            
        try:
            # Take screenshot using browser manager
            success, filepath = self.browser_manager.take_screenshot()
            
            if success and self.screenshot_manager:
                # Process and store screenshot
                screenshot_id = self.screenshot_manager.process_screenshot(filepath)
                return screenshot_id
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    def _add_step(self, step: Dict[str, Any]) -> None:
        """
        Add a step to the recorded steps list.
        
        Args:
            step: Step data
        """
        # Add step ID
        step['id'] = len(self.recorded_steps) + 1
        
        # Add step to list
        self.recorded_steps.append(step)
        
        # Call callback if provided
        if self.step_callback:
            try:
                self.step_callback(step)
            except Exception as e:
                self.logger.error(f"Error in step callback: {str(e)}")
                
        self.logger.info(f"Added step: {step['action']}")



