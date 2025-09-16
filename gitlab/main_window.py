"""
main_window.py - Main Tkinter window for Selenium Recorder

This module implements the main application window with toolbar, step table,
settings panel, and preview panel.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Import custom modules
from core.browser_manager import BrowserManager
from core.locator_engine import LocatorEngine
from core.recorder import ActionRecorder
from core.script_generator import ScriptGenerator
from utils.logger import setup_logger
from utils.screenshot import ScreenshotManager
from utils.config_manager import ConfigManager
from ui.toolbar import Toolbar
from ui.step_table import StepTable
from ui.settings_panel import SettingsPanel
from ui.preview_panel import PreviewPanel
from ui.log_panel import LogPanel

class MainWindow:
    """
    Main application window for Selenium Recorder.
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Selenium Recorder")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Set up logging
        self.logger = setup_logger("selenium_recorder")
        
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Initialize components
        self.browser_manager = BrowserManager(self.config.get("browser", {}))
        self.locator_engine = LocatorEngine()
        self.screenshot_manager = ScreenshotManager(
            self.config.get("screenshot_dir", "screenshots")
        )
        self.recorder = ActionRecorder(
            self.browser_manager, 
            self.locator_engine,
            self.screenshot_manager
        )
        self.script_generator = ScriptGenerator()
        
        # Set up UI
        self._setup_ui()
        self._setup_menu()
        self._setup_bindings()
        
        # State variables
        self.is_recording = False
        self.current_project = None
        self.unsaved_changes = False
        
        # Update window title
        self._update_title()
        
        self.logger.info("Application initialized")
        
    def _setup_ui(self):
        """
        Set up the main UI components.
        """
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create toolbar
        self.toolbar = Toolbar(self.main_frame, self._on_toolbar_action)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Create paned window for main content
        self.main_paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create left panel (steps and settings)
        self.left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel, weight=3)
        
        # Create notebook for steps and settings
        self.left_notebook = ttk.Notebook(self.left_panel)
        self.left_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create steps tab
        self.steps_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(self.steps_frame, text="Steps")
        
        # Create step table
        self.step_table = StepTable(
            self.steps_frame, 
            self._on_step_selected,
            self._on_step_edited,
            self._on_step_deleted
        )
        self.step_table.pack(fill=tk.BOTH, expand=True)
        
        # Create settings tab
        self.settings_frame = ttk.Frame(self.left_notebook)
        self.left_notebook.add(self.settings_frame, text="Settings")
        
        # Create settings panel
        self.settings_panel = SettingsPanel(
            self.settings_frame,
            self.config,
            self._on_settings_changed
        )
        self.settings_panel.pack(fill=tk.BOTH, expand=True)
        
        # Create right panel (preview and logs)
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=2)
        
        # Create notebook for preview and logs
        self.right_notebook = ttk.Notebook(self.right_panel)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create preview tab
        self.preview_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.preview_frame, text="Preview")
        
        # Create preview panel
        self.preview_panel = PreviewPanel(
            self.preview_frame,
            self.screenshot_manager
        )
        self.preview_panel.pack(fill=tk.BOTH, expand=True)
        
        # Create logs tab
        self.logs_frame = ttk.Frame(self.right_notebook)
        self.right_notebook.add(self.logs_frame, text="Logs")
        
        # Create log panel
        self.log_panel = LogPanel(self.logs_frame)
        self.log_panel.pack(fill=tk.BOTH, expand=True)
        
        # Set initial pane positions
        self.main_paned.sashpos(0, 700)
        
        # Create status bar
        self.status_bar = ttk.Frame(self.main_frame, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.recording_indicator = ttk.Label(
            self.status_bar, 
            text="●", 
            foreground="gray"
        )
        self.recording_indicator.pack(side=tk.RIGHT, padx=5)
        
    def _setup_menu(self):
        """
        Set up the application menu.
        """
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Project", command=self._new_project)
        self.file_menu.add_command(label="Open Project...", command=self._open_project)
        self.file_menu.add_command(label="Save Project", command=self._save_project)
        self.file_menu.add_command(label="Save Project As...", command=self._save_project_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Export as Python...", command=self._export_python)
        self.file_menu.add_command(label="Export as JSON...", command=self._export_json)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self._exit_app)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Delete Selected Step", command=self._delete_selected_step)
        self.edit_menu.add_command(label="Clear All Steps", command=self._clear_all_steps)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Preferences...", command=self._show_preferences)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # Recording menu
        self.recording_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.recording_menu.add_command(label="Start Recording", command=self._start_recording)
        self.recording_menu.add_command(label="Stop Recording", command=self._stop_recording)
        self.recording_menu.add_separator()
        self.recording_menu.add_command(label="Start Browser", command=self._start_browser)
        self.recording_menu.add_command(label="Stop Browser", command=self._stop_browser)
        self.recording_menu.add_separator()
        self.recording_menu.add_command(label="Navigate to URL...", command=self._navigate_to_url)
        self.menu_bar.add_cascade(label="Recording", menu=self.recording_menu)
        
        # Playback menu
        self.playback_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.playback_menu.add_command(label="Play All Steps", command=self._play_all_steps)
        self.playback_menu.add_command(label="Play Selected Step", command=self._play_selected_step)
        self.playback_menu.add_command(label="Play From Selected", command=self._play_from_selected)
        self.playback_menu.add_separator()
        self.playback_menu.add_command(label="Playback Settings...", command=self._show_playback_settings)
        self.menu_bar.add_cascade(label="Playback", menu=self.playback_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Documentation", command=self._show_documentation)
        self.help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
        
    def _setup_bindings(self):
        """
        Set up keyboard and window bindings.
        """
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_project_as())
        self.root.bind("<Control-e>", lambda e: self._export_python())
        self.root.bind("<Control-r>", lambda e: self._start_recording())
        self.root.bind("<Control-Shift-R>", lambda e: self._stop_recording())
        self.root.bind("<Control-p>", lambda e: self._play_all_steps())
        self.root.bind("<Delete>", lambda e: self._delete_selected_step())
        
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._exit_app)
        
    def _update_title(self):
        """
        Update the window title based on current project.
        """
        title = "Selenium Recorder"
        
        if self.current_project:
            title += f" - {os.path.basename(self.current_project)}"
            
        if self.unsaved_changes:
            title += " *"
            
        self.root.title(title)
        
    def _update_status(self, message: str):
        """
        Update the status bar message.
        
        Args:
            message: Status message to display
        """
        self.status_label.config(text=message)
        self.logger.info(message)
        
    def _update_recording_indicator(self, is_recording: bool):
        """
        Update the recording indicator in the status bar.
        
        Args:
            is_recording: Whether recording is active
        """
        if is_recording:
            self.recording_indicator.config(foreground="red")
        else:
            self.recording_indicator.config(foreground="gray")
            
    def _on_toolbar_action(self, action: str):
        """
        Handle toolbar button actions.
        
        Args:
            action: Action identifier
        """
        if action == "new":
            self._new_project()
        elif action == "open":
            self._open_project()
        elif action == "save":
            self._save_project()
        elif action == "start_browser":
            self._start_browser()
        elif action == "stop_browser":
            self._stop_browser()
        elif action == "start_recording":
            self._start_recording()
        elif action == "stop_recording":
            self._stop_recording()
        elif action == "play":
            self._play_all_steps()
        elif action == "export":
            self._export_python()
            
    def _on_step_selected(self, step_id: int):
        """
        Handle step selection in the step table.
        
        Args:
            step_id: ID of the selected step
        """
        # Find the step with the given ID
        for step in self.recorder.get_recorded_steps():
            if step.get("id") == step_id:
                # Update preview panel with step screenshot
                screenshot_id = step.get("screenshot")
                if screenshot_id:
                    self.preview_panel.show_screenshot(screenshot_id)
                break
                
    def _on_step_edited(self, step_id: int, new_values: Dict[str, Any]):
        """
        Handle step editing in the step table.
        
        Args:
            step_id: ID of the edited step
            new_values: New values for the step
        """
        # Find and update the step with the given ID
        steps = self.recorder.get_recorded_steps()
        for i, step in enumerate(steps):
            if step.get("id") == step_id:
                # Update step values
                for key, value in new_values.items():
                    steps[i][key] = value
                
                self.unsaved_changes = True
                self._update_title()
                break
                
    def _on_step_deleted(self, step_id: int):
        """
        Handle step deletion in the step table.
        
        Args:
            step_id: ID of the deleted step
        """
        self._delete_step(step_id)
        
    def _on_settings_changed(self, new_settings: Dict[str, Any]):
        """
        Handle settings changes.
        
        Args:
            new_settings: New settings values
        """
        # Update configuration
        self.config.update(new_settings)
        self.config_manager.save_config(self.config)
        
        # Apply settings to components
        if "browser" in new_settings:
            self.browser_manager = BrowserManager(new_settings["browser"])
            self.recorder = ActionRecorder(
                self.browser_manager,
                self.locator_engine,
                self.screenshot_manager
            )
            
        if "screenshot_dir" in new_settings:
            self.screenshot_manager = ScreenshotManager(new_settings["screenshot_dir"])
            self.recorder.screenshot_manager = self.screenshot_manager
            self.preview_panel.screenshot_manager = self.screenshot_manager
            
        self._update_status("Settings updated")
    def _new_project(self):
        """
        Create a new project.
        """
        if self.unsaved_changes:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to continue and discard them?"
            ):
                return
                
        # Clear steps
        self.recorder.clear_recorded_steps()
        self.step_table.clear_steps()
        
        # Reset project state
        self.current_project = None
        self.unsaved_changes = False
        
        # Update UI
        self._update_title()
        self._update_status("New project created")
        self.preview_panel.clear()
        
    def _open_project(self):
        """
        Open an existing project.
        """
        if self.unsaved_changes:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to continue and discard them?"
            ):
                return
                
        # Show file dialog
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[("Selenium Recorder Project", "*.srp"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Load project file
            with open(file_path, 'r') as f:
                project_data = json.load(f)
                
            # Validate project data
            if not isinstance(project_data, dict) or "steps" not in project_data:
                raise ValueError("Invalid project file format")
                
            # Clear current steps
            self.recorder.clear_recorded_steps()
            
            # Load steps
            for step in project_data["steps"]:
                self.recorder.recorded_steps.append(step)
                
            # Update step table
            self.step_table.set_steps(self.recorder.get_recorded_steps())
            
            # Update project state
            self.current_project = file_path
            self.unsaved_changes = False
            
            # Update UI
            self._update_title()
            self._update_status(f"Project loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open project: {str(e)}")
            self.logger.error(f"Error opening project: {str(e)}")
            
    def _save_project(self):
        """
        Save the current project.
        """
        if not self.current_project:
            self._save_project_as()
            return
            
        try:
            # Create project data
            project_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "steps": self.recorder.get_recorded_steps()
            }
            
            # Save project file
            with open(self.current_project, 'w') as f:
                json.dump(project_data, f, indent=2)
                
            # Update project state
            self.unsaved_changes = False
            
            # Update UI
            self._update_title()
            self._update_status(f"Project saved: {os.path.basename(self.current_project)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save project: {str(e)}")
            self.logger.error(f"Error saving project: {str(e)}")
            
    def _save_project_as(self):
        """
        Save the current project with a new name.
        """
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".srp",
            filetypes=[("Selenium Recorder Project", "*.srp"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        # Update project path
        self.current_project = file_path
        
        # Save project
        self._save_project()
        
    def _export_python(self):
        """
        Export recorded steps as a Python script.
        """
        if not self.recorder.get_recorded_steps():
            messagebox.showinfo("Export", "No steps to export")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Python Script",
            defaultextension=".py",
            filetypes=[("Python Script", "*.py"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Generate Python script
            script = self.script_generator.generate_python_script(
                self.recorder.get_recorded_steps(),
                self.config.get("script_options", {})
            )
            
            # Save script file
            with open(file_path, 'w') as f:
                f.write(script)
                
            # Update UI
            self._update_status(f"Python script exported: {os.path.basename(file_path)}")
            
            # Ask if user wants to open the file
            if messagebox.askyesno("Export", "Script exported successfully. Open it now?"):
                self._open_file(file_path)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export Python script: {str(e)}")
            self.logger.error(f"Error exporting Python script: {str(e)}")
            
    def _export_json(self):
        """
        Export recorded steps as a JSON file.
        """
        if not self.recorder.get_recorded_steps():
            messagebox.showinfo("Export", "No steps to export")
            return
            
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export JSON",
            defaultextension=".json",
            filetypes=[("JSON File", "*.json"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Create JSON data
            json_data = {
                "version": "1.0",
                "exported": datetime.now().isoformat(),
                "steps": self.recorder.get_recorded_steps()
            }
            
            # Save JSON file
            with open(file_path, 'w') as f:
                json.dump(json_data, f, indent=2)
                
            # Update UI
            self._update_status(f"JSON exported: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export JSON: {str(e)}")
            self.logger.error(f"Error exporting JSON: {str(e)}")
            
    def _start_browser(self):
        """
        Start the browser for recording.
        """
        # Disable UI during browser startup
        self._set_ui_enabled(False)
        self._update_status("Starting browser...")
        
        # Start browser in a separate thread
        def start_browser_thread():
            success, message = self.browser_manager.start_browser()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._browser_started(success, message))
            
        threading.Thread(target=start_browser_thread).start()
        
    def _browser_started(self, success: bool, message: str):
        """
        Handle browser startup completion.
        
        Args:
            success: Whether browser started successfully
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self._update_status(message)
            
            # Ask for URL to navigate to
            self._navigate_to_url()
        else:
            messagebox.showerror("Error", f"Failed to start browser: {message}")
            self._update_status(f"Browser start failed: {message}")
            
    def _stop_browser(self):
        """
        Stop the browser.
        """
        if self.is_recording:
            self._stop_recording()
            
        # Disable UI during browser shutdown
        self._set_ui_enabled(False)
        self._update_status("Stopping browser...")
        
        # Stop browser in a separate thread
        def stop_browser_thread():
            success, message = self.browser_manager.stop_browser()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._browser_stopped(success, message))
            
        threading.Thread(target=stop_browser_thread).start()
        
    def _browser_stopped(self, success: bool, message: str):
        """
        Handle browser shutdown completion.
        
        Args:
            success: Whether browser stopped successfully
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self._update_status(message)
        else:
            messagebox.showerror("Error", f"Failed to stop browser: {message}")
            self._update_status(f"Browser stop failed: {message}")
            
    def _navigate_to_url(self):
        """
        Navigate the browser to a URL.
        """
        if not self.browser_manager.driver:
            messagebox.showinfo("Navigate", "Browser is not running")
            return
            
        # Show input dialog
        url = tk.simpledialog.askstring(
            "Navigate",
            "Enter URL to navigate to:",
            initialvalue="https://"
        )
        
        if not url:
            return
            
        # Disable UI during navigation
        self._set_ui_enabled(False)
        self._update_status(f"Navigating to {url}...")
        
        # Navigate in a separate thread
        def navigate_thread():
            success, message = self.browser_manager.navigate_to(url)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._navigation_completed(success, message))
            
        threading.Thread(target=navigate_thread).start()
        
    def _navigation_completed(self, success: bool, message: str):
        """
        Handle navigation completion.
        
        Args:
            success: Whether navigation was successful
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self._update_status(message)
            
            # Add navigation step
            step = {
                'action': 'navigate',
                'url': self.browser_manager.driver.current_url,
                'timestamp': datetime.now().isoformat(),
                'screenshot': self._take_screenshot()
            }
            
            self.recorder.recorded_steps.append(step)
            self.step_table.add_step(step)
            
            self.unsaved_changes = True
            self._update_title()
        else:
            messagebox.showerror("Error", f"Failed to navigate: {message}")
            self._update_status(f"Navigation failed: {message}")
            
    def _start_recording(self):
        """
        Start recording user actions.
        """
        if not self.browser_manager.driver:
            messagebox.showinfo("Record", "Browser is not running")
            return
            
        if self.is_recording:
            messagebox.showinfo("Record", "Recording is already in progress")
            return
            
        # Disable UI during recording start
        self._set_ui_enabled(False)
        self._update_status("Starting recording...")
        
        # Start recording in a separate thread
        def start_recording_thread():
            success, message = self.recorder.start_recording(self._on_step_recorded)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._recording_started(success, message))
            
        threading.Thread(target=start_recording_thread).start()
        
    def _recording_started(self, success: bool, message: str):
        """
        Handle recording start completion.
        
        Args:
            success: Whether recording started successfully
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self.is_recording = True
            self._update_recording_indicator(True)
            self._update_status(message)
        else:
            messagebox.showerror("Error", f"Failed to start recording: {message}")
            self._update_status(f"Recording start failed: {message}")
            
    def _stop_recording(self):
        """
        Stop recording user actions.
        """
        if not self.is_recording:
            messagebox.showinfo("Record", "No recording in progress")
            return
            
        # Disable UI during recording stop
        self._set_ui_enabled(False)
        self._update_status("Stopping recording...")
        
        # Stop recording in a separate thread
        def stop_recording_thread():
            success, message = self.recorder.stop_recording()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._recording_stopped(success, message))
            
        threading.Thread(target=stop_recording_thread).start()
        
    def _recording_stopped(self, success: bool, message: str):
        """
        Handle recording stop completion.
        
        Args:
            success: Whether recording stopped successfully
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self.is_recording = False
            self._update_recording_indicator(False)
            self._update_status(message)
        else:
            messagebox.showerror("Error", f"Failed to stop recording: {message}")
            self._update_status(f"Recording stop failed: {message}")

    def _on_step_recorded(self, step: Dict[str, Any]):
        """
        Handle a new step being recorded.
        
        Args:
            step: Step data
        """
        # Add step to table
        self.step_table.add_step(step)
        
        # Update preview panel with step screenshot
        screenshot_id = step.get("screenshot")
        if screenshot_id:
            self.preview_panel.show_screenshot(screenshot_id)
            
        # Update project state
        self.unsaved_changes = True
        self._update_title()
        
    def _play_all_steps(self):
        """
        Play back all recorded steps.
        """
        steps = self.recorder.get_recorded_steps()
        if not steps:
            messagebox.showinfo("Playback", "No steps to play")
            return
            
        self._play_steps(steps)
        
    def _play_selected_step(self):
        """
        Play back the selected step.
        """
        selected_id = self.step_table.get_selected_step_id()
        if not selected_id:
            messagebox.showinfo("Playback", "No step selected")
            return
            
        # Find the step with the selected ID
        for step in self.recorder.get_recorded_steps():
            if step.get("id") == selected_id:
                self._play_steps([step])
                break
                
    def _play_from_selected(self):
        """
        Play back from the selected step to the end.
        """
        selected_id = self.step_table.get_selected_step_id()
        if not selected_id:
            messagebox.showinfo("Playback", "No step selected")
            return
            
        # Find all steps from the selected ID to the end
        steps = []
        found_selected = False
        
        for step in self.recorder.get_recorded_steps():
            if step.get("id") == selected_id:
                found_selected = True
                
            if found_selected:
                steps.append(step)
                
        if steps:
            self._play_steps(steps)
            
    def _play_steps(self, steps: List[Dict[str, Any]]):
        """
        Play back a list of steps.
        
        Args:
            steps: List of steps to play
        """
        if not self.browser_manager.driver:
            messagebox.showinfo("Playback", "Browser is not running")
            return
            
        if self.is_recording:
            messagebox.showinfo("Playback", "Cannot play steps while recording")
            return
            
        # Disable UI during playback
        self._set_ui_enabled(False)
        self._update_status("Playing steps...")
        
        # Play steps in a separate thread
        def play_steps_thread():
            try:
                for i, step in enumerate(steps):
                    # Update status in main thread
                    self.root.after(0, lambda msg=f"Playing step {i+1}/{len(steps)}": self._update_status(msg))
                    
                    # Highlight current step in table
                    self.root.after(0, lambda id=step.get("id"): self.step_table.highlight_step(id))
                    
                    # Execute step
                    self._execute_step(step)
                    
                    # Pause between steps
                    time.sleep(self.config.get("playback_delay", 0.5))
                    
                # Update UI in main thread
                self.root.after(0, lambda: self._playback_completed(True, "Playback completed"))
                
            except Exception as e:
                # Update UI in main thread on error
                self.root.after(0, lambda: self._playback_completed(False, str(e)))
                
        threading.Thread(target=play_steps_thread).start()
        
    def _playback_completed(self, success: bool, message: str):
        """
        Handle playback completion.
        
        Args:
            success: Whether playback completed successfully
            message: Status message
        """
        # Re-enable UI
        self._set_ui_enabled(True)
        
        if success:
            self._update_status(message)
        else:
            messagebox.showerror("Error", f"Playback failed: {message}")
            self._update_status(f"Playback failed: {message}")
            
    def _execute_step(self, step: Dict[str, Any]):
        """
        Execute a single step.
        
        Args:
            step: Step data
        """
        action = step.get("action")
        
        if action == "navigate":
            url = step.get("url")
            if url:
                self.browser_manager.navigate_to(url)
                
        elif action == "click":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                element.click()
                
        elif action == "double_click":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                ActionChains(self.browser_manager.driver).double_click(element).perform()
                
        elif action == "right_click":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                ActionChains(self.browser_manager.driver).context_click(element).perform()
                
        elif action == "hover":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                ActionChains(self.browser_manager.driver).move_to_element(element).perform()
                
        elif action == "input":
            locators = step.get("locators", {})
            value = step.get("value", "")
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                element.clear()
                element.send_keys(value)
                
        elif action == "select":
            locators = step.get("locators", {})
            selected_options = step.get("selected_options", [])
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                select = Select(element)
                for option in selected_options:
                    value = option.get("value")
                    if value:
                        select.select_by_value(value)
                    else:
                        select.select_by_visible_text(option.get("text", ""))
                        
        elif action == "check" or action == "uncheck":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                is_selected = element.is_selected()
                if (action == "check" and not is_selected) or (action == "uncheck" and is_selected):
                    element.click()
                    
        elif action == "press_key":
            locators = step.get("locators", {})
            key = step.get("key")
            element = self.locator_engine.find_element_with_locators(locators)
            if element and key:
                # Map key string to Keys constant
                key_mapping = {
                    "ENTER": Keys.ENTER,
                    "TAB": Keys.TAB,
                    "ESCAPE": Keys.ESCAPE,
                    "ARROW_UP": Keys.ARROW_UP,
                    "ARROW_DOWN": Keys.ARROW_DOWN,
                    "ARROW_LEFT": Keys.ARROW_LEFT,
                    "ARROW_RIGHT": Keys.ARROW_RIGHT,
                    "BACK_SPACE": Keys.BACK_SPACE,
                    "DELETE": Keys.DELETE,
                    "HOME": Keys.HOME,
                    "END": Keys.END,
                    "PAGE_UP": Keys.PAGE_UP,
                    "PAGE_DOWN": Keys.PAGE_DOWN
                }
                
                selenium_key = key_mapping.get(key)
                if selenium_key:
                    element.send_keys(selenium_key)
                    
        elif action == "drag_and_drop":
            source_locators = step.get("source_locators", {})
            target_locators = step.get("target_locators", {})
            
            source = self.locator_engine.find_element_with_locators(source_locators)
            target = self.locator_engine.find_element_with_locators(target_locators)
            
            if source and target:
                ActionChains(self.browser_manager.driver).drag_and_drop(source, target).perform()
                
        elif action == "switch_to_frame":
            locators = step.get("locators", {})
            element = self.locator_engine.find_element_with_locators(locators)
            if element:
                self.browser_manager.driver.switch_to.frame(element)
                
        elif action == "accept_alert":
            try:
                alert = self.browser_manager.driver.switch_to.alert
                alert.accept()
            except NoAlertPresentException:
                pass
                
    def _delete_selected_step(self):
        """
        Delete the selected step.
        """
        selected_id = self.step_table.get_selected_step_id()
        if not selected_id:
            return
            
        if messagebox.askyesno("Delete Step", "Are you sure you want to delete this step?"):
            self._delete_step(selected_id)
            
    def _delete_step(self, step_id: int):
        """
        Delete a step by ID.
        
        Args:
            step_id: ID of the step to delete
        """
        # Remove step from recorder
        steps = self.recorder.get_recorded_steps()
        for i, step in enumerate(steps):
            if step.get("id") == step_id:
                del steps[i]
                break
                
        # Update step table
        self.step_table.remove_step(step_id)
        
        # Update project state
        self.unsaved_changes = True
        self._update_title()
        
    def _clear_all_steps(self):
        """
        Clear all recorded steps.
        """
        if not self.recorder.get_recorded_steps():
            return
            
        if messagebox.askyesno("Clear Steps", "Are you sure you want to clear all steps?"):
            # Clear steps
            self.recorder.clear_recorded_steps()
            self.step_table.clear_steps()
            
            # Update project state
            self.unsaved_changes = True
            self._update_title()
            
            # Update UI
            self._update_status("All steps cleared")
            self.preview_panel.clear()
            
    def _show_preferences(self):
        """
        Show preferences dialog.
        """
        # Switch to settings tab
        self.left_notebook.select(1)
        
    def _show_playback_settings(self):
        """
        Show playback settings dialog.
        """
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Playback Settings")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create settings frame
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Playback delay
        ttk.Label(frame, text="Playback Delay (seconds):").grid(row=0, column=0, sticky=tk.W, pady=5)
        delay_var = tk.DoubleVar(value=self.config.get("playback_delay", 0.5))
        delay_entry = ttk.Spinbox(frame, from_=0.0, to=10.0, increment=0.1, textvariable=delay_var)
        delay_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Highlight elements
        highlight_var = tk.BooleanVar(value=self.config.get("highlight_elements", True))
        highlight_check = ttk.Checkbutton(frame, text="Highlight elements during playback", variable=highlight_var)
        highlight_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Take screenshots
        screenshots_var = tk.BooleanVar(value=self.config.get("take_screenshots", True))
        screenshots_check = ttk.Checkbutton(frame, text="Take screenshots during playback", variable=screenshots_var)
        screenshots_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        def save_settings():
            self.config["playback_delay"] = delay_var.get()
            self.config["highlight_elements"] = highlight_var.get()
            self.config["take_screenshots"] = screenshots_var.get()
            self.config_manager.save_config(self.config)
            dialog.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
    def _show_documentation(self):
        """
        Show documentation.
        """
        # Open documentation URL
        import webbrowser
        webbrowser.open("https://github.com/yourusername/selenium-recorder/wiki")
        
    def _show_about(self):
        """
        Show about dialog.
        """
        messagebox.showinfo(
            "About Selenium Recorder",
            "Selenium Recorder v1.0\n\n"
            "A robust tool for recording and playing back Selenium tests.\n\n"
            "© 2023 Your Name"
        )
        
    def _exit_app(self):
        """
        Exit the application.
        """
        if self.unsaved_changes:
            if not messagebox.askyesno(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to exit without saving?"
            ):
                return
                
        # Stop browser if running
        if self.browser_manager.driver:
            self.browser_manager.stop_browser()
            
        # Exit application
        self.root.destroy()
        
    def _set_ui_enabled(self, enabled: bool):
        """
        Enable or disable UI elements during long operations.
        
        Args:
            enabled: Whether UI should be enabled
        """
        state = "normal" if enabled else "disabled"
        
        # Update menu state
        for menu in [self.file_menu, self.edit_menu, self.recording_menu, self.playback_menu]:
            for i in range(menu.index("end") + 1):
                try:
                    menu.entryconfig(i, state=state)
                except:
                    pass
                    
        # Update toolbar state
        self.toolbar.set_enabled(enabled)
        
    def _take_screenshot(self) -> Optional[str]:
        """
        Take a screenshot of the current browser window.
        
        Returns:
            Screenshot ID or None if failed
        """
        if not self.browser_manager.driver or not self.screenshot_manager:
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
            
    def _open_file(self, file_path: str):
        """
        Open a file with the default application.
        
        Args:
            file_path: Path to the file to open
        """
        import os
        import platform
        import subprocess
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            self.logger.error(f"Error opening file: {str(e)}")


def main():
    """
    Main application entry point.
    """
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
