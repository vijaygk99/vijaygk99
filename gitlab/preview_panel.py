"""
preview_panel.py - Preview panel component for Selenium Recorder

This module implements a panel for displaying screenshots of recorded steps
and providing visual feedback to the user.
"""

import tkinter as tk
from tkinter import ttk
import os
import io
from typing import Optional, Dict, Any
from PIL import Image, ImageTk

class PreviewPanel(ttk.Frame):
    """
    Panel for displaying screenshots and step information.
    """
    
    def __init__(self, parent, screenshot_manager=None):
        """
        Initialize the preview panel.
        
        Args:
            parent: Parent widget
            screenshot_manager: ScreenshotManager instance
        """
        super().__init__(parent)
        
        self.screenshot_manager = screenshot_manager
        
        # Current screenshot data
        self.current_screenshot_id = None
        self.current_image = None
        self.current_photo = None
        self.zoom_level = 1.0
        
        # Create UI components
        self._create_ui()
        
    def _create_ui(self):
        """
        Create the UI components.
        """
        # Create main layout
        self.main_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Create screenshot frame
        self.screenshot_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.screenshot_frame, weight=3)
        
        # Create canvas for screenshot
        self.canvas_frame = ttk.Frame(self.screenshot_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.canvas_frame,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
            bg="white"
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Create toolbar
        self.toolbar = ttk.Frame(self.screenshot_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Zoom controls
        ttk.Label(self.toolbar, text="Zoom:").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.toolbar, text="-", width=2, command=self._zoom_out).pack(side=tk.LEFT)
        
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(self.toolbar, textvariable=self.zoom_var, width=6).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.toolbar, text="+", width=2, command=self._zoom_in).pack(side=tk.LEFT)
        
        ttk.Button(self.toolbar, text="Fit", command=self._zoom_fit).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.toolbar, text="100%", command=self._zoom_reset).pack(side=tk.LEFT)
        
        # Create info frame
        self.info_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.info_frame, weight=1)
        
        # Create notebook for info tabs
        self.info_notebook = ttk.Notebook(self.info_frame)
        self.info_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create details tab
        self.details_frame = ttk.Frame(self.info_notebook, padding=10)
        self.info_notebook.add(self.details_frame, text="Details")
        
        # Create element info tab
        self.element_frame = ttk.Frame(self.info_notebook, padding=10)
        self.info_notebook.add(self.element_frame, text="Element")
        
        # Create details content
        self._create_details_content()
        
        # Create element info content
        self._create_element_info_content()
        
        # Set initial pane positions
        self.main_paned.sashpos(0, 400)
        
        # Bind events
        self._bind_events()

    def _create_details_content(self):
        """
        Create the content for the details tab.
        """
        # Create grid layout
        for i in range(2):
            self.details_frame.columnconfigure(i, weight=1)
            
        # Step ID
        ttk.Label(self.details_frame, text="Step ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.step_id_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.step_id_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Action
        ttk.Label(self.details_frame, text="Action:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.action_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.action_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Target
        ttk.Label(self.details_frame, text="Target:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.target_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.target_var, wraplength=300).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Value
        ttk.Label(self.details_frame, text="Value:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.value_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.value_var, wraplength=300).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Timestamp
        ttk.Label(self.details_frame, text="Timestamp:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.timestamp_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.timestamp_var).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Screenshot info
        ttk.Label(self.details_frame, text="Screenshot:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.screenshot_var = tk.StringVar()
        ttk.Label(self.details_frame, textvariable=self.screenshot_var).grid(row=5, column=1, sticky=tk.W, pady=2)
        
    def _create_element_info_content(self):
        """
        Create the content for the element info tab.
        """
        # Create a frame with scrollbar
        element_scroll_frame = ttk.Frame(self.element_frame)
        element_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(element_scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget
        self.element_text = tk.Text(element_scroll_frame, wrap=tk.WORD, width=40, height=10)
        self.element_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.element_text.yview)
        self.element_text.config(yscrollcommand=scrollbar.set)
        
        # Make text read-only
        self.element_text.config(state=tk.DISABLED)
        
    def _bind_events(self):
        """
        Bind events to widgets.
        """
        # Bind mouse wheel for zooming
        self.canvas.bind("<Control-MouseWheel>", self._on_mouse_wheel)
        
        # Bind mouse drag for panning
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        
        # Bind resize event
        self.bind("<Configure>", self._on_resize)
        
    def _on_mouse_wheel(self, event):
        """
        Handle mouse wheel event for zooming.
        
        Args:
            event: Event data
        """
        # Determine zoom direction
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
            
    def _on_mouse_down(self, event):
        """
        Handle mouse button press for panning.
        
        Args:
            event: Event data
        """
        self.canvas.scan_mark(event.x, event.y)
        
    def _on_mouse_drag(self, event):
        """
        Handle mouse drag for panning.
        
        Args:
            event: Event data
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def _on_resize(self, event):
        """
        Handle resize event.
        
        Args:
            event: Event data
        """
        # Redraw the image if needed
        if self.current_image:
            self._display_image()
            
    def _zoom_in(self):
        """
        Zoom in on the image.
        """
        self.zoom_level *= 1.2
        self._update_zoom()
        
    def _zoom_out(self):
        """
        Zoom out on the image.
        """
        self.zoom_level /= 1.2
        self._update_zoom()
        
    def _zoom_reset(self):
        """
        Reset zoom to 100%.
        """
        self.zoom_level = 1.0
        self._update_zoom()
        
    def _zoom_fit(self):
        """
        Zoom to fit the image in the canvas.
        """
        if not self.current_image:
            return
            
        # Get canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Get image size
        image_width, image_height = self.current_image.size
        
        # Calculate zoom level to fit
        width_ratio = canvas_width / image_width
        height_ratio = canvas_height / image_height
        
        # Use the smaller ratio to ensure the entire image fits
        self.zoom_level = min(width_ratio, height_ratio) * 0.9
        
        self._update_zoom()

    def _update_zoom(self):
        """
        Update the zoom level and redisplay the image.
        """
        # Ensure zoom level is within reasonable bounds
        self.zoom_level = max(0.1, min(5.0, self.zoom_level))
        
        # Update zoom label
        self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
        
        # Redisplay the image
        self._display_image()
        
    def show_screenshot(self, screenshot_id: str):
        """
        Show a screenshot in the preview panel.
        
        Args:
            screenshot_id: ID of the screenshot to show
        """
        if not self.screenshot_manager or not screenshot_id:
            self.clear()
            return
            
        # Load screenshot
        image_path = self.screenshot_manager.get_screenshot_path(screenshot_id)
        if not image_path or not os.path.exists(image_path):
            self.clear()
            return
            
        try:
            # Load image
            self.current_screenshot_id = screenshot_id
            self.current_image = Image.open(image_path)
            
            # Display image
            self._display_image()
            
            # Update screenshot info
            self.screenshot_var.set(f"{screenshot_id} ({self.current_image.width}x{self.current_image.height})")
            
        except Exception as e:
            print(f"Error loading screenshot: {e}")
            self.clear()
            
    def show_step(self, step: Dict[str, Any]):
        """
        Show a step in the preview panel.
        
        Args:
            step: Step data
        """
        if not step:
            self.clear()
            return
            
        # Update step details
        self.step_id_var.set(str(step.get("id", "")))
        self.action_var.set(step.get("action", ""))
        
        # Get target description
        target = self._get_target_description(step)
        self.target_var.set(target)
        
        # Get value description
        value = self._get_value_description(step)
        self.value_var.set(value)
        
        # Format timestamp
        timestamp = step.get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        self.timestamp_var.set(timestamp)
        
        # Show element info
        self._show_element_info(step)
        
        # Show screenshot
        screenshot_id = step.get("screenshot")
        if screenshot_id:
            self.show_screenshot(screenshot_id)
            
    def clear(self):
        """
        Clear the preview panel.
        """
        # Clear image
        self.current_screenshot_id = None
        self.current_image = None
        self.current_photo = None
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Reset zoom
        self.zoom_level = 1.0
        self.zoom_var.set("100%")
        
        # Clear details
        self.step_id_var.set("")
        self.action_var.set("")
        self.target_var.set("")
        self.value_var.set("")
        self.timestamp_var.set("")
        self.screenshot_var.set("")
        
        # Clear element info
        self.element_text.config(state=tk.NORMAL)
        self.element_text.delete("1.0", tk.END)
        self.element_text.config(state=tk.DISABLED)
        
    def _display_image(self):
        """
        Display the current image on the canvas.
        """
        if not self.current_image:
            return
            
        # Calculate new size
        width, height = self.current_image.size
        new_width = int(width * self.zoom_level)
        new_height = int(height * self.zoom_level)
        
        # Resize image
        resized_image = self.current_image.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to PhotoImage
        self.current_photo = ImageTk.PhotoImage(resized_image)
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Display image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo)
        
        # Configure canvas scrollregion
        self.canvas.config(scrollregion=(0, 0, new_width, new_height))
        
    def _show_element_info(self, step: Dict[str, Any]):
        """
        Show element information in the element info tab.
        
        Args:
            step: Step data
        """
        # Enable text widget for editing
        self.element_text.config(state=tk.NORMAL)
        
        # Clear text
        self.element_text.delete("1.0", tk.END)
        
        # Get element info
        element_info = step.get("element_info", {})
        if not element_info:
            self.element_text.insert(tk.END, "No element information available.")
            self.element_text.config(state=tk.DISABLED)
            return
            
        # Format element info
        lines = []
        
        # Add tag name
        tag_name = element_info.get("tag_name", "").upper()
        if tag_name:
            lines.append(f"Tag: {tag_name}")
            
        # Add ID
        element_id = element_info.get("id")
        if element_id:
            lines.append(f"ID: {element_id}")
            
        # Add name
        name = element_info.get("name")
        if name:
            lines.append(f"Name: {name}")
            
        # Add class
        class_name = element_info.get("class")
        if class_name:
            lines.append(f"Class: {class_name}")
            
        # Add type
        element_type = element_info.get("type")
        if element_type:
            lines.append(f"Type: {element_type}")
            
        # Add value
        value = element_info.get("value")
        if value:
            if len(value) > 50:
                value = value[:47] + "..."
            lines.append(f"Value: {value}")
            
        # Add text
        text = element_info.get("text")
        if text:
            if len(text) > 50:
                text = text[:47] + "..."
            lines.append(f"Text: {text}")
            
        # Add position
        position = element_info.get("position")
        if position:
            x = position.get("x")
            y = position.get("y")
            width = position.get("width")
            height = position.get("height")
            lines.append(f"Position: x={x}, y={y}, width={width}, height={height}")
            
        # Add other attributes
        for key, value in element_info.items():
            if key not in ["tag_name", "id", "name", "class", "type", "value", "text", "position"]:
                if isinstance(value, (str, int, float, bool)):
                    lines.append(f"{key}: {value}")
                    
        # Insert text
        self.element_text.insert(tk.END, "\n".join(lines))
        
        # Disable text widget
        self.element_text.config(state=tk.DISABLED)
        
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
        
    def _get_value_description(self, step: Dict[str, Any]) -> str:
        """
        Get a human-readable description of the step value.
        
        Args:
            step: Step data
            
        Returns:
            Value description
        """
        action = step.get("action", "")
        
        if action == "input":
            value = step.get("value", "")
            if len(value) > 30:
                value = value[:27] + "..."
            return value
            
        elif action == "select":
            selected_options = step.get("selected_options", [])
            values = []
            
            for option in selected_options:
                text = option.get("text")
                if text:
                    values.append(text)
                    
            return ", ".join(values)
            
        elif action == "press_key":
            return step.get("key", "")
            
        elif action == "check":
            return "✓"
            
        elif action == "uncheck":
            return "☐"
            
        return ""
