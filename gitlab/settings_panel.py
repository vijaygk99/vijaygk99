"""
settings_panel.py - Settings panel component for Selenium Recorder

This module implements a panel for configuring application settings
such as browser options, recording options, and playback options.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
from typing import Dict, Any, Callable

class SettingsPanel(ttk.Frame):
    """
    Panel for configuring application settings.
    """
    
    def __init__(
        self, 
        parent, 
        config: Dict[str, Any],
        on_change: Callable[[Dict[str, Any]], None] = None
    ):
        """
        Initialize the settings panel.
        
        Args:
            parent: Parent widget
            config: Current configuration
            on_change: Callback when settings are changed
        """
        super().__init__(parent)
        
        self.config = config
        self.on_change = on_change
        
        # Create UI components
        self._create_notebook()
        
    def _create_notebook(self):
        """
        Create a notebook with tabs for different settings categories.
        """
        # Create notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.browser_tab = ttk.Frame(self.notebook, padding=10)
        self.recording_tab = ttk.Frame(self.notebook, padding=10)
        self.playback_tab = ttk.Frame(self.notebook, padding=10)
        self.export_tab = ttk.Frame(self.notebook, padding=10)
        
        # Add tabs to notebook
        self.notebook.add(self.browser_tab, text="Browser")
        self.notebook.add(self.recording_tab, text="Recording")
        self.notebook.add(self.playback_tab, text="Playback")
        self.notebook.add(self.export_tab, text="Export")
        
        # Create settings in each tab
        self._create_browser_settings()
        self._create_recording_settings()
        self._create_playback_settings()
        self._create_export_settings()
        
        # Add save button
        save_frame = ttk.Frame(self)
        save_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            save_frame, 
            text="Save Settings", 
            command=self._save_settings
        ).pack(side=tk.RIGHT)
        
    def _create_browser_settings(self):
        """
        Create browser settings UI.
        """
        # Get browser settings
        browser_config = self.config.get("browser", {})
        
        # Browser type
        ttk.Label(self.browser_tab, text="Browser Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.browser_type_var = tk.StringVar(value=browser_config.get("type", "chrome"))
        browser_type_combo = ttk.Combobox(self.browser_tab, textvariable=self.browser_type_var, state="readonly")
        browser_type_combo["values"] = ["chrome", "firefox", "edge", "safari"]
        browser_type_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Driver path
        ttk.Label(self.browser_tab, text="Driver Path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        driver_path_frame = ttk.Frame(self.browser_tab)
        driver_path_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        self.driver_path_var = tk.StringVar(value=browser_config.get("driver_path", ""))
        driver_path_entry = ttk.Entry(driver_path_frame, textvariable=self.driver_path_var)
        driver_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_driver():
            path = filedialog.askopenfilename(
                title="Select WebDriver",
                filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
            )
            if path:
                self.driver_path_var.set(path)
                
        ttk.Button(driver_path_frame, text="Browse...", command=browse_driver).pack(side=tk.RIGHT, padx=5)
        
        # Headless mode
        self.headless_var = tk.BooleanVar(value=browser_config.get("headless", False))
        ttk.Checkbutton(
            self.browser_tab, 
            text="Headless Mode", 
            variable=self.headless_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Window size
        ttk.Label(self.browser_tab, text="Window Size:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        size_frame = ttk.Frame(self.browser_tab)
        size_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        self.window_width_var = tk.IntVar(value=browser_config.get("window_width", 1280))
        self.window_height_var = tk.IntVar(value=browser_config.get("window_height", 800))
        
        ttk.Entry(size_frame, textvariable=self.window_width_var, width=6).pack(side=tk.LEFT)
        ttk.Label(size_frame, text="×").pack(side=tk.LEFT, padx=5)
        ttk.Entry(size_frame, textvariable=self.window_height_var, width=6).pack(side=tk.LEFT)
        
        # User agent
        ttk.Label(self.browser_tab, text="User Agent:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.user_agent_var = tk.StringVar(value=browser_config.get("user_agent", ""))
        ttk.Entry(self.browser_tab, textvariable=self.user_agent_var).grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Additional options
        ttk.Label(self.browser_tab, text="Additional Options:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        self.additional_options_text = tk.Text(self.browser_tab, height=5, width=40)
        self.additional_options_text.grid(row=5, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Set additional options text
        additional_options = browser_config.get("additional_options", {})
        if additional_options:
            options_text = "\n".join([f"{k}={v}" for k, v in additional_options.items()])
            self.additional_options_text.insert("1.0", options_text)

    def _create_recording_settings(self):
        """
        Create recording settings UI.
        """
        # Get recording settings
        recording_config = self.config.get("recording", {})
        
        # Screenshot directory
        ttk.Label(self.recording_tab, text="Screenshot Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        screenshot_dir_frame = ttk.Frame(self.recording_tab)
        screenshot_dir_frame.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        self.screenshot_dir_var = tk.StringVar(value=self.config.get("screenshot_dir", "screenshots"))
        screenshot_dir_entry = ttk.Entry(screenshot_dir_frame, textvariable=self.screenshot_dir_var)
        screenshot_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_screenshot_dir():
            path = filedialog.askdirectory(title="Select Screenshot Directory")
            if path:
                self.screenshot_dir_var.set(path)
                
        ttk.Button(screenshot_dir_frame, text="Browse...", command=browse_screenshot_dir).pack(side=tk.RIGHT, padx=5)
        
        # Take screenshots
        self.take_screenshots_var = tk.BooleanVar(value=recording_config.get("take_screenshots", True))
        ttk.Checkbutton(
            self.recording_tab, 
            text="Take Screenshots During Recording", 
            variable=self.take_screenshots_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Record mouse movements
        self.record_mouse_var = tk.BooleanVar(value=recording_config.get("record_mouse", False))
        ttk.Checkbutton(
            self.recording_tab, 
            text="Record Mouse Movements", 
            variable=self.record_mouse_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Record keyboard
        self.record_keyboard_var = tk.BooleanVar(value=recording_config.get("record_keyboard", True))
        ttk.Checkbutton(
            self.recording_tab, 
            text="Record Keyboard Input", 
            variable=self.record_keyboard_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Smart element detection
        self.smart_detection_var = tk.BooleanVar(value=recording_config.get("smart_detection", True))
        ttk.Checkbutton(
            self.recording_tab, 
            text="Smart Element Detection", 
            variable=self.smart_detection_var
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def _create_playback_settings(self):
        """
        Create playback settings UI.
        """
        # Get playback settings
        playback_config = self.config.get("playback", {})
        
        # Playback speed
        ttk.Label(self.playback_tab, text="Playback Speed:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.playback_delay_var = tk.DoubleVar(value=self.config.get("playback_delay", 0.5))
        delay_frame = ttk.Frame(self.playback_tab)
        delay_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(delay_frame, text="Delay between steps:").pack(side=tk.LEFT)
        ttk.Spinbox(
            delay_frame, 
            from_=0.0, 
            to=10.0, 
            increment=0.1, 
            width=5,
            textvariable=self.playback_delay_var
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(delay_frame, text="seconds").pack(side=tk.LEFT)
        
        # Highlight elements
        self.highlight_elements_var = tk.BooleanVar(value=playback_config.get("highlight_elements", True))
        ttk.Checkbutton(
            self.playback_tab, 
            text="Highlight Elements During Playback", 
            variable=self.highlight_elements_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Wait for page load
        self.wait_for_page_load_var = tk.BooleanVar(value=playback_config.get("wait_for_page_load", True))
        ttk.Checkbutton(
            self.playback_tab, 
            text="Wait for Page Load After Navigation", 
            variable=self.wait_for_page_load_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Wait timeout
        ttk.Label(self.playback_tab, text="Wait Timeout:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        timeout_frame = ttk.Frame(self.playback_tab)
        timeout_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        self.wait_timeout_var = tk.IntVar(value=playback_config.get("wait_timeout", 30))
        ttk.Spinbox(
            timeout_frame, 
            from_=1, 
            to=120, 
            increment=1, 
            width=5,
            textvariable=self.wait_timeout_var
        ).pack(side=tk.LEFT)
        ttk.Label(timeout_frame, text="seconds").pack(side=tk.LEFT, padx=5)

    def _create_export_settings(self):
        """
        Create export settings UI.
        """
        # Get export settings
        export_config = self.config.get("export", {})
        script_options = self.config.get("script_options", {})
        
        # Python framework
        ttk.Label(self.export_tab, text="Python Framework:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.framework_var = tk.StringVar(value=script_options.get("framework", "selenium"))
        framework_combo = ttk.Combobox(self.export_tab, textvariable=self.framework_var, state="readonly")
        framework_combo["values"] = ["selenium", "playwright", "cypress"]
        framework_combo.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Include comments
        self.include_comments_var = tk.BooleanVar(value=script_options.get("include_comments", True))
        ttk.Checkbutton(
            self.export_tab, 
            text="Include Comments in Generated Code", 
            variable=self.include_comments_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Include timestamps
        self.include_timestamps_var = tk.BooleanVar(value=script_options.get("include_timestamps", False))
        ttk.Checkbutton(
            self.export_tab, 
            text="Include Timestamps in Comments", 
            variable=self.include_timestamps_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Use explicit waits
        self.use_explicit_waits_var = tk.BooleanVar(value=script_options.get("use_explicit_waits", True))
        ttk.Checkbutton(
            self.export_tab, 
            text="Use Explicit Waits", 
            variable=self.use_explicit_waits_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Generate assertions
        self.generate_assertions_var = tk.BooleanVar(value=script_options.get("generate_assertions", False))
        ttk.Checkbutton(
            self.export_tab, 
            text="Generate Assertions", 
            variable=self.generate_assertions_var
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Test framework
        ttk.Label(self.export_tab, text="Test Framework:").grid(row=5, column=0, sticky=tk.W, pady=5)
        
        self.test_framework_var = tk.StringVar(value=script_options.get("test_framework", "pytest"))
        test_framework_combo = ttk.Combobox(self.export_tab, textvariable=self.test_framework_var, state="readonly")
        test_framework_combo["values"] = ["pytest", "unittest", "none"]
        test_framework_combo.grid(row=5, column=1, sticky=tk.W+tk.E, pady=5)
        
    def _save_settings(self):
        """
        Save the current settings.
        """
        # Update browser settings
        browser_config = {
            "type": self.browser_type_var.get(),
            "driver_path": self.driver_path_var.get(),
            "headless": self.headless_var.get(),
            "window_width": self.window_width_var.get(),
            "window_height": self.window_height_var.get(),
            "user_agent": self.user_agent_var.get(),
            "additional_options": self._parse_additional_options()
        }
        
        # Update recording settings
        recording_config = {
            "take_screenshots": self.take_screenshots_var.get(),
            "record_mouse": self.record_mouse_var.get(),
            "record_keyboard": self.record_keyboard_var.get(),
            "smart_detection": self.smart_detection_var.get()
        }
        
        # Update playback settings
        playback_config = {
            "highlight_elements": self.highlight_elements_var.get(),
            "wait_for_page_load": self.wait_for_page_load_var.get(),
            "wait_timeout": self.wait_timeout_var.get()
        }
        
        # Update export settings
        script_options = {
            "framework": self.framework_var.get(),
            "include_comments": self.include_comments_var.get(),
            "include_timestamps": self.include_timestamps_var.get(),
            "use_explicit_waits": self.use_explicit_waits_var.get(),
            "generate_assertions": self.generate_assertions_var.get(),
            "test_framework": self.test_framework_var.get()
        }
        
        # Update config
        new_config = self.config.copy()
        new_config["browser"] = browser_config
        new_config["recording"] = recording_config
        new_config["playback"] = playback_config
        new_config["script_options"] = script_options
        new_config["playback_delay"] = self.playback_delay_var.get()
        new_config["screenshot_dir"] = self.screenshot_dir_var.get()
        
        # Call change callback
        if self.on_change:
            self.on_change(new_config)
            
    def _parse_additional_options(self) -> Dict[str, Any]:
        """
        Parse additional browser options from text.
        
        Returns:
            Dictionary of additional options
        """
        options = {}
        
        # Get text
        text = self.additional_options_text.get("1.0", tk.END).strip()
        
        # Parse options
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            # Split by first equals sign
            parts = line.split("=", 1)
            if len(parts) != 2:
                continue
                
            key = parts[0].strip()
            value = parts[1].strip()
            
            # Try to convert value to appropriate type
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
                value = float(value)
                
            options[key] = value
            
        return options

