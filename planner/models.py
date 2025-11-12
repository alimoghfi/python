"""Domain models for the modern planner application."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import List, Optional


@dataclass
class Task:
    """Represents a task in the planner."""

    title: str
    due: Optional[datetime] = None
    priority: int = 3
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    uid: str = field(default_factory=lambda: datetime.utcnow().strftime("tsk%Y%m%d%H%M%S%f"))

    def mark_complete(self) -> None:
        self.completed = True
        self.completed_at = datetime.utcnow()

    def snooze(self, delta: timedelta) -> None:
        if self.due:
            self.due = self.due + delta

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "due": self.due.isoformat() if self.due else None,
            "priority": self.priority,
            "tags": self.tags,
            "notes": self.notes,
            "completed": self.completed,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            title=data["title"],
            due=datetime.fromisoformat(data["due"]) if data.get("due") else None,
            priority=data.get("priority", 3),
            tags=list(data.get("tags", [])),
            notes=data.get("notes"),
            completed=data.get("completed", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            uid=data.get("uid", datetime.utcnow().strftime("tsk%Y%m%d%H%M%S%f")),
        )


@dataclass
class Event:
    """Represents a calendar event."""

    title: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    uid: str = field(default_factory=lambda: datetime.utcnow().strftime("evt%Y%m%d%H%M%S%f"))

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "tags": self.tags,
            "notes": self.notes,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(
            title=data["title"],
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            location=data.get("location"),
            tags=list(data.get("tags", [])),
            notes=data.get("notes"),
            uid=data.get("uid", datetime.utcnow().strftime("evt%Y%m%d%H%M%S%f")),
        )


@dataclass
class Agenda:
    """Represents a combination of tasks and events for a day."""

    day: date
    tasks: List[Task] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)

    def summary(self) -> str:
        return f"Agenda for {self.day.isoformat()}: {len(self.tasks)} tasks, {len(self.events)} events"
