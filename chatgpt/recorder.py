# app/recorder.py

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import json

class Recorder:
    """
    Record user actions in the browser for generating automation scripts.
    """

    def __init__(self, driver, locator_engine):
        self.driver = driver
        self.locator_engine = locator_engine
        self.actions = []  # List of recorded steps
        self.recording = False

    def start_recording(self):
        """Begin recording user actions."""
        self.recording = True
        print("Recording started...")

    def stop_recording(self):
        """Stop recording user actions."""
        self.recording = False
        print("Recording stopped.")

    def record_click(self, element):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "click", "locator": locator}
        self.actions.append(step)

    def record_double_click(self, element):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "double_click", "locator": locator}
        self.actions.append(step)

    def record_right_click(self, element):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "right_click", "locator": locator}
        self.actions.append(step)

    def record_hover(self, element):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "hover", "locator": locator}
        self.actions.append(step)

    def record_drag_drop(self, source, target):
        if not self.recording:
            return
        src_locator = self.locator_engine.get_locator(source)
        tgt_locator = self.locator_engine.get_locator(target)
        step = {"action": "drag_drop", "source": src_locator, "target": tgt_locator}
        self.actions.append(step)

    def record_input(self, element, text):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "input", "locator": locator, "text": text}
        self.actions.append(step)

    def record_select(self, element, option_text):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "select", "locator": locator, "option": option_text}
        self.actions.append(step)

    def record_check_uncheck(self, element, check=True):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "check" if check else "uncheck", "locator": locator}
        self.actions.append(step)

    def record_navigate(self, url):
        if not self.recording:
            return
        step = {"action": "navigate", "url": url}
        self.actions.append(step)

    def record_switch_frame(self, element=None):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element) if element else None
        step = {"action": "switch_frame", "locator": locator}
        self.actions.append(step)

    def record_upload(self, element, file_path):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "upload", "locator": locator, "file": file_path}
        self.actions.append(step)

    def record_download(self, element):
        if not self.recording:
            return
        locator = self.locator_engine.get_locator(element)
        step = {"action": "download", "locator": locator}
        self.actions.append(step)

    def record_alert_accept(self):
        if not self.recording:
            return
        step = {"action": "alert_accept"}
        self.actions.append(step)

    def record_alert_dismiss(self):
        if not self.recording:
            return
        step = {"action": "alert_dismiss"}
        self.actions.append(step)

    def save_actions(self, file_path):
        """Save recorded actions to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.actions, f, indent=4)

    def load_actions(self, file_path):
        """Load recorded actions from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            self.actions = json.load(f)

    def execute_actions(self):
        """Play back recorded actions in the browser."""
        for step in self.actions:
            action = step["action"]
            if action == "click":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    elem.click()
            elif action == "double_click":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    ActionChains(self.driver).double_click(elem).perform()
            elif action == "right_click":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    ActionChains(self.driver).context_click(elem).perform()
            elif action == "hover":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    ActionChains(self.driver).move_to_element(elem).perform()
            elif action == "drag_drop":
                src = self.locator_engine.find_element(step["source"])
                tgt = self.locator_engine.find_element(step["target"])
                if src and tgt:
                    ActionChains(self.driver).drag_and_drop(src, tgt).perform()
            elif action == "input":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    elem.clear()
                    elem.send_keys(step["text"])
            elif action == "select":
                from selenium.webdriver.support.ui import Select
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    Select(elem).select_by_visible_text(step["option"])
            elif action == "check":
                elem = self.locator_engine.find_element(step["locator"])
                if elem and not elem.is_selected():
                    elem.click()
            elif action == "uncheck":
                elem = self.locator_engine.find_element(step["locator"])
                if elem and elem.is_selected():
                    elem.click()
            elif action == "navigate":
                self.driver.get(step["url"])
            elif action == "switch_frame":
                if step.get("locator"):
                    elem = self.locator_engine.find_element(step["locator"])
                    if elem:
                        self.driver.switch_to.frame(elem)
                else:
                    self.driver.switch_to.default_content()
            elif action == "upload":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    elem.send_keys(step["file"])
            elif action == "download":
                elem = self.locator_engine.find_element(step["locator"])
                if elem:
                    elem.click()
            elif action == "alert_accept":
                try:
                    self.driver.switch_to.alert.accept()
                except:
                    pass
            elif action == "alert_dismiss":
                try:
                    self.driver.switch_to.alert.dismiss()
                except:
                    pass
            time.sleep(0.2)  # small delay between steps
