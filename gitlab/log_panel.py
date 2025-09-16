"""
log_panel.py - Log panel component for Selenium Recorder

This module implements a panel for displaying application logs
and providing debugging information to the user.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

class LogHandler(logging.Handler):
    """
    Custom logging handler that forwards logs to the LogPanel.
    """
    
    def __init__(self, callback):
        """
        Initialize the handler.
        
        Args:
            callback: Function to call with log records
        """
        super().__init__()
        self.callback = callback
        
    def emit(self, record):
        """
        Emit a log record.
        
        Args:
            record: Log record
        """
        try:
            self.callback(record)
        except Exception:
            self.handleError(record)

class LogPanel(ttk.Frame):
    """
    Panel for displaying application logs.
    """
    
    def __init__(self, parent):
        """
        Initialize the log panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Log data
        self.log_records = []
        self.max_records = 1000  # Maximum number of records to keep
        
        # Create UI components
        self._create_ui()
        
        # Set up logging
        self._setup_logging()
        
    def _create_ui(self):
        """
        Create the UI components.
        """
        # Create toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Log level filter
        ttk.Label(toolbar, text="Log Level:").pack(side=tk.LEFT, padx=5)
        
        self.level_var = tk.StringVar(value="INFO")
        level_combo = ttk.Combobox(toolbar, textvariable=self.level_var, state="readonly", width=10)
        level_combo["values"] = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_combo.pack(side=tk.LEFT, padx=5)
        level_combo.bind("<<ComboboxSelected>>", lambda e: self._update_log_display())
        
        # Auto-scroll option
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar, 
            text="Auto-scroll", 
            variable=self.auto_scroll_var
        ).pack(side=tk.LEFT, padx=10)
        
        # Clear button
        ttk.Button(toolbar, text="Clear", command=self.clear_logs).pack(side=tk.RIGHT, padx=5)
        
        # Save button
        ttk.Button(toolbar, text="Save...", command=self._save_logs).pack(side=tk.RIGHT, padx=5)
        
        # Create log text area with scrollbar
        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create text widget
        self.log_text = tk.Text(
            log_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            yscrollcommand=scrollbar.set,
            background="#f0f0f0",
            font=("Consolas", 9)
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar
        scrollbar.config(command=self.log_text.yview)
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("DEBUG", foreground="gray")
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("CRITICAL", foreground="red", font=("Consolas", 9, "bold"))
        
        # Make text read-only
        self.log_text.config(state=tk.DISABLED)
        
    def _setup_logging(self):
        """
        Set up logging to capture application logs.
        """
        # Create handler
        self.log_handler = LogHandler(self.add_log_record)
        self.log_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
        # Add handler to root logger
        logging.getLogger().addHandler(self.log_handler)
        
        # Log initial message
        logging.info("Log panel initialized")
        
    def add_log_record(self, record: logging.LogRecord):
        """
        Add a log record to the panel.
        
        Args:
            record: Log record
        """
        # Add record to list
        self.log_records.append(record)
        
        # Trim list if needed
        if len(self.log_records) > self.max_records:
            self.log_records = self.log_records[-self.max_records:]
            
        # Update display
        self._update_log_display()
        
    def _update_log_display(self):
        """
        Update the log display based on current filter settings.
        """
        # Get current filter level
        level_name = self.level_var.get()
        level = getattr(logging, level_name)
        
        # Enable text widget for editing
        self.log_text.config(state=tk.NORMAL)
        
        # Clear text
        self.log_text.delete("1.0", tk.END)
        
        # Add filtered records
        for record in self.log_records:
            if record.levelno >= level:
                # Format time
                timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
                
                # Format message
                message = f"{timestamp} [{record.levelname}] {record.message}\n"
                
                # Insert with appropriate tag
                self.log_text.insert(tk.END, message, record.levelname)
                
        # Disable text widget
        self.log_text.config(state=tk.DISABLED)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
    def clear_logs(self):
        """
        Clear all log records.
        """
        # Clear records
        self.log_records = []
        
        # Update display
        self._update_log_display()
        
        # Log clear action
        logging.info("Logs cleared")
        
    def _save_logs(self):
        """
        Save logs to a file.
        """
        # Show file dialog
        file_path = filedialog.asksaveasfilename(
            title="Save Logs",
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # Open file
            with open(file_path, 'w') as f:
                # Write logs
                for record in self.log_records:
                    # Format time
                    timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Format message
                    message = f"{timestamp} [{record.levelname}] {record.name}: {record.message}\n"
                    
                    # Write to file
                    f.write(message)
                    
            # Log save action
            logging.info(f"Logs saved to {file_path}")
            
        except Exception as e:
            # Log error
            logging.error(f"Error saving logs: {str(e)}")
