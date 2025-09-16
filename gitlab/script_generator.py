"""
script_generator.py - Script generator for Selenium Recorder

This module converts recorded steps into executable Selenium code.
It supports different frameworks and formats for generating automation scripts.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class ScriptGenerator:
    """
    Generator for creating automation scripts from recorded steps.
    """
    
    def __init__(self):
        """
        Initialize the script generator.
        """
        # Template directories
        self.template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        
        # Framework handlers
        self.framework_handlers = {
            "selenium": self._generate_selenium_script,
            "playwright": self._generate_playwright_script,
            "cypress": self._generate_cypress_script
        }
        
    def generate_python_script(self, steps: List[Dict[str, Any]], options: Dict[str, Any] = None) -> str:
        """
        Generate a Python script from recorded steps.
        
        Args:
            steps: List of recorded steps
            options: Script generation options
            
        Returns:
            Generated script as a string
        """
        if not steps:
            return "# No steps to generate script from"
            
        # Default options
        if options is None:
            options = {}
            
        # Get framework
        framework = options.get("framework", "selenium")
        
        # Call appropriate handler
        handler = self.framework_handlers.get(framework)
        if handler:
            return handler(steps, options)
        else:
            return f"# Unsupported framework: {framework}"
            
    def generate_json(self, steps: List[Dict[str, Any]]) -> str:
        """
        Generate a JSON representation of the recorded steps.
        
        Args:
            steps: List of recorded steps
            
        Returns:
            JSON string
        """
        if not steps:
            return "{}"
            
        # Create JSON data
        data = {
            "version": "1.0",
            "generated": datetime.now().isoformat(),
            "steps": steps
        }
        
        # Convert to JSON string
        return json.dumps(data, indent=2)
        
    def _generate_selenium_script(self, steps: List[Dict[str, Any]], options: Dict[str, Any]) -> str:
        """
        Generate a Selenium script from recorded steps.
        
        Args:
            steps: List of recorded steps
            options: Script generation options
            
        Returns:
            Generated Selenium script
        """
        # Get options
        include_comments = options.get("include_comments", True)
        include_timestamps = options.get("include_timestamps", False)
        use_explicit_waits = options.get("use_explicit_waits", True)
        generate_assertions = options.get("generate_assertions", False)
        test_framework = options.get("test_framework", "pytest")
        
        # Build script
        lines = []
        
        # Add imports
        lines.extend(self._generate_selenium_imports(test_framework))
        lines.append("")
        
        # Add test class or function
        if test_framework == "unittest":
            lines.extend(self._generate_unittest_class())
        else:
            lines.extend(self._generate_pytest_function())
            
        # Add setup code
        lines.extend(self._generate_selenium_setup(test_framework))
        
        # Process steps
        for step in steps:
            # Add step comment
            if include_comments:
                comment = f"# Step {step.get('id')}: {step.get('action')}"
                
                # Add target description
                target_desc = self._get_target_description(step)
                if target_desc:
                    comment += f" {target_desc}"
                    
                # Add timestamp
                if include_timestamps and "timestamp" in step:
                    try:
                        dt = datetime.fromisoformat(step["timestamp"])
                        comment += f" ({dt.strftime('%H:%M:%S')})"
                    except:
                        pass
                        
                lines.append(comment)
                
            # Generate step code
            step_code = self._generate_selenium_step_code(step, use_explicit_waits)
            lines.extend(step_code)
            
            # Add assertion if needed
            if generate_assertions:
                assertion_code = self._generate_selenium_assertion(step, test_framework)
                if assertion_code:
                    lines.extend(assertion_code)
                    
            # Add blank line after step
            lines.append("")
            
        # Add teardown code
        lines.extend(self._generate_selenium_teardown(test_framework))
        
        # Join lines
        return "\n".join(lines)
        
    def _generate_selenium_imports(self, test_framework: str) -> List[str]:
        """
        Generate import statements for Selenium script.
        
        Args:
            test_framework: Test framework to use
            
        Returns:
            List of import statements
        """
        imports = [
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.common.keys import Keys",
            "from selenium.webdriver.common.action_chains import ActionChains",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "from selenium.webdriver.support.ui import Select",
            "import time"
        ]
        
        # Add test framework imports
        if test_framework == "unittest":
            imports.append("import unittest")
        elif test_framework == "pytest":
            imports.append("import pytest")
            
        return imports
        
    def _generate_unittest_class(self) -> List[str]:
        """
        Generate unittest class definition.
        
        Returns:
            List of code lines
        """
        return [
            "class SeleniumTest(unittest.TestCase):",
            ""
        ]
        
    def _generate_pytest_function(self) -> List[str]:
        """
        Generate pytest function definition.
        
        Returns:
            List of code lines
        """
        return [
            "def test_selenium_script():",
            ""
        ]
        
    def _generate_selenium_setup(self, test_framework: str) -> List[str]:
        """
        Generate setup code for Selenium script.
        
        Args:
            test_framework: Test framework to use
            
        Returns:
            List of code lines
        """
        indent = "    " if test_framework == "unittest" else ""
        
        setup = [
            f"{indent}# Set up the driver",
            f"{indent}driver = webdriver.Chrome()",
            f"{indent}driver.implicitly_wait(10)",
            f"{indent}driver.maximize_window()",
            f"{indent}"
        ]
        
        return setup
        
    def _generate_selenium_teardown(self, test_framework: str) -> List[str]:
        """
        Generate teardown code for Selenium script.
        
        Args:
            test_framework: Test framework to use
            
        Returns:
            List of code lines
        """
        indent = "    " if test_framework == "unittest" else ""
        
        teardown = [
            f"{indent}# Clean up",
            f"{indent}driver.quit()"
        ]
        
        # Add main block for unittest
        if test_framework == "unittest":
            teardown.extend([
                "",
                "if __name__ == '__main__':",
                "    unittest.main()"
            ])
            
        return teardown

    def _generate_selenium_step_code(self, step: Dict[str, Any], use_explicit_waits: bool) -> List[str]:
        """
        Generate code for a Selenium step.
        
        Args:
            step: Step data
            use_explicit_waits: Whether to use explicit waits
            
        Returns:
            List of code lines
        """
        action = step.get("action", "")
        indent = "    " if "unittest" in step.get("test_framework", "") else ""
        
        if action == "navigate":
            url = step.get("url", "")
            return [f"{indent}driver.get(\"{url}\")"]
            
        elif action == "click":
            locator = self._get_selenium_locator(step)
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}element.click()"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}element.click()"
                ]
                
        elif action == "double_click":
            locator = self._get_selenium_locator(step)
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}ActionChains(driver).double_click(element).perform()"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}ActionChains(driver).double_click(element).perform()"
                ]
                
        elif action == "right_click":
            locator = self._get_selenium_locator(step)
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}ActionChains(driver).context_click(element).perform()"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}ActionChains(driver).context_click(element).perform()"
                ]
                
        elif action == "hover":
            locator = self._get_selenium_locator(step)
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.visibility_of_element_located({locator})",
                    f"{indent})",
                    f"{indent}ActionChains(driver).move_to_element(element).perform()"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}ActionChains(driver).move_to_element(element).perform()"
                ]
                
        elif action == "input":
            locator = self._get_selenium_locator(step)
            value = step.get("value", "")
            # Escape quotes in value
            value = value.replace('"', '\\"')
            
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}element.clear()",
                    f"{indent}element.send_keys(\"{value}\")"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}element.clear()",
                    f"{indent}element.send_keys(\"{value}\")"
                ]
                
        elif action == "select":
            locator = self._get_selenium_locator(step)
            selected_options = step.get("selected_options", [])
            
            lines = []
            if use_explicit_waits:
                lines.extend([
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}select = Select(element)"
                ])
            else:
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}select = Select(element)"
                ])
                
            for option in selected_options:
                value = option.get("value")
                text = option.get("text")
                
                if value:
                    # Escape quotes in value
                    value = value.replace('"', '\\"')
                    lines.append(f"{indent}select.select_by_value(\"{value}\")")
                elif text:
                    # Escape quotes in text
                    text = text.replace('"', '\\"')
                    lines.append(f"{indent}select.select_by_visible_text(\"{text}\")")
                    
            return lines
            
        elif action == "check" or action == "uncheck":
            locator = self._get_selenium_locator(step)
            
            if use_explicit_waits:
                lines = [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})"
                ]
            else:
                lines = [
                    f"{indent}element = driver.find_element({locator})"
                ]
                
            if action == "check":
                lines.append(f"{indent}if not element.is_selected():")
                lines.append(f"{indent}    element.click()")
            else:  # uncheck
                lines.append(f"{indent}if element.is_selected():")
                lines.append(f"{indent}    element.click()")
                
            return lines
            
        elif action == "press_key":
            locator = self._get_selenium_locator(step)
            key = step.get("key", "")
            
            # Map key string to Keys constant
            key_mapping = {
                "ENTER": "Keys.ENTER",
                "TAB": "Keys.TAB",
                "ESCAPE": "Keys.ESCAPE",
                "ARROW_UP": "Keys.UP",
                "ARROW_DOWN": "Keys.DOWN",
                "ARROW_LEFT": "Keys.LEFT",
                "ARROW_RIGHT": "Keys.RIGHT",
                "BACK_SPACE": "Keys.BACK_SPACE",
                "DELETE": "Keys.DELETE",
                "HOME": "Keys.HOME",
                "END": "Keys.END",
                "PAGE_UP": "Keys.PAGE_UP",
                "PAGE_DOWN": "Keys.PAGE_DOWN"
            }
            
            selenium_key = key_mapping.get(key, f'"{key}"')
            
            if use_explicit_waits:
                return [
                    f"{indent}element = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({locator})",
                    f"{indent})",
                    f"{indent}element.send_keys({selenium_key})"
                ]
            else:
                return [
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}element.send_keys({selenium_key})"
                ]
                
        elif action == "drag_and_drop":
            source_locator = self._get_selenium_locator(step, "source_locators")
            target_locator = self._get_selenium_locator(step, "target_locators")
            
            if use_explicit_waits:
                return [
                    f"{indent}source = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({source_locator})",
                    f"{indent})",
                    f"{indent}target = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.element_to_be_clickable({target_locator})",
                    f"{indent})",
                    f"{indent}ActionChains(driver).drag_and_drop(source, target).perform()"
                ]
            else:
                return [
                    f"{indent}source = driver.find_element({source_locator})",
                    f"{indent}target = driver.find_element({target_locator})",
                    f"{indent}ActionChains(driver).drag_and_drop(source, target).perform()"
                ]
                
        elif action == "switch_to_frame":
            locator = self._get_selenium_locator(step)
            
            if use_explicit_waits:
                return [
                    f"{indent}frame = WebDriverWait(driver, 10).until(",
                    f"{indent}    EC.frame_to_be_available_and_switch_to_it({locator})",
                    f"{indent})"
                ]
            else:
                return [
                    f"{indent}frame = driver.find_element({locator})",
                    f"{indent}driver.switch_to.frame(frame)"
                ]
                
        elif action == "accept_alert":
            return [
                f"{indent}# Wait for alert to be present",
                f"{indent}alert = WebDriverWait(driver, 10).until(EC.alert_is_present())",
                f"{indent}alert.accept()"
            ]
            
        else:
            return [f"{indent}# Unsupported action: {action}"]

    def _generate_selenium_assertion(self, step: Dict[str, Any], test_framework: str) -> List[str]:
        """
        Generate assertion code for a Selenium step.
        
        Args:
            step: Step data
            test_framework: Test framework to use
            
        Returns:
            List of code lines with assertions
        """
        action = step.get("action", "")
        indent = "    " if test_framework == "unittest" else ""
        
        # Only generate assertions for certain actions
        if action not in ["navigate", "input", "select", "check", "uncheck"]:
            return []
            
        if action == "navigate":
            url = step.get("url", "")
            if test_framework == "unittest":
                return [f"{indent}self.assertEqual(driver.current_url, \"{url}\")"]
            else:
                return [f"{indent}assert driver.current_url == \"{url}\""]
                
        elif action == "input":
            locator = self._get_selenium_locator(step)
            value = step.get("value", "")
            # Escape quotes in value
            value = value.replace('"', '\\"')
            
            lines = [f"{indent}# Verify input value"]
            if test_framework == "unittest":
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}self.assertEqual(element.get_attribute(\"value\"), \"{value}\")"
                ])
            else:
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}assert element.get_attribute(\"value\") == \"{value}\""
                ])
                
            return lines
            
        elif action == "select":
            locator = self._get_selenium_locator(step)
            selected_options = step.get("selected_options", [])
            
            if not selected_options:
                return []
                
            lines = [f"{indent}# Verify selected option"]
            lines.extend([
                f"{indent}element = driver.find_element({locator})",
                f"{indent}select = Select(element)"
            ])
            
            # Get first selected option for assertion
            option = selected_options[0]
            text = option.get("text")
            
            if text:
                # Escape quotes in text
                text = text.replace('"', '\\"')
                if test_framework == "unittest":
                    lines.append(f"{indent}self.assertEqual(select.first_selected_option.text, \"{text}\")")
                else:
                    lines.append(f"{indent}assert select.first_selected_option.text == \"{text}\"")
                    
            return lines
            
        elif action == "check":
            locator = self._get_selenium_locator(step)
            
            lines = [f"{indent}# Verify checkbox is checked"]
            if test_framework == "unittest":
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}self.assertTrue(element.is_selected())"
                ])
            else:
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}assert element.is_selected()"
                ])
                
            return lines
            
        elif action == "uncheck":
            locator = self._get_selenium_locator(step)
            
            lines = [f"{indent}# Verify checkbox is unchecked"]
            if test_framework == "unittest":
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}self.assertFalse(element.is_selected())"
                ])
            else:
                lines.extend([
                    f"{indent}element = driver.find_element({locator})",
                    f"{indent}assert not element.is_selected()"
                ])
                
            return lines
            
        return []
        
    def _get_selenium_locator(self, step: Dict[str, Any], locators_key: str = "locators") -> str:
        """
        Get the best Selenium locator for a step.
        
        Args:
            step: Step data
            locators_key: Key for locators in step data
            
        Returns:
            Selenium locator string
        """
        locators = step.get(locators_key, {})
        
        # Try ID locator (most reliable)
        if locators.get("id"):
            return f"By.ID, \"{locators['id']}\""
            
        # Try name locator
        elif locators.get("name"):
            return f"By.NAME, \"{locators['name']}\""
            
        # Try CSS selector
        elif locators.get("css"):
            return f"By.CSS_SELECTOR, \"{locators['css']}\""
            
        # Try XPath
        elif locators.get("xpath", {}).get("id_based"):
            return f"By.XPATH, \"{locators['xpath']['id_based']}\""
        elif locators.get("xpath", {}).get("attributes"):
            return f"By.XPATH, \"{locators['xpath']['attributes']}\""
        elif locators.get("xpath", {}).get("text"):
            return f"By.XPATH, \"{locators['xpath']['text']}\""
        elif locators.get("xpath", {}).get("full"):
            return f"By.XPATH, \"{locators['xpath']['full']}\""
            
        # Fallback to link text
        elif locators.get("link_text"):
            return f"By.LINK_TEXT, \"{locators['link_text']}\""
            
        # Last resort: use a generic XPath
        return "By.XPATH, \"//body\""
        
    def _get_target_description(self, step: Dict[str, Any]) -> str:
        """
        Get a human-readable description of the step target.
        
        Args:
            step: Step data
            
        Returns:
            Target description
        """
        action = step.get("action", "")
        
        if action == "navigate":
            return step.get("url", "")
            
        elif action == "accept_alert":
            return step.get("alert_text", "Alert")
            
        elif action in ["click", "double_click", "right_click", "hover", "input", "select", "check", "uncheck", "press_key"]:
            # Get element info
            element_info = step.get("element_info", {})
            
            # Build description
            parts = []
            
            # Add tag name
            tag_name = element_info.get("tag_name", "").upper()
            if tag_name:
                parts.append(tag_name)
                
            # Add ID
            element_id = element_info.get("id")
            if element_id:
                parts.append(f"id='{element_id}'")
                
            # Add name
            name = element_info.get("name")
            if name:
                parts.append(f"name='{name}'")
                
            # Add text
            text = element_info.get("text")
            if text and len(text) < 30:
                parts.append(f"text='{text}'")
                
            # Fallback to locator
            if not parts and "locators" in step:
                locators = step["locators"]
                
                # Try ID locator
                if locators.get("id"):
                    parts.append(f"id='{locators['id']}'")
                    
                # Try XPath
                elif locators.get("xpath", {}).get("id_based"):
                    parts.append(locators["xpath"]["id_based"])
                    
                # Try CSS
                elif locators.get("css"):
                    parts.append(locators["css"])
                    
            return " ".join(parts)
            
        return ""
        
    def _generate_playwright_script(self, steps: List[Dict[str, Any]], options: Dict[str, Any]) -> str:
        """
        Generate a Playwright script from recorded steps.
        
        Args:
            steps: List of recorded steps
            options: Script generation options
            
        Returns:
            Generated Playwright script
        """
        # This is a placeholder for Playwright script generation
        # The implementation would be similar to Selenium but with Playwright-specific code
        return "# Playwright script generation not yet implemented"
        
    def _generate_cypress_script(self, steps: List[Dict[str, Any]], options: Dict[str, Any]) -> str:
        """
        Generate a Cypress script from recorded steps.
        
        Args:
            steps: List of recorded steps
            options: Script generation options
            
        Returns:
            Generated Cypress script
        """
        # This is a placeholder for Cypress script generation
        # The implementation would be similar to Selenium but with Cypress-specific code
        return "// Cypress script generation not yet implemented"
