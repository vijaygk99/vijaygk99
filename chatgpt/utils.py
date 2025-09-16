# app/utils.py

import os
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class Logger:
    """Centralized logger for application and generated scripts."""

    @staticmethod
    def setup(log_dir: str = "logs") -> str:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(log_dir, f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)

        logging.info(f"Logger initialized. Log file: {log_file}")
        return log_file


class ScreenshotManager:
    """Handles screenshot capture per step and on errors."""

    def __init__(self, base_dir: str = "screenshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def capture(self, driver, step_name: str) -> str:
        """Capture screenshot for a given step."""
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{step_name}.png"
        file_path = self.base_dir / file_name
        try:
            driver.save_screenshot(str(file_path))
            logging.info(f"Screenshot saved: {file_path}")
        except Exception as e:
            logging.error(f"Failed to capture screenshot: {e}")
        return str(file_path)


class RunManager:
    """Manages run directories for each session."""

    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_run_folder(self) -> str:
        """Create a unique run folder for each execution."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_folder = self.base_dir / f"run_{run_id}"
        run_folder.mkdir(parents=True, exist_ok=True)
        logging.info(f"Run folder created: {run_folder}")
        return str(run_folder)


class Exporter:
    """Exports recorded actions to JSON and CSV for reusability."""

    @staticmethod
    def to_json(actions: List[Dict[str, Any]], file_path: str):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(actions, f, indent=4)
            logging.info(f"Actions exported to JSON: {file_path}")
        except Exception as e:
            logging.error(f"Failed to export JSON: {e}")

    @staticmethod
    def to_csv(actions: List[Dict[str, Any]], file_path: str):
        try:
            if not actions:
                return
            keys = actions[0].keys()
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(actions)
            logging.info(f"Actions exported to CSV: {file_path}")
        except Exception as e:
            logging.error(f"Failed to export CSV: {e}")
