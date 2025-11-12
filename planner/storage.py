"""Storage utilities for the modern planner application."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Tuple

from .models import Event, Task

DEFAULT_DATA_DIR = Path(os.environ.get("MODERN_PLANNER_HOME", Path.home() / ".modern_planner"))
DEFAULT_DATA_FILE = DEFAULT_DATA_DIR / "planner_data.json"


def ensure_storage(file_path: Path = DEFAULT_DATA_FILE) -> None:
    """Ensure that the storage directory and file exist."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        data = {"tasks": [], "events": []}
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_data(file_path: Path = DEFAULT_DATA_FILE) -> Tuple[List[Task], List[Event]]:
    """Load tasks and events from storage."""
    ensure_storage(file_path)
    content = json.loads(file_path.read_text(encoding="utf-8"))
    tasks = [Task.from_dict(item) for item in content.get("tasks", [])]
    events = [Event.from_dict(item) for item in content.get("events", [])]
    return tasks, events


def save_data(tasks: Iterable[Task], events: Iterable[Event], file_path: Path = DEFAULT_DATA_FILE) -> None:
    """Persist tasks and events to storage."""
    ensure_storage(file_path)
    payload = {
        "tasks": [task.to_dict() for task in tasks],
        "events": [event.to_dict() for event in events],
    }
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
