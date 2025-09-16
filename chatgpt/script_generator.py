# app/script_generator.py

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

class ScriptGenerator:
    """
    Generates executable Python Selenium scripts from recorded actions.
    """

    def __init__(self, actions, driver_path="chromedriver", download_dir=None, screenshot_dir=None):
        self.actions = actions
        self.driver_path = driver_path
        self.download_dir = download_dir or str(Path.cwd() / "downloads")
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        self.screenshot_dir = screenshot_dir or str(Path.cwd() / "screenshots")
        Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def generate_script_text(self) -> str:
        """Generate Python script text for Selenium execution."""
        script_lines = [
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "from selenium.webdriver.support.ui import WebDriverWait",
            "from selenium.webdriver.support import expected_conditions as EC",
            "from selenium.webdriver.support.ui import Select",
            "from selenium.webdriver.common.action_chains import ActionChains",
            "import time, os",
            "",
            f"driver = webdriver.Chrome(executable_path='{self.driver_path}')",
            "driver.maximize_window()",
            f"os.makedirs('{self.download_dir}', exist_ok=True)",
            f"os.makedirs('{self.screenshot_dir}', exist_ok=True)",
            "",
        ]

        for idx, step in enumerate(self.actions, 1):
            script_lines.append(f"# Step {idx}: {step.get('action')}")
            action = step["action"]

            if action == "navigate":
                script_lines.append(f"driver.get('{step['url']}')")
                script_lines.append("time.sleep(1)")

            elif action in ["click", "double_click", "right_click", "hover", "input", "select", "check", "uncheck", "upload", "download"]:
                locator = step.get("locator")
                if not locator:
                    continue
                by = f"By.{locator['by'].split('.')[-1]}"
                value = locator["value"].replace("'", "\\'")
                script_lines.append(f"try:")
                script_lines.append(f"    elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located(({by}, '{value}')))")
                if action == "click":
                    script_lines.append(f"    elem.click()")
                elif action == "double_click":
                    script_lines.append(f"    ActionChains(driver).double_click(elem).perform()")
                elif action == "right_click":
                    script_lines.append(f"    ActionChains(driver).context_click(elem).perform()")
                elif action == "hover":
                    script_lines.append(f"    ActionChains(driver).move_to_element(elem).perform()")
                elif action == "input":
                    script_lines.append(f"    elem.clear()")
                    script_lines.append(f"    elem.send_keys('{step['text']}')")
                elif action == "select":
                    script_lines.append(f"    Select(elem).select_by_visible_text('{step['option']}')")
                elif action == "check":
                    script_lines.append(f"    if not elem.is_selected(): elem.click()")
                elif action == "uncheck":
                    script_lines.append(f"    if elem.is_selected(): elem.click()")
                elif action == "upload":
                    script_lines.append(f"    elem.send_keys('{step['file']}')")
                elif action == "download":
                    script_lines.append(f"    elem.click()")
                script_lines.append(f"except Exception as e:")
                script_lines.append(f"    print('Step {idx} failed:', e)")
                script_lines.append(f"time.sleep(0.5)")
            
            elif action == "switch_frame":
                locator = step.get("locator")
                if locator:
                    by = f"By.{locator['by'].split('.')[-1]}"
                    value = locator["value"].replace("'", "\\'")
                    script_lines.append(f"frame_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located(({by}, '{value}')))")
                    script_lines.append("driver.switch_to.frame(frame_elem)")
                else:
                    script_lines.append("driver.switch_to.default_content()")

            elif action == "alert_accept":
                script_lines.append("try: driver.switch_to.alert.accept()")
                script_lines.append("except: pass")

            elif action == "alert_dismiss":
                script_lines.append("try: driver.switch_to.alert.dismiss()")
                script_lines.append("except: pass")

            # Optional screenshot per step
            script_lines.append(f"driver.save_screenshot(os.path.join('{self.screenshot_dir}', 'step_{idx}.png'))")
            script_lines.append("")

        script_lines.append("driver.quit()")
        return "\n".join(script_lines)

    def save_script(self, file_path: str):
        """Save generated script to a Python file."""
        script_text = self.generate_script_text()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(script_text)
        print(f"Script saved to {file_path}")
