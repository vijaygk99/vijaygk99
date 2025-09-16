"""
locator_engine.py - Element locator strategies for Selenium Recorder

This module provides robust element identification with multiple fallback strategies,
prioritizing absolute XPath for maximum reliability while offering alternative locators
for better readability and maintenance.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException, 
    NoSuchElementException,
    JavascriptException
)

class LocatorEngine:
    """
    Generates and validates multiple locator strategies for web elements
    with a focus on robustness and reliability.
    """
    
    def __init__(self, driver: Optional[WebDriver] = None):
        """
        Initialize the locator engine.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.logger = logging.getLogger(__name__)
        self.driver = driver
        
    def set_driver(self, driver: WebDriver) -> None:
        """
        Set the WebDriver instance for the locator engine.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver

    def generate_locators(self, element: WebElement) -> Dict[str, Any]:
        """
        Generate multiple locator strategies for a given element.
        
        Args:
            element: WebElement to generate locators for
            
        Returns:
            Dictionary containing various locator strategies
        """
        if not self.driver:
            raise ValueError("WebDriver not set in LocatorEngine")
            
        locators = {
            "xpath": {
                "absolute": None,
                "relative": None,
                "id_based": None,
                "text_based": None,
                "attributes": None
            },
            "css": None,
            "id": None,
            "name": None,
            "class_name": None,
            "tag_name": None,
            "link_text": None,
            "accessibility": None,
            "javascript": None
        }
        
        try:
            # Generate all locator types
            locators["xpath"]["absolute"] = self._generate_absolute_xpath(element)
            locators["xpath"]["relative"] = self._generate_relative_xpath(element)
            
            # Get element attributes for other locator types
            attributes = self._get_element_attributes(element)
            
            # ID-based locators
            if attributes.get("id"):
                locators["id"] = attributes["id"]
                locators["xpath"]["id_based"] = f"//*[@id='{attributes['id']}']"
                locators["css"] = f"#{attributes['id']}"
                
            # Name-based locators
            if attributes.get("name"):
                locators["name"] = attributes["name"]
                
            # Class-based locators
            if attributes.get("class"):
                locators["class_name"] = attributes["class"]
                
            # Tag-based locators
            if attributes.get("tagName"):
                locators["tag_name"] = attributes["tagName"].lower()
                
            # Link text for anchor tags
            if attributes.get("tagName") == "A" and attributes.get("innerText"):
                locators["link_text"] = attributes["innerText"]
                locators["xpath"]["text_based"] = f"//a[contains(text(),'{attributes['innerText']}')]"
                
            # Attribute-based XPath
            locators["xpath"]["attributes"] = self._generate_attributes_xpath(element, attributes)
            
            # Accessibility locators
            if attributes.get("aria-label"):
                locators["accessibility"] = attributes["aria-label"]
                
            # JavaScript locator (for shadow DOM)
            if self._is_in_shadow_dom(element):
                locators["javascript"] = self._generate_shadow_dom_js(element)
                
            # Validate and rank locators
            self._validate_and_rank_locators(locators)
            
            return locators
            
        except StaleElementReferenceException:
            self.logger.warning("Element became stale during locator generation")
            # Return at least the absolute XPath if we have it
            if locators["xpath"]["absolute"]:
                return locators
            raise
            
        except Exception as e:
            self.logger.error(f"Error generating locators: {str(e)}")
            # Return any locators we managed to generate
            if locators["xpath"]["absolute"]:
                return locators
            raise
    
    def find_element_with_locators(self, locators: Dict[str, Any]) -> Optional[WebElement]:
        """
        Find an element using the provided locators, trying multiple strategies.
        
        Args:
            locators: Dictionary of locator strategies
            
        Returns:
            WebElement if found, None otherwise
        """
        if not self.driver:
            raise ValueError("WebDriver not set in LocatorEngine")
            
        # Try locators in order of reliability
        try:
            # Try ID first (fastest and most reliable if available)
            if locators.get("id"):
                try:
                    element = self.driver.find_element("id", locators["id"])
                    return element
                except NoSuchElementException:
                    pass
                    
            # Try absolute XPath (most robust)
            if locators["xpath"].get("absolute"):
                try:
                    element = self.driver.find_element("xpath", locators["xpath"]["absolute"])
                    return element
                except NoSuchElementException:
                    pass
                    
            # Try CSS selector
            if locators.get("css"):
                try:
                    element = self.driver.find_element("css selector", locators["css"])
                    return element
                except NoSuchElementException:
                    pass
                    
            # Try other XPath strategies
            for xpath_type in ["id_based", "attributes", "text_based", "relative"]:
                if locators["xpath"].get(xpath_type):
                    try:
                        element = self.driver.find_element("xpath", locators["xpath"][xpath_type])
                        return element
                    except NoSuchElementException:
                        pass
                        
            # Try JavaScript for shadow DOM
            if locators.get("javascript"):
                try:
                    element = self.driver.execute_script(locators["javascript"])
                    return element
                except JavascriptException:
                    pass
                    
            # Try remaining locator types
            for locator_type in ["name", "class_name", "tag_name", "link_text"]:
                if locators.get(locator_type):
                    try:
                        element = self.driver.find_element(locator_type.replace("_", " "), locators[locator_type])
                        return element
                    except NoSuchElementException:
                        pass
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding element with locators: {str(e)}")
            return None
    def _generate_absolute_xpath(self, element: WebElement) -> str:
        """
        Generate absolute XPath for an element.
        
        Args:
            element: WebElement to generate XPath for
            
        Returns:
            Absolute XPath string
        """
        try:
            # Use JavaScript to generate absolute XPath
            script = """
            function getAbsoluteXPath(element) {
                if (element.id !== '') {
                    return '//*[@id="' + element.id + '"]';
                }
                
                var paths = [];
                
                // Use the element to get to the root (document)
                for (; element && element.nodeType === Node.ELEMENT_NODE; 
                     element = element.parentNode) {
                    var index = 0;
                    var hasFollowingSiblings = false;
                    
                    // Count preceding siblings with same tag name
                    for (var sibling = element.previousSibling; sibling; 
                         sibling = sibling.previousSibling) {
                        if (sibling.nodeType === Node.DOCUMENT_TYPE_NODE) {
                            continue;
                        }
                        if (sibling.nodeName === element.nodeName) {
                            index++;
                        }
                    }
                    
                    // Check if there are following siblings with same tag name
                    for (var sibling = element.nextSibling; sibling && !hasFollowingSiblings; 
                         sibling = sibling.nextSibling) {
                        if (sibling.nodeName === element.nodeName) {
                            hasFollowingSiblings = true;
                        }
                    }
                    
                    var tagName = element.nodeName.toLowerCase();
                    var pathIndex = (index || hasFollowingSiblings) ? 
                                   '[' + (index + 1) + ']' : '';
                    paths.unshift(tagName + pathIndex);
                }
                
                return '/' + paths.join('/');
            }
            return getAbsoluteXPath(arguments[0]);
            """
            
            xpath = self.driver.execute_script(script, element)
            return xpath
            
        except Exception as e:
            self.logger.error(f"Error generating absolute XPath: {str(e)}")
            
            # Fallback method if JavaScript fails
            try:
                from selenium.webdriver.common.by import By
                
                # Get element tag
                tag_name = element.tag_name
                
                # Try to find a unique attribute
                for attr in ["id", "name", "class", "title", "aria-label"]:
                    value = element.get_attribute(attr)
                    if value:
                        # Test if this attribute is unique
                        elements = self.driver.find_elements(By.XPATH, f"//{tag_name}[@{attr}='{value}']")
                        if len(elements) == 1:
                            return f"//{tag_name}[@{attr}='{value}']"
                
                # If no unique attribute, use position-based XPath
                parent = element.find_element(By.XPATH, "..")
                siblings = parent.find_elements(By.XPATH, f"./{tag_name}")
                position = siblings.index(element) + 1
                
                # Get parent's XPath
                parent_xpath = self._generate_absolute_xpath(parent)
                return f"{parent_xpath}/{tag_name}[{position}]"
                
            except Exception as inner_e:
                self.logger.error(f"Fallback XPath generation failed: {str(inner_e)}")
                return f"//body//*[contains(text(), '{element.text[:20]}')]" if element.text else "//body/*"
    
    def _generate_relative_xpath(self, element: WebElement) -> str:
        """
        Generate a relative XPath that's more readable but still robust.
        
        Args:
            element: WebElement to generate XPath for
            
        Returns:
            Relative XPath string
        """
        try:
            # Get element attributes
            attributes = self._get_element_attributes(element)
            tag_name = attributes.get("tagName", "").lower()
            
            if not tag_name:
                return None
                
            # Try to create a relative XPath based on key attributes
            xpath_parts = []
            
            # Add tag
            xpath_parts.append(f"//{tag_name}")
            
            # Add constraints based on available attributes
            constraints = []
            
            if attributes.get("id"):
                constraints.append(f"@id='{attributes['id']}'")
                
            if attributes.get("name"):
                constraints.append(f"@name='{attributes['name']}'")
                
            if attributes.get("class"):
                # Handle multiple classes
                classes = attributes["class"].split()
                for cls in classes:
                    constraints.append(f"contains(@class,'{cls}')")
                    
            if attributes.get("type"):
                constraints.append(f"@type='{attributes['type']}'")
                
            if attributes.get("innerText") and len(attributes["innerText"]) < 50:
                # Escape quotes in text
                text = attributes["innerText"].replace("'", "\\'")
                constraints.append(f"contains(text(),'{text}')")
                
            # Add constraints to XPath
            if constraints:
                xpath_parts.append("[" + " and ".join(constraints) + "]")
                
            return "".join(xpath_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating relative XPath: {str(e)}")
            return None
    def _generate_attributes_xpath(self, element: WebElement, attributes: Dict[str, str]) -> str:
        """
        Generate an XPath based on multiple attributes for robustness.
        
        Args:
            element: WebElement to generate XPath for
            attributes: Dictionary of element attributes
            
        Returns:
            Attributes-based XPath string
        """
        try:
            tag_name = attributes.get("tagName", "").lower()
            
            if not tag_name:
                return None
                
            # Start with tag name
            xpath = f"//{tag_name}"
            
            # Add attribute constraints
            constraints = []
            
            # Priority attributes
            for attr in ["id", "name", "type", "role", "aria-label"]:
                if attributes.get(attr):
                    constraints.append(f"@{attr}='{attributes[attr]}'")
                    
            # Add data attributes
            for attr, value in attributes.items():
                if attr.startswith("data-") and value:
                    constraints.append(f"@{attr}='{value}'")
                    
            # Add position if we have a parent
            try:
                parent = element.find_element("xpath", "..")
                siblings = parent.find_elements("xpath", f"./{tag_name}")
                if len(siblings) > 1:
                    position = siblings.index(element) + 1
                    constraints.append(f"position()={position}")
            except:
                pass
                
            # Add constraints to XPath
            if constraints:
                xpath += "[" + " and ".join(constraints) + "]"
                
            return xpath
            
        except Exception as e:
            self.logger.error(f"Error generating attributes XPath: {str(e)}")
            return None
    
    def _get_element_attributes(self, element: WebElement) -> Dict[str, str]:
        """
        Get all relevant attributes of an element.
        
        Args:
            element: WebElement to get attributes for
            
        Returns:
            Dictionary of element attributes
        """
        try:
            # Use JavaScript to get all attributes
            script = """
            function getElementAttributes(element) {
                var attributes = {};
                
                // Get standard properties
                attributes['tagName'] = element.tagName;
                attributes['innerText'] = element.innerText ? 
                                         element.innerText.substring(0, 100) : '';
                attributes['textContent'] = element.textContent ? 
                                           element.textContent.substring(0, 100) : '';
                attributes['className'] = element.className;
                attributes['id'] = element.id;
                attributes['name'] = element.name;
                attributes['type'] = element.type;
                attributes['value'] = element.value;
                attributes['href'] = element.href;
                attributes['src'] = element.src;
                attributes['alt'] = element.alt;
                attributes['title'] = element.title;
                attributes['class'] = element.getAttribute('class');
                
                // Get all attributes
                var attrs = element.attributes;
                for (var i = 0; i < attrs.length; i++) {
                    attributes[attrs[i].name] = attrs[i].value;
                }
                
                // Get computed styles that might be useful for identification
                var style = window.getComputedStyle(element);
                attributes['width'] = style.width;
                attributes['height'] = style.height;
                attributes['display'] = style.display;
                attributes['position'] = style.position;
                
                return attributes;
            }
            return getElementAttributes(arguments[0]);
            """
            
            attributes = self.driver.execute_script(script, element)
            
            # Clean up attributes (remove None, empty strings, etc.)
            return {k: v for k, v in attributes.items() if v}
            
        except Exception as e:
            self.logger.error(f"Error getting element attributes: {str(e)}")
            
            # Fallback to getting attributes individually
            try:
                attributes = {
                    "tagName": element.tag_name.upper(),
                    "id": element.get_attribute("id"),
                    "name": element.get_attribute("name"),
                    "class": element.get_attribute("class"),
                    "type": element.get_attribute("type"),
                    "value": element.get_attribute("value"),
                    "innerText": element.text
                }
                
                # Clean up attributes
                return {k: v for k, v in attributes.items() if v}
                
            except:
                # Return minimal attributes
                return {"tagName": element.tag_name.upper()}
    def _is_in_shadow_dom(self, element: WebElement) -> bool:
        """
        Check if an element is inside a shadow DOM.
        
        Args:
            element: WebElement to check
            
        Returns:
            True if element is in shadow DOM, False otherwise
        """
        try:
            script = """
            function isInShadowDOM(element) {
                let node = element;
                while (node) {
                    if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE && node.host) {
                        return true;
                    }
                    node = node.parentNode;
                }
                return false;
            }
            return isInShadowDOM(arguments[0]);
            """
            
            return self.driver.execute_script(script, element)
            
        except Exception as e:
            self.logger.error(f"Error checking if element is in shadow DOM: {str(e)}")
            return False
    
    def _generate_shadow_dom_js(self, element: WebElement) -> str:
        """
        Generate JavaScript to access an element in shadow DOM.
        
        Args:
            element: WebElement in shadow DOM
            
        Returns:
            JavaScript code to access the element
        """
        try:
            script = """
            function generateShadowPath(element) {
                let path = [];
                let node = element;
                
                // Traverse up to find all shadow roots
                while (node) {
                    let shadowRoot = null;
                    let host = null;
                    
                    // Check if we're in a shadow root
                    if (node.nodeType === Node.DOCUMENT_FRAGMENT_NODE && node.host) {
                        shadowRoot = node;
                        host = node.host;
                        path.unshift({
                            type: 'shadow',
                            host: {
                                tag: host.tagName.toLowerCase(),
                                id: host.id,
                                className: host.className,
                                attributes: {}
                            }
                        });
                        
                        // Get attributes of host
                        for (let i = 0; i < host.attributes.length; i++) {
                            let attr = host.attributes[i];
                            path[0].host.attributes[attr.name] = attr.value;
                        }
                        
                        node = host;
                        continue;
                    }
                    
                    // Regular DOM traversal
                    if (node === element || path.length > 0) {
                        // Only add to path once we've found our element or a shadow root
                        let elementInfo = {
                            type: 'element',
                            tag: node.tagName.toLowerCase(),
                            id: node.id,
                            className: node.className,
                            innerText: node.innerText ? node.innerText.substring(0, 50) : '',
                            attributes: {},
                            index: 0
                        };
                        
                        // Get attributes
                        for (let i = 0; i < node.attributes.length; i++) {
                            let attr = node.attributes[i];
                            elementInfo.attributes[attr.name] = attr.value;
                        }
                        
                        // Get index among siblings
                        if (node.parentNode) {
                            let siblings = Array.from(node.parentNode.children)
                                .filter(n => n.tagName === node.tagName);
                            elementInfo.index = siblings.indexOf(node);
                        }
                        
                        path.unshift(elementInfo);
                    }
                    
                    node = node.parentNode;
                    if (!node || node.nodeType === Node.DOCUMENT_NODE) {
                        break;
                    }
                }
                
                return path;
            }
            
            return generateShadowPath(arguments[0]);
            """
            
            shadow_path = self.driver.execute_script(script, element)
            
            # Generate JavaScript to access the element
            js_code = "return (function() {\n"
            js_code += "  let node = document;\n"
            
            for step in shadow_path:
                if step["type"] == "shadow":
                    # Find shadow host
                    host_locator = self._get_js_locator(step["host"])
                    js_code += f"  node = {host_locator};\n"
                    js_code += "  node = node.shadowRoot;\n"
                else:
                    # Find element in current context
                    element_locator = self._get_js_locator(step)
                    js_code += f"  node = {element_locator};\n"
            
            js_code += "  return node;\n"
            js_code += "})();"
            
            return js_code
            
        except Exception as e:
            self.logger.error(f"Error generating shadow DOM JavaScript: {str(e)}")
            return None
    
    def _get_js_locator(self, element_info: Dict[str, Any]) -> str:
        """
        Generate JavaScript code to locate an element.
        
        Args:
            element_info: Dictionary with element information
            
        Returns:
            JavaScript code to locate the element
        """
        tag = element_info["tag"]
        
        # Try ID first
        if element_info["id"]:
            return f"document.getElementById('{element_info['id']}')"
        
        # Try other attributes
        selectors = []
        
        if tag:
            selectors.append(tag)
            
        for attr, value in element_info.get("attributes", {}).items():
            if attr in ["id", "class", "className"]:
                continue
            selectors.append(f"[{attr}='{value}']")
            
        if element_info.get("className"):
            classes = element_info["className"].split()
            for cls in classes:
                selectors.append(f".{cls}")
                
        selector = "".join(selectors)
        
        # Use querySelector with index if needed
        if element_info.get("index", 0) > 0:
            return f"Array.from(node.querySelectorAll('{selector}'))[{element_info['index']}]"
        else:
            return f"node.querySelector('{selector}')"
    
    def _validate_and_rank_locators(self, locators: Dict[str, Any]) -> None:
        """
        Validate locators and rank them by reliability.
        
        Args:
            locators: Dictionary of locator strategies to validate
        """
        if not self.driver:
            return
            
        # Skip validation if we don't have any locators
        if not any(locators.values()):
            return
            
        try:
            # Test each locator and count matching elements
            locator_counts = {}
            
            # Test ID
            if locators.get("id"):
                try:
                    elements = self.driver.find_elements("id", locators["id"])
                    locator_counts["id"] = len(elements)
                except:
                    locator_counts["id"] = 0
                    
            # Test XPath strategies
            for xpath_type, xpath in locators["xpath"].items():
                if xpath:
                    try:
                        elements = self.driver.find_elements("xpath", xpath)
                        locator_counts[f"xpath_{xpath_type}"] = len(elements)
                    except:
                        locator_counts[f"xpath_{xpath_type}"] = 0
                        
            # Test CSS
            if locators.get("css"):
                try:
                    elements = self.driver.find_elements("css selector", locators["css"])
                    locator_counts["css"] = len(elements)
                except:
                    locator_counts["css"] = 0
                    
            # Add reliability score to each locator
            locators["_reliability"] = {}
            
            for locator_type, count in locator_counts.items():
                # Ideal locator matches exactly one element
                if count == 1:
                    locators["_reliability"][locator_type] = 1.0
                elif count == 0:
                    locators["_reliability"][locator_type] = 0.0
                else:
                    # More matches = less reliable
                    locators["_reliability"][locator_type] = 1.0 / count
                    
        except Exception as e:
            self.logger.error(f"Error validating locators: {str(e)}")

