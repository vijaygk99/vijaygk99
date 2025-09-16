"""
step_table.py - Table component for displaying recorded steps

This module implements a table for displaying, selecting, and editing
recorded steps in the Selenium Recorder.
"""

import tkinter as tk
from tkinter import ttk
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

class StepTable(ttk.Frame):
    """
    Table for displaying and managing recorded steps.
    """
    
    def __init__(
        self, 
        parent, 
        on_select: Callable[[int], None] = None,
        on_edit: Callable[[int, Dict[str, Any]], None] = None,
        on_delete: Callable[[int], None] = None
    ):
        """
        Initialize the step table.
        
        Args:
            parent: Parent widget
            on_select: Callback when a step is selected
            on_edit: Callback when a step is edited
            on_delete: Callback when a step is deleted
        """
        super().__init__(parent)
        
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        # Step data
        self.steps = []
        self.step_map = {}  # Maps step IDs to row indices
        
        # Create UI components
        self._create_table()
        self._create_context_menu()
    def _create_table(self):
        """
        Create the table for displaying steps.
        """
        # Create a frame with scrollbar
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create treeview
        columns = ("id", "action", "target", "value", "timestamp")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns,
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        
        # Configure scrollbar
        scrollbar.config(command=self.tree.yview)
        
        # Set column headings
        self.tree.heading("id", text="#")
        self.tree.heading("action", text="Action")
        self.tree.heading("target", text="Target")
        self.tree.heading("value", text="Value")
        self.tree.heading("timestamp", text="Time")
        
        # Set column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("action", width=100, stretch=True)
        self.tree.column("target", width=200, stretch=True)
        self.tree.column("value", width=200, stretch=True)
        self.tree.column("timestamp", width=150, stretch=False)
        
        # Pack treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._on_tree_right_click)  # Right-click for context menu
        
    def _create_context_menu(self):
        """
        Create context menu for the table.
        """
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit Step", command=self._edit_selected_step)
        self.context_menu.add_command(label="Delete Step", command=self._delete_selected_step)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Play This Step", command=self._play_selected_step)
        self.context_menu.add_command(label="Play From Here", command=self._play_from_selected)

    def add_step(self, step: Dict[str, Any]):
        """
        Add a step to the table.
        
        Args:
            step: Step data
        """
        # Extract step data
        step_id = step.get("id", len(self.steps) + 1)
        action = step.get("action", "")
        
        # Get target description
        target = self._get_target_description(step)
        
        # Get value
        value = self._get_value_description(step)
        
        # Format timestamp
        timestamp = step.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%H:%M:%S")
            except:
                pass
                
        # Insert into treeview
        item_id = self.tree.insert(
            "", 
            "end", 
            values=(step_id, action, target, value, timestamp)
        )
        
        # Store step data
        self.steps.append(step)
        self.step_map[step_id] = len(self.steps) - 1
        
        # Select the new step
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        
    def set_steps(self, steps: List[Dict[str, Any]]):
        """
        Set all steps in the table.
        
        Args:
            steps: List of step data
        """
        # Clear existing steps
        self.clear_steps()
        
        # Add new steps
        for step in steps:
            self.add_step(step)
            
    def clear_steps(self):
        """
        Clear all steps from the table.
        """
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Clear step data
        self.steps = []
        self.step_map = {}
        
    def remove_step(self, step_id: int):
        """
        Remove a step from the table.
        
        Args:
            step_id: ID of the step to remove
        """
        # Find the item in the treeview
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and int(values[0]) == step_id:
                self.tree.delete(item)
                break
                
        # Remove from step data
        if step_id in self.step_map:
            index = self.step_map[step_id]
            self.steps.pop(index)
            
            # Update step map
            self.step_map = {}
            for i, step in enumerate(self.steps):
                self.step_map[step.get("id")] = i
                
    def get_selected_step_id(self) -> Optional[int]:
        """
        Get the ID of the selected step.
        
        Returns:
            Step ID or None if no step is selected
        """
        selection = self.tree.selection()
        if not selection:
            return None
            
        values = self.tree.item(selection[0], "values")
        if not values:
            return None
            
        return int(values[0])
        
    def highlight_step(self, step_id: int):
        """
        Highlight a step in the table.
        
        Args:
            step_id: ID of the step to highlight
        """
        # Find the item in the treeview
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and int(values[0]) == step_id:
                # Select and scroll to the item
                self.tree.selection_set(item)
                self.tree.see(item)
                
                # Update UI
                self.update_idletasks()
                break

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
            
        elif action == "drag_and_drop":
            # Get source and target descriptions
            source_info = step.get("source_element_info", {})
            target_info = step.get("target_element_info", {})
            
            source_desc = source_info.get("id") or source_info.get("tag_name", "").upper()
            target_desc = target_info.get("id") or target_info.get("tag_name", "").upper()
            
            return f"{source_desc} → {target_desc}"
            
        elif action == "switch_to_frame":
            # Get frame description
            element_info = step.get("element_info", {})
            
            frame_id = element_info.get("id")
            frame_name = element_info.get("name")
            
            if frame_id:
                return f"Frame id='{frame_id}'"
            elif frame_name:
                return f"Frame name='{frame_name}'"
            else:
                return "Frame"
                
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
        
    def _on_tree_select(self, event):
        """
        Handle tree selection event.
        
        Args:
            event: Event data
        """
        if not self.on_select:
            return
            
        step_id = self.get_selected_step_id()
        if step_id is not None:
            self.on_select(step_id)
            
    def _on_tree_double_click(self, event):
        """
        Handle tree double-click event.
        
        Args:
            event: Event data
        """
        self._edit_selected_step()
        
    def _on_tree_right_click(self, event):
        """
        Handle tree right-click event.
        
        Args:
            event: Event data
        """
        # Select the item under the cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # Show context menu
            self.context_menu.post(event.x_root, event.y_root)
            
    def _edit_selected_step(self):
        """
        Edit the selected step.
        """
        if not self.on_edit:
            return
            
        step_id = self.get_selected_step_id()
        if step_id is None:
            return
            
        # Find step data
        step = None
        for s in self.steps:
            if s.get("id") == step_id:
                step = s
                break
                
        if not step:
            return
            
        # Create edit dialog
        self._show_edit_dialog(step)

    def _delete_selected_step(self):
        """
        Delete the selected step.
        """
        if not self.on_delete:
            return
            
        step_id = self.get_selected_step_id()
        if step_id is not None:
            self.on_delete(step_id)
            
    def _play_selected_step(self):
        """
        Play the selected step.
        """
        # This is handled by the main window
        pass
        
    def _play_from_selected(self):
        """
        Play from the selected step.
        """
        # This is handled by the main window
        pass
        
    def _show_edit_dialog(self, step: Dict[str, Any]):
        """
        Show dialog for editing a step.
        
        Args:
            step: Step data to edit
        """
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Edit Step")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        dialog.transient(self)
        dialog.grab_set()
        
        # Create form
        form_frame = ttk.Frame(dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Step ID (read-only)
        ttk.Label(form_frame, text="Step ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text=str(step.get("id", ""))).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Action
        ttk.Label(form_frame, text="Action:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        action_var = tk.StringVar(value=step.get("action", ""))
        action_combo = ttk.Combobox(form_frame, textvariable=action_var, state="readonly")
        action_combo["values"] = [
            "navigate", "click", "double_click", "right_click", "hover",
            "input", "select", "check", "uncheck", "press_key",
            "drag_and_drop", "switch_to_frame", "accept_alert"
        ]
        action_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Value
        ttk.Label(form_frame, text="Value:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        value_var = tk.StringVar(value=step.get("value", ""))
        value_entry = ttk.Entry(form_frame, textvariable=value_var)
        value_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=5)
        
        description_var = tk.StringVar(value=step.get("description", ""))
        description_entry = ttk.Entry(form_frame, textvariable=description_var)
        description_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Target (read-only)
        ttk.Label(form_frame, text="Target:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text=self._get_target_description(step)).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        def save_changes():
            # Create updated step data
            updated_values = {
                "action": action_var.get(),
                "value": value_var.get(),
                "description": description_var.get()
            }
            
            # Call edit callback
            if self.on_edit:
                self.on_edit(step.get("id"), updated_values)
                
            # Close dialog
            dialog.destroy()
            
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
