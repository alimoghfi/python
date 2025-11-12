"""Command line interface for the modern planner."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from typing import List, Optional

from .models import Agenda, Event, Task
from .services import PlannerService

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
]


def parse_date(value: str) -> datetime:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Could not parse date '{value}'.")


def parse_datetime(value: str) -> datetime:
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Could not parse datetime '{value}'.")


def parse_timedelta(value: str) -> timedelta:
    try:
        hours, minutes = value.split(":")
        return timedelta(hours=int(hours), minutes=int(minutes))
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError("Timedelta format must be HH:MM") from exc


def format_task(task: Task) -> str:
    due = task.due.strftime("%Y-%m-%d %H:%M") if task.due else "--"
    tags = f" [{' ,'.join(task.tags)}]" if task.tags else ""
    status = "✓" if task.completed else " "
    return f"[{status}] {task.uid} | {task.title} | due: {due} | priority: {task.priority}{tags}"


def format_event(event: Event) -> str:
    start = event.start.strftime("%Y-%m-%d %H:%M")
    end = event.end.strftime("%H:%M")
    location = f" @ {event.location}" if event.location else ""
    tags = f" [{' ,'.join(event.tags)}]" if event.tags else ""
    return f"{event.uid} | {event.title} | {start}-{end}{location}{tags}"


def format_agenda(agenda: Agenda) -> List[str]:
    lines = [agenda.summary(), "  Tasks:"]
    if agenda.tasks:
        lines.extend([f"    - {format_task(task)}" for task in agenda.tasks])
    else:
        lines.append("    (no tasks)")
    lines.append("  Events:")
    if agenda.events:
        lines.extend([f"    - {format_event(event)}" for event in agenda.events])
    else:
        lines.append("    (no events)")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A modern command line planner for tasks and events.")
    parser.add_argument("--storage", help="Path to the storage file (defaults to ~/.modern_planner/planner_data.json)")

    subparsers = parser.add_subparsers(dest="command")

    # Add task
    add_task = subparsers.add_parser("add-task", help="Add a new task")
    add_task.add_argument("title", help="Task title")
    add_task.add_argument("--due", type=parse_datetime, help="Due date/time")
    add_task.add_argument("--priority", type=int, default=3, help="Priority (1-5)")
    add_task.add_argument("--tags", nargs="*", default=[], help="Tags for grouping tasks")
    add_task.add_argument("--notes", help="Additional notes")

    # List tasks
    list_tasks = subparsers.add_parser("list-tasks", help="List tasks")
    list_tasks.add_argument("--all", action="store_true", help="Include completed tasks")

    # Complete task
    complete_task = subparsers.add_parser("complete", help="Mark a task as completed")
    complete_task.add_argument("uid", help="Task identifier")

    # Snooze task
    snooze_task = subparsers.add_parser("snooze", help="Snooze a task by HH:MM")
    snooze_task.add_argument("uid", help="Task identifier")
    snooze_task.add_argument("duration", type=parse_timedelta, help="Time to snooze, formatted as HH:MM")

    # Add event
    add_event = subparsers.add_parser("add-event", help="Add a new calendar event")
    add_event.add_argument("title", help="Event title")
    add_event.add_argument("start", type=parse_datetime, help="Start datetime")
    add_event.add_argument("end", type=parse_datetime, help="End datetime")
    add_event.add_argument("--location", help="Event location")
    add_event.add_argument("--tags", nargs="*", default=[], help="Tags for grouping events")
    add_event.add_argument("--notes", help="Additional notes")

    # List events
    list_events = subparsers.add_parser("list-events", help="List events")
    list_events.add_argument("--from", dest="start", type=parse_date, help="Start date filter")
    list_events.add_argument("--to", dest="end", type=parse_date, help="End date filter")

    # Agenda
    agenda = subparsers.add_parser("agenda", help="Show agenda for the coming days")
    agenda.add_argument("--days", type=int, default=3, help="Number of upcoming days to display")

    # Stats
    subparsers.add_parser("stats", help="Show planner statistics")

    return parser


def dispatch(args: argparse.Namespace, service: PlannerService) -> Optional[List[str]]:
    if args.command == "add-task":
        task = service.add_task(
            args.title,
            due=args.due,
            priority=args.priority,
            tags=args.tags,
            notes=args.notes,
        )
        return ["Task created:", f"  {format_task(task)}"]
    if args.command == "list-tasks":
        tasks = service.list_tasks(include_completed=args.all)
        if not tasks:
            return ["No tasks found."]
        return [format_task(task) for task in tasks]
    if args.command == "complete":
        task = service.complete_task(args.uid)
        return [f"Task {args.uid} completed."] if task else [f"Task {args.uid} not found."]
    if args.command == "snooze":
        task = service.snooze_task(args.uid, args.duration)
        return [f"Task {args.uid} snoozed by {args.duration}."] if task else [f"Task {args.uid} not found."]
    if args.command == "add-event":
        event = service.add_event(
            args.title,
            start=args.start,
            end=args.end,
            location=args.location,
            tags=args.tags,
            notes=args.notes,
        )
        return ["Event created:", f"  {format_event(event)}"]
    if args.command == "list-events":
        events = service.list_events(start_date=args.start.date() if args.start else None, end_date=args.end.date() if args.end else None)
        if not events:
            return ["No events found."]
        return [format_event(event) for event in events]
    if args.command == "agenda":
        agenda_items = service.upcoming_agenda(days=args.days)
        lines: List[str] = []
        for agenda_item in agenda_items:
            lines.extend(format_agenda(agenda_item))
            lines.append("")
        return lines[:-1] if lines else ["No agenda items found."]
    if args.command == "stats":
        stats = service.stats()
        lines = [
            "Planner statistics:",
            f"  Tasks: {stats['total_tasks']} (completed: {stats['completed_tasks']}, upcoming: {stats['upcoming_tasks']})",
            f"  Events: {stats['events']}",
            "  By priority:",
        ]
        lines.extend([f"    Priority {priority}: {count}" for priority, count in stats["by_priority"].items()])
        return lines
    return None


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    service = PlannerService(storage_path=args.storage)
    output = dispatch(args, service)
    if output:
        for line in output:
            print(line)
    elif output is None:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
