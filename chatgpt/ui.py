# app/ui.py
"""
Tkinter UI for Selenium Recorder (Chrome-only)

Integrates:
 - app.browser_manager.ChromeManager
 - app.locator_engine.LocatorEngine
 - app.recorder.Recorder
 - app.script_generator.ScriptGenerator
 - app.utils (Logger, ScreenshotManager, RunManager, Exporter)

Usage: This file is intended to be imported by run_recorder.py which creates
an AppConfig and starts RecorderApp(cfg). Save into app/ui.py
"""

import os
import sys
import threading
import time
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Import local modules - ensure these exist in app/
from .browser_manager import ChromeManager
from .locator_engine import LocatorEngine, BY_MAP
from .recorder import Recorder
from .script_generator import ScriptGenerator
from .utils import Logger, ScreenshotManager, RunManager, Exporter

# Basic logging to console (ScriptGenerator and others also use logging module)
import logging

logger = logging.getLogger("selenium_recorder.ui")
logging.getLogger().setLevel(logging.INFO)


class AppConfig:
    def __init__(self):
        # default config values -- user may edit them in UI
        self.chromedriver_path: Optional[str] = None
        self.chrome_binary: Optional[str] = None
        self.download_dir: str = str(Path.cwd() / "downloads")
        self.headless: bool = False
        self.implicit_wait: int = 5
        self.explicit_wait: int = 15
        self.retry_attempts: int = 2
        self.default_timeout: int = 15
        self.screenshot_dir: str = str(Path.cwd() / "artifacts" / "screenshots")


class RecorderApp(tk.Tk):
    def __init__(self, config: AppConfig):
        super().__init__()
        self.title("Selenium Recorder - Full")
        self.geometry("1200x760")
        self.minsize(1000, 600)

        self.config_obj = config

        # Initialize utils
        self.log_file = Logger.setup(log_dir=str(Path.cwd() / "artifacts" / "logs"))
        self.screenshot_mgr = ScreenshotManager(base_dir=self.config_obj.screenshot_dir)
        self.run_mgr = RunManager(base_dir=str(Path.cwd() / "artifacts" / "runs"))

        # Browser & engine placeholders (initialized after start)
        self.chrome_mgr: Optional[ChromeManager] = ChromeManager(
            chromedriver_path=self.config_obj.chromedriver_path,
            chrome_binary=self.config_obj.chrome_binary,
            download_dir=self.config_obj.download_dir,
            headless=self.config_obj.headless,
            implicit_wait=self.config_obj.implicit_wait,
        )
        self.locator_engine: Optional[LocatorEngine] = LocatorEngine(self.chrome_mgr.current)
        self.recorder: Optional[Recorder] = Recorder(self.chrome_mgr, self.locator_engine)

        # UI state
        self.selected_step_index: Optional[int] = None

        # Build UI
        self._build_ui()

    # ----------------- UI Construction -----------------
    def _build_ui(self):
        # Top config frame
        cfg_frame = ttk.Frame(self)
        cfg_frame.pack(side=tk.TOP, fill=tk.X, padx=6, pady=6)

        ttk.Label(cfg_frame, text="Chromedriver:").pack(side=tk.LEFT, padx=(0, 4))
        self.cd_entry = ttk.Entry(cfg_frame, width=45)
        self.cd_entry.pack(side=tk.LEFT)
        ttk.Button(cfg_frame, text="Browse", command=self.browse_chromedriver).pack(side=tk.LEFT, padx=4)

        ttk.Label(cfg_frame, text=" Download Dir:").pack(side=tk.LEFT, padx=(10, 4))
        self.download_entry = ttk.Entry(cfg_frame, width=30)
        self.download_entry.insert(0, self.config_obj.download_dir)
        self.download_entry.pack(side=tk.LEFT)
        ttk.Button(cfg_frame, text="Browse", command=self.browse_download_dir).pack(side=tk.LEFT, padx=4)

        ttk.Button(cfg_frame, text="Start Chrome", command=self.start_chrome).pack(side=tk.LEFT, padx=8)
        ttk.Button(cfg_frame, text="Stop Chrome", command=self.stop_chrome).pack(side=tk.LEFT)

        # Middle panes: left (actions) and right (props/logs)
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0,6))

        # Left panel: action palette + step list
        left_panel = ttk.Frame(main_pane, width=360)
        main_pane.add(left_panel, weight=1)

        ttk.Label(left_panel, text="Action Palette", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=6, pady=(6,0))
        actions = [
            "Navigate","Click","DoubleClick","RightClick","Type","Select",
            "Check","Uncheck","Hover","DragDrop","SwitchFrame","SwitchWindow",
            "ExecuteJS","UploadFile","Download","Wait","Assert_Text"
        ]
        self.action_var = tk.StringVar(value=actions[0])
        self.action_combo = ttk.Combobox(left_panel, values=actions, textvariable=self.action_var, state="readonly")
        self.action_combo.pack(fill=tk.X, padx=6, pady=4)

        # Form for action parameters
        form = ttk.Frame(left_panel)
        form.pack(fill=tk.X, padx=6, pady=4)
        ttk.Label(form, text="Locator (by:value)").grid(row=0, column=0, sticky=tk.W)
        self.loc_entry = ttk.Entry(form)
        self.loc_entry.grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Label(form, text="Value / Text").grid(row=1, column=0, sticky=tk.W)
        self.val_entry = ttk.Entry(form)
        self.val_entry.grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Label(form, text="Comment").grid(row=2, column=0, sticky=tk.W)
        self.comment_entry = ttk.Entry(form)
        self.comment_entry.grid(row=2, column=1, sticky="ew", padx=4)
        form.columnconfigure(1, weight=1)

        ttk.Button(left_panel, text="Add & Execute", command=self.on_add_and_execute).pack(fill=tk.X, padx=6, pady=6)

        ttk.Label(left_panel, text="Recorded Steps", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=6)
        self.steps_list = tk.Listbox(left_panel)
        self.steps_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.steps_list.bind("<<ListboxSelect>>", self.on_step_select)

        # bottom buttons for reorder/remove
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill=tk.X, padx=6, pady=(0,6))
        ttk.Button(btn_frame, text="Move Up", command=self.move_step_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Move Down", command=self.move_step_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self.remove_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_steps).pack(side=tk.LEFT, padx=2)

        # Right panel: properties, playback, logs
        right_panel = ttk.Frame(main_pane)
        main_pane.add(right_panel, weight=3)

        ttk.Label(right_panel, text="Step Properties / Playback", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=6, pady=(6,0))
        self.props_text = tk.Text(right_panel, height=10)
        self.props_text.pack(fill=tk.X, padx=6, pady=6)

        run_btn_frame = ttk.Frame(right_panel)
        run_btn_frame.pack(fill=tk.X, padx=6)
        ttk.Button(run_btn_frame, text="Play All", command=self.play_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Play Step", command=self.play_step).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Export Script", command=self.export_script).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Run Exported Script (Test)", command=self.run_exported_script_test).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Save Project", command=self.save_project).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Load Project", command=self.load_project).pack(side=tk.LEFT, padx=4)
        ttk.Button(run_btn_frame, text="Export CSV/JSON", command=self.export_csv_json).pack(side=tk.LEFT, padx=4)

        ttk.Label(right_panel, text="Logs", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=6, pady=(8,0))
        self.log_text = tk.Text(right_panel)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Bottom status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=6)

        # Populate sample projects menu (simple)
        menubar = tk.Menu(self)
        sample_menu = tk.Menu(menubar, tearoff=0)
        sample_menu.add_command(label="Sample: Login Flow", command=self.add_sample_login)
        sample_menu.add_command(label="Sample: Upload Flow", command=self.add_sample_upload)
        sample_menu.add_command(label="Sample: Iframe Flow", command=self.add_sample_iframe)
        menubar.add_cascade(label="Samples", menu=sample_menu)
        self.config(menu=menubar)

        # Initialize recorder list storage
        self._steps: List[Dict[str, Any]] = []

    # ----------------- UI Callbacks & Utilities -----------------
    def browse_chromedriver(self):
        p = filedialog.askopenfilename(title="Select chromedriver executable")
        if p:
            self.cd_entry.delete(0, tk.END)
            self.cd_entry.insert(0, p)
            self.config_obj.chromedriver_path = p
            self.chrome_mgr.chromedriver_path = p
            self._log(f"Chromedriver set: {p}")

    def browse_download_dir(self):
        d = filedialog.askdirectory(title="Select download directory")
        if d:
            self.download_entry.delete(0, tk.END)
            self.download_entry.insert(0, d)
            self.config_obj.download_dir = d
            self.chrome_mgr.download_dir = d
            self._log(f"Download dir set: {d}")

    def start_chrome(self):
        # Validate chromedriver path if provided
        path = self.cd_entry.get().strip() or None
        if path:
            if not Path(path).exists():
                messagebox.showerror("Chromedriver", "Chromedriver path not found.")
                return
            self.config_obj.chromedriver_path = path
        self.config_obj.download_dir = self.download_entry.get().strip() or self.config_obj.download_dir
        # Start in thread
        def _start():
            try:
                self.status_var.set("Starting Chrome...")
                self.chrome_mgr.chromedriver_path = self.config_obj.chromedriver_path
                self.chrome_mgr.download_dir = self.config_obj.download_dir
                self.chrome_mgr.headless = self.config_obj.headless
                self.chrome_mgr.implicit_wait = self.config_obj.implicit_wait
                self.chrome_mgr.start()
                # Rebind locator engine and recorder to the live driver
                self.locator_engine = LocatorEngine(self.chrome_mgr.current)
                self.recorder = Recorder(self.chrome_mgr, self.locator_engine)
                self.status_var.set("Chrome started")
                self._log("Chrome started")
            except Exception as e:
                self._log(f"Failed to start Chrome: {e}")
                messagebox.showerror("Error", str(e))
                self.status_var.set("Start failed")
        threading.Thread(target=_start, daemon=True).start()

    def stop_chrome(self):
        try:
            self.chrome_mgr.stop()
            self.status_var.set("Chrome stopped")
            self._log("Chrome stopped")
        except Exception as e:
            self._log(f"Error stopping Chrome: {e}")

    def on_add_and_execute(self):
        action = self.action_var.get()
        locator_text = self.loc_entry.get().strip() or None
        value = self.val_entry.get().strip() or None
        comment = self.comment_entry.get().strip() or None

        locator = None
        if locator_text:
            if ":" in locator_text:
                by, val = locator_text.split(":", 1)
                locator = {"by": by.strip(), "value": val.strip()}
            else:
                locator = {"by": "css", "value": locator_text}

        # Add step to internal list
        step = {"action": action, "locator": locator, "value": value, "comment": comment}
        self._steps.append(step)
        self.steps_list.insert(tk.END, f"{len(self._steps)}. {action} - {comment or ''}")

        # Execute step immediately (in background)
        threading.Thread(target=self._execute_step_thread, args=(step,), daemon=True).start()

    def _execute_step_thread(self, step: Dict[str, Any]):
        try:
            self.status_var.set(f"Executing: {step.get('action')}")
            self._log(f"Executing: {step.get('action')}")
            # For simple immediate execution use Recorder.execute_actions on single-step list
            temp_recorder = Recorder(self.chrome_mgr, self.locator_engine)
            temp_recorder.actions = [step]
            temp_recorder.execute_actions()
            self._log("Execution finished")
        except Exception as e:
            self._log(f"Execution failed: {e}")
            # Try to capture a screenshot
            try:
                run_folder = Path(self.run_mgr.create_run_folder())
                ss_path = Path(run_folder) / f"error_{int(time.time())}.png"
                self.screenshot_mgr.capture(self.chrome_mgr.current(), ss_path.stem)
                self._log(f"Captured screenshot: {ss_path}")
            except Exception as _:
                pass
        finally:
            self.status_var.set("Ready")

    def on_step_select(self, event):
        sel = self.steps_list.curselection()
        if not sel:
            self.selected_step_index = None
            return
        idx = sel[0]
        self.selected_step_index = idx
        step = self._steps[idx]
        pretty = json.dumps(step, indent=2)
        self.props_text.delete("1.0", tk.END)
        self.props_text.insert(tk.END, pretty)

    def move_step_up(self):
        sel = self.steps_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            return
        self._steps[idx-1], self._steps[idx] = self._steps[idx], self._steps[idx-1]
        self._refresh_steps_list()
        self.steps_list.select_set(idx-1)

    def move_step_down(self):
        sel = self.steps_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._steps)-1:
            return
        self._steps[idx+1], self._steps[idx] = self._steps[idx], self._steps[idx+1]
        self._refresh_steps_list()
        self.steps_list.select_set(idx+1)

    def remove_step(self):
        sel = self.steps_list.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a step to remove.")
            return
        idx = sel[0]
        del self._steps[idx]
        self._refresh_steps_list()
        self._log(f"Removed step #{idx+1}")

    def clear_steps(self):
        if messagebox.askyesno("Clear Steps", "Remove all recorded steps?"):
            self._steps.clear()
            self._refresh_steps_list()
            self._log("Cleared all steps")

    def _refresh_steps_list(self):
        self.steps_list.delete(0, tk.END)
        for i, s in enumerate(self._steps):
            desc = s.get("comment") or f"{i+1}. {s.get('action')}"
            self.steps_list.insert(tk.END, desc)

    # ----------------- Playback / Export / Run -----------------
    def play_all(self):
        if not self._steps:
            messagebox.showinfo("Info", "No steps recorded.")
            return
        def _play():
            self.status_var.set("Playing all steps...")
            self._log("Play All started")
            try:
                rec = Recorder(self.chrome_mgr, self.locator_engine)
                rec.actions = list(self._steps)
                rec.execute_actions()
                self._log("Play All finished")
            except Exception as e:
                self._log(f"Play All error: {e}")
            finally:
                self.status_var.set("Ready")
        threading.Thread(target=_play, daemon=True).start()

    def play_step(self):
        sel = self.steps_list.curselection()
        if not sel:
            messagebox.showinfo("Info", "Select a step to play.")
            return
        idx = sel[0]
        step = self._steps[idx]
        threading.Thread(target=self._execute_step_thread, args=(step,), daemon=True).start()

    def export_script(self):
        if not self._steps:
            messagebox.showinfo("Info", "No steps to export.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files","*.py")])
        if not p:
            return
        try:
            gen = ScriptGenerator(self._steps, driver_path=self.config_obj.chromedriver_path or "chromedriver", download_dir=self.config_obj.download_dir, screenshot_dir=self.config_obj.screenshot_dir)
            gen.save_script(p)
            self._log(f"Exported script: {p}")
            messagebox.showinfo("Exported", f"Script exported to {p}")
        except Exception as e:
            self._log(f"Export failed: {e}")
            messagebox.showerror("Export failed", str(e))

    def run_exported_script_test(self):
        # Exports to a temporary script in a run folder and executes it as subprocess
        if not self._steps:
            messagebox.showinfo("Info", "No steps to run.")
            return
        run_folder = Path(self.run_mgr.create_run_folder())
        script_path = run_folder / "test_script.py"
        try:
            gen = ScriptGenerator(self._steps, driver_path=self.config_obj.chromedriver_path or "chromedriver", download_dir=self.config_obj.download_dir, screenshot_dir=str(run_folder / "screenshots"))
            gen.save_script(str(script_path))
            self._log(f"Running exported script: {script_path}")

            def _run_subprocess():
                try:
                    proc = subprocess.Popen([sys.executable, str(script_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    out, err = proc.communicate()
                    (run_folder / "stdout.txt").write_text(out or "", encoding="utf-8")
                    (run_folder / "stderr.txt").write_text(err or "", encoding="utf-8")
                    self._log(f"Script finished. Return code: {proc.returncode}")
                    if out:
                        self._log("STDOUT:\n" + (out[:4000] if len(out) > 4000 else out))
                    if err:
                        self._log("STDERR:\n" + (err[:4000] if len(err) > 4000 else err))
                    messagebox.showinfo("Run finished", f"Return code: {proc.returncode}\nRun folder: {run_folder}")
                except Exception as e:
                    self._log(f"Error running exported script: {e}")
                    messagebox.showerror("Run failed", str(e))

            threading.Thread(target=_run_subprocess, daemon=True).start()
        except Exception as e:
            self._log(f"Failed to export & run: {e}")
            messagebox.showerror("Error", str(e))

    # ----------------- Save / Load / Export -----------------
    def save_project(self):
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not p:
            return
        try:
            Exporter.to_json(self._steps, p)
            self._log(f"Project saved: {p}")
            messagebox.showinfo("Saved", f"Project saved to {p}")
        except Exception as e:
            self._log(f"Save failed: {e}")
            messagebox.showerror("Save failed", str(e))

    def load_project(self):
        p = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not p:
            return
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            self._steps = list(data)
            self._refresh_steps_list()
            self._log(f"Project loaded: {p}")
        except Exception as e:
            self._log(f"Load failed: {e}")
            messagebox.showerror("Load failed", str(e))

    def export_csv_json(self):
        if not self._steps:
            messagebox.showinfo("Info", "No steps to export.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
        if not p:
            return
        try:
            Exporter.to_json(self._steps, p)
            csv_p = str(Path(p).with_suffix(".csv"))
            Exporter.to_csv(self._steps, csv_p)
            self._log(f"Exported JSON and CSV: {p}, {csv_p}")
            messagebox.showinfo("Exported", f"Exported: {p} and {csv_p}")
        except Exception as e:
            self._log(f"Export failed: {e}")
            messagebox.showerror("Export failed", str(e))

    # ----------------- Sample Projects -----------------
    def add_sample_login(self):
        # Example login flow using common locator patterns
        self._steps.extend([
            {"action":"navigate","locator":None,"value":"https://example.com/login","comment":"Open login page"},
            {"action":"input","locator":{"by":"id","value":"username"},"value":"demo_user","comment":"Enter username"},
            {"action":"input","locator":{"by":"id","value":"password"},"value":"demo_pass","comment":"Enter password"},
            {"action":"click","locator":{"by":"css","value":"button[type='submit']"},"value":None,"comment":"Submit login"},
            {"action":"wait","locator":None,"value":"2","comment":"Wait after login"},
        ])
        self._refresh_steps_list()
        self._log("Sample login flow added")

    def add_sample_upload(self):
        self._steps.extend([
            {"action":"navigate","locator":None,"value":"https://example.com/upload","comment":"Open upload page"},
            {"action":"upload","locator":{"by":"css","value":"input[type='file']"},"file":str(Path.cwd() / "samples" / "sample_upload.txt"),"comment":"Upload sample file"},
            {"action":"click","locator":{"by":"css","value":"button[type='submit']"},"comment":"Submit upload"},
        ])
        self._refresh_steps_list()
        self._log("Sample upload flow added")

    def add_sample_iframe(self):
        self._steps.extend([
            {"action":"navigate","locator":None,"value":"https://example.com/iframe_page","comment":"Open iframe page"},
            {"action":"switch_frame","locator":{"by":"css","value":"iframe#iframe_id"},"comment":"Switch to iframe"},
            {"action":"click","locator":{"by":"css","value":"button.do-in-iframe"},"comment":"Click inside iframe"},
            {"action":"switch_frame","locator":None,"comment":"Back to default content"}
        ])
        self._refresh_steps_list()
        self._log("Sample iframe flow added")

    # ----------------- Logging helper -----------------
    def _log(self, text: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        message = f"{ts} - {text}\n"
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        logger.info(text)

# If run as main for quick testing
if __name__ == "__main__":
    cfg = AppConfig()
    app = RecorderApp(cfg)
    app.mainloop()
