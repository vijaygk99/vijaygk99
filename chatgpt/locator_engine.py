# app/locator_engine.py

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Optional
import time

class LocatorEngine:
    """
    Generate robust locators for web elements.
    Supports dynamic IDs, XPath fallback, ancestor/descendant traversal, shadow DOM.
    """
    def __init__(self, driver):
        self.driver = driver

    def get_locator(self, element) -> dict:
        """
        Generate a locator dictionary for a given WebElement.
        Returns: {'by': By.XPATH/By.ID/By.CSS_SELECTOR, 'value': locator_string}
        """
        if not element:
            return {}

        # Try ID first
        elem_id = element.get_attribute("id")
        if elem_id and self._is_unique(By.ID, elem_id):
            return {"by": By.ID, "value": elem_id}

        # Try name
        elem_name = element.get_attribute("name")
        if elem_name and self._is_unique(By.NAME, elem_name):
            return {"by": By.NAME, "value": elem_name}

        # Try CSS classes
        elem_class = element.get_attribute("class")
        if elem_class:
            css = f".{'.'.join(elem_class.split())}"
            if self._is_unique(By.CSS_SELECTOR, css):
                return {"by": By.CSS_SELECTOR, "value": css}

        # Fallback XPath
        xpath = self._generate_xpath(element)
        return {"by": By.XPATH, "value": xpath}

    def _is_unique(self, by, value) -> bool:
        """Check if locator uniquely identifies an element."""
        try:
            elems = self.driver.find_elements(by, value)
            return len(elems) == 1
        except NoSuchElementException:
            return False

    def _generate_xpath(self, element) -> str:
        """Generate XPath by traversing ancestors."""
        components = []
        child = element
        while child is not None:
            tag = child.tag_name
            # Add class if available
            classes = child.get_attribute("class")
            if classes:
                classes = classes.strip().split()
                cls_str = ".".join(classes)
                components.append(f"{tag}[contains(@class,'{cls_str}')]")
            else:
                components.append(tag)
            try:
                child = child.find_element(By.XPATH, "..")  # Move to parent
            except NoSuchElementException:
                break
        components.reverse()
        xpath = "/" + "/".join(components)
        return xpath

    def find_element(self, locator: dict, timeout: int = 10):
        """
        Find an element using a locator dictionary.
        Supports waiting until visible.
        """
        by = locator.get("by")
        value = locator.get("value")
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                elem = self.driver.find_element(by, value)
                return elem
            except NoSuchElementException:
                time.sleep(0.2)
        return None

    def shadow_dom_element(self, root_element, selector: str):
        """
        Access element inside shadow DOM.
        :param root_element: The shadow host element
        :param selector: CSS selector inside shadow DOM
        """
        try:
            return self.driver.execute_script(
                "return arguments[0].shadowRoot.querySelector(arguments[1])",
                root_element,
                selector
            )
        except Exception:
            return None
