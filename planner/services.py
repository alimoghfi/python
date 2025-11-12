"""Service layer for the modern planner application."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Optional, Sequence

from .models import Agenda, Event, Task
from .storage import load_data, save_data


class PlannerService:
    """Encapsulates core planner operations."""

    def __init__(self, storage_path=None):
        self.storage_path = storage_path
        self.tasks: List[Task] = []
        self.events: List[Event] = []
        self.refresh()

    def refresh(self) -> None:
        self.tasks, self.events = load_data(self.storage_path) if self.storage_path else load_data()

    def persist(self) -> None:
        save_data(self.tasks, self.events, self.storage_path) if self.storage_path else save_data(self.tasks, self.events)

    # Task management -----------------------------------------------------
    def add_task(
        self,
        title: str,
        *,
        due: Optional[datetime] = None,
        priority: int = 3,
        tags: Optional[Sequence[str]] = None,
        notes: Optional[str] = None,
    ) -> Task:
        task = Task(title=title, due=due, priority=priority, tags=list(tags or []), notes=notes)
        self.tasks.append(task)
        self.persist()
        return task

    def list_tasks(self, *, include_completed: bool = False) -> List[Task]:
        tasks = sorted(self.tasks, key=lambda t: (
            t.completed,
            t.due or datetime.max,
            t.priority,
            t.created_at,
        ))
        if not include_completed:
            tasks = [task for task in tasks if not task.completed]
        return tasks

    def complete_task(self, uid: str) -> Optional[Task]:
        for task in self.tasks:
            if task.uid == uid:
                task.mark_complete()
                self.persist()
                return task
        return None

    def snooze_task(self, uid: str, delta: timedelta) -> Optional[Task]:
        for task in self.tasks:
            if task.uid == uid:
                task.snooze(delta)
                self.persist()
                return task
        return None

    # Event management ----------------------------------------------------
    def add_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        *,
        location: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        notes: Optional[str] = None,
    ) -> Event:
        event = Event(
            title=title,
            start=start,
            end=end,
            location=location,
            tags=list(tags or []),
            notes=notes,
        )
        self.events.append(event)
        self.persist()
        return event

    def list_events(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Event]:
        events = sorted(self.events, key=lambda e: e.start)
        if start_date:
            events = [event for event in events if event.start.date() >= start_date]
        if end_date:
            events = [event for event in events if event.start.date() <= end_date]
        return events

    # Agenda --------------------------------------------------------------
    def agenda_for(self, day: date) -> Agenda:
        tasks = [task for task in self.tasks if (task.due and task.due.date() == day) and not task.completed]
        events = [event for event in self.events if event.start.date() == day]
        return Agenda(day=day, tasks=tasks, events=events)

    def upcoming_agenda(self, *, days: int = 7) -> List[Agenda]:
        today = date.today()
        agenda_items: List[Agenda] = []
        for offset in range(days):
            current_day = today + timedelta(days=offset)
            agenda_items.append(self.agenda_for(current_day))
        return agenda_items

    def stats(self) -> dict:
        by_priority = defaultdict(int)
        for task in self.tasks:
            by_priority[task.priority] += 1
        completed = sum(1 for task in self.tasks if task.completed)
        upcoming = sum(1 for task in self.tasks if (task.due and task.due.date() >= date.today() and not task.completed))
        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": completed,
            "upcoming_tasks": upcoming,
            "events": len(self.events),
            "by_priority": dict(sorted(by_priority.items())),
        }
