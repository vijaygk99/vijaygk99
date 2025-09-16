# app/browser_manager.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os
import time

class BrowserManager:
    def __init__(self, driver_path: str, download_dir: str = None, headless: bool = False, implicit_wait: int = 5):
        """
        Initialize the Chrome browser manager.
        :param driver_path: Path to ChromeDriver executable
        :param download_dir: Default download folder
        :param headless: Launch in headless mode
        :param implicit_wait: Implicit wait seconds
        """
        self.driver_path = driver_path
        self.download_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
        self.headless = headless
        self.implicit_wait = implicit_wait
        self.driver = None

    def start_browser(self):
        """Start Chrome browser with options."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        prefs = {
            "download.default_directory": self.download_dir,
            "profile.default_content_settings.popups": 0,
            "directory_upgrade": True
        }
        options.add_experimental_option("prefs", prefs)

        service = Service(self.driver_path)
        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(self.implicit_wait)
        except WebDriverException as e:
            raise RuntimeError(f"Failed to start ChromeDriver: {e}")

    def stop_browser(self):
        """Quit the browser."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def navigate_to(self, url: str):
        """Open a URL in the browser."""
        if not self.driver:
            raise RuntimeError("Browser not started.")
        self.driver.get(url)

    def wait_for_element(self, by, value, timeout=10):
        """Wait until the element is visible."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, value)))
            return element
        except TimeoutException:
            return None

    def switch_to_window(self, index: int):
        """Switch to a browser window/tab by index."""
        handles = self.driver.window_handles
        if index < 0 or index >= len(handles):
            raise IndexError("Invalid window index.")
        self.driver.switch_to.window(handles[index])

    def accept_alert(self):
        """Accept an alert if present."""
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass

    def dismiss_alert(self):
        """Dismiss an alert if present."""
        try:
            alert = self.driver.switch_to.alert
            alert.dismiss()
        except:
            pass

    def execute_js(self, script: str):
        """Execute JavaScript in the current page."""
        return self.driver.execute_script(script)

    def refresh_page(self):
        """Refresh the current page."""
        self.driver.refresh()

    def get_current_url(self):
        """Get current page URL."""
        return self.driver.current_url

    def wait_for_page_load(self, timeout=10):
        """Wait until document.readyState is complete."""
        end_time = time.time() + timeout
        while time.time() < end_time:
            ready_state = self.execute_js("return document.readyState;")
            if ready_state == "complete":
                return True
            time.sleep(0.2)
        return False
