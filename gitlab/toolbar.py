"""
toolbar.py - Toolbar component for Selenium Recorder

This module implements a toolbar with buttons for common actions like
starting/stopping recording, browser control, and file operations.
"""

import tkinter as tk
from tkinter import ttk
import os
from typing import Callable, Dict, Any

class Toolbar(ttk.Frame):
    """
    Toolbar with buttons for common actions.
    """
    
    def __init__(self, parent, callback: Callable[[str], None]):
        """
        Initialize the toolbar.
        
        Args:
            parent: Parent widget
            callback: Function to call when a button is clicked
        """
        super().__init__(parent)
        
        self.callback = callback
        self.buttons = {}
        
        # Create toolbar buttons
        self._create_buttons()
        
    def _create_buttons(self):
        """
        Create toolbar buttons.
        """
        # Define button configurations
        button_configs = [
            {
                "id": "new",
                "text": "New",
                "icon": "new.png",
                "tooltip": "Create a new project",
                "command": lambda: self.callback("new")
            },
            {
                "id": "open",
                "text": "Open",
                "icon": "open.png",
                "tooltip": "Open an existing project",
                "command": lambda: self.callback("open")
            },
            {
                "id": "save",
                "text": "Save",
                "icon": "save.png",
                "tooltip": "Save the current project",
                "command": lambda: self.callback("save")
            },
            {
                "id": "separator1",
                "is_separator": True
            },
            {
                "id": "start_browser",
                "text": "Start Browser",
                "icon": "browser.png",
                "tooltip": "Start the browser",
                "command": lambda: self.callback("start_browser")
            },
            {
                "id": "stop_browser",
                "text": "Stop Browser",
                "icon": "browser_stop.png",
                "tooltip": "Stop the browser",
                "command": lambda: self.callback("stop_browser")
            },
            {
                "id": "separator2",
                "is_separator": True
            },
            {
                "id": "start_recording",
                "text": "Record",
                "icon": "record.png",
                "tooltip": "Start recording",
                "command": lambda: self.callback("start_recording")
            },
            {
                "id": "stop_recording",
                "text": "Stop",
                "icon": "stop.png",
                "tooltip": "Stop recording",
                "command": lambda: self.callback("stop_recording")
            },
            {
                "id": "separator3",
                "is_separator": True
            },
            {
                "id": "play",
                "text": "Play",
                "icon": "play.png",
                "tooltip": "Play recorded steps",
                "command": lambda: self.callback("play")
            },
            {
                "id": "separator4",
                "is_separator": True
            },
            {
                "id": "export",
                "text": "Export",
                "icon": "export.png",
                "tooltip": "Export as Python script",
                "command": lambda: self.callback("export")
            }
        ]
        
        # Create buttons
        for config in button_configs:
            if config.get("is_separator", False):
                ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
                continue
                
            button = ttk.Button(
                self,
                text=config.get("text", ""),
                command=config.get("command")
            )
            
            # Try to load icon
            icon_path = os.path.join("resources", "icons", config.get("icon", ""))
            if os.path.exists(icon_path):
                try:
                    icon = tk.PhotoImage(file=icon_path)
                    button.config(image=icon, compound=tk.LEFT)
                    button.image = icon  # Keep a reference to prevent garbage collection
                except Exception as e:
                    print(f"Error loading icon {icon_path}: {e}")
                    
            # Add tooltip
            tooltip = config.get("tooltip")
            if tooltip:
                self._create_tooltip(button, tooltip)
                
            button.pack(side=tk.LEFT, padx=2)
            
            # Store button reference
            self.buttons[config["id"]] = button
            
    def _create_tooltip(self, widget, text):
        """
        Create a tooltip for a widget.
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create tooltip window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            
            widget.tooltip = tooltip
            
        def leave(event):
            if hasattr(widget, "tooltip"):
                widget.tooltip.destroy()
                
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
        
    def set_enabled(self, enabled: bool):
        """
        Enable or disable all toolbar buttons.
        
        Args:
            enabled: Whether buttons should be enabled
        """
        state = "normal" if enabled else "disabled"
        
        for button_id, button in self.buttons.items():
            button.config(state=state)
