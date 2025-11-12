"""Tkinter user interface for the modern planner application."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

from .services import PlannerService

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class PlannerApp(tk.Tk):
    """Main window for the planner application."""

    def __init__(self, service: Optional[PlannerService] = None) -> None:
        super().__init__()
        self.title("Modern Planner")
        self.geometry("900x600")
        self.minsize(800, 500)

        self.service = service or PlannerService()

        self._create_widgets()
        self.refresh_all()

    # ------------------------------------------------------------------
    # UI creation helpers
    def _create_widgets(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tasks_frame = ttk.Frame(notebook, padding=10)
        self.events_frame = ttk.Frame(notebook, padding=10)
        notebook.add(self.tasks_frame, text="Tasks")
        notebook.add(self.events_frame, text="Events")

        self._create_tasks_tab()
        self._create_events_tab()

        self.status_var = tk.StringVar(self, "")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 5))

    def _create_tasks_tab(self) -> None:
        columns = ("title", "due", "priority", "tags", "completed")
        self.tasks_tree = ttk.Treeview(
            self.tasks_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "title": "Title",
            "due": "Due",
            "priority": "Priority",
            "tags": "Tags",
            "completed": "Completed",
        }
        for column, text in headings.items():
            self.tasks_tree.heading(column, text=text)
            self.tasks_tree.column(column, width=120, stretch=True)
        self.tasks_tree.column("title", width=220)
        self.tasks_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        button_bar = ttk.Frame(self.tasks_frame)
        button_bar.pack(fill=tk.X, pady=10)

        add_task_btn = ttk.Button(button_bar, text="Add Task", command=self.open_add_task_dialog)
        add_task_btn.pack(side=tk.LEFT)

        complete_task_btn = ttk.Button(button_bar, text="Mark Complete", command=self.complete_selected_task)
        complete_task_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(button_bar, text="Refresh", command=self.refresh_tasks)
        refresh_btn.pack(side=tk.LEFT)

    def _create_events_tab(self) -> None:
        columns = ("title", "start", "end", "location", "tags")
        self.events_tree = ttk.Treeview(
            self.events_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "title": "Title",
            "start": "Start",
            "end": "End",
            "location": "Location",
            "tags": "Tags",
        }
        for column, text in headings.items():
            self.events_tree.heading(column, text=text)
            self.events_tree.column(column, width=140, stretch=True)
        self.events_tree.column("title", width=220)
        self.events_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        button_bar = ttk.Frame(self.events_frame)
        button_bar.pack(fill=tk.X, pady=10)

        add_event_btn = ttk.Button(button_bar, text="Add Event", command=self.open_add_event_dialog)
        add_event_btn.pack(side=tk.LEFT)

        refresh_btn = ttk.Button(button_bar, text="Refresh", command=self.refresh_events)
        refresh_btn.pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # Refresh logic
    def refresh_all(self) -> None:
        self.refresh_tasks()
        self.refresh_events()
        self.update_status()

    def refresh_tasks(self) -> None:
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        for task in self.service.list_tasks(include_completed=True):
            due_display = task.due.strftime(DATE_TIME_FORMAT) if task.due else ""
            tags_display = ", ".join(task.tags)
            self.tasks_tree.insert(
                "",
                tk.END,
                iid=task.uid,
                values=(task.title, due_display, task.priority, tags_display, "Yes" if task.completed else "No"),
            )
        self.update_status()

    def refresh_events(self) -> None:
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)

        for event in self.service.list_events():
            start_display = event.start.strftime(DATE_TIME_FORMAT)
            end_display = event.end.strftime(DATE_TIME_FORMAT)
            tags_display = ", ".join(event.tags)
            self.events_tree.insert(
                "",
                tk.END,
                iid=event.uid,
                values=(event.title, start_display, end_display, event.location or "", tags_display),
            )
        self.update_status()

    def update_status(self) -> None:
        stats = self.service.stats()
        status_text = (
            f"Tasks: {stats['total_tasks']} (Completed: {stats['completed_tasks']}, Upcoming: {stats['upcoming_tasks']})"
            f" | Events: {stats['events']}"
        )
        self.status_var.set(status_text)

    # ------------------------------------------------------------------
    # Task actions
    def complete_selected_task(self) -> None:
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showinfo("Complete Task", "Please select a task to mark as completed.")
            return

        uid = selection[0]
        task = self.service.complete_task(uid)
        if task is None:
            messagebox.showerror("Complete Task", "The selected task could not be updated.")
            return

        self.refresh_tasks()

    def open_add_task_dialog(self) -> None:
        dialog = TaskDialog(self, title="Add Task")
        self.wait_window(dialog)
        if dialog.result:
            title, due, priority, tags, notes = dialog.result
            try:
                due_dt = datetime.strptime(due, DATE_TIME_FORMAT) if due else None
            except ValueError:
                messagebox.showerror("Invalid Due Date", f"Please enter due date as YYYY-MM-DD HH:MM.")
                return
            try:
                priority_value = int(priority) if priority else 3
            except ValueError:
                messagebox.showerror("Invalid Priority", "Priority must be a number.")
                return
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
            self.service.add_task(title, due=due_dt, priority=priority_value, tags=tags_list, notes=notes or None)
            self.refresh_tasks()

    # ------------------------------------------------------------------
    # Event actions
    def open_add_event_dialog(self) -> None:
        dialog = EventDialog(self, title="Add Event")
        self.wait_window(dialog)
        if dialog.result:
            title, start, end, location, tags, notes = dialog.result
            try:
                start_dt = datetime.strptime(start, DATE_TIME_FORMAT)
                end_dt = datetime.strptime(end, DATE_TIME_FORMAT)
            except ValueError:
                messagebox.showerror("Invalid Date", "Start and end must use YYYY-MM-DD HH:MM format.")
                return
            if end_dt <= start_dt:
                messagebox.showerror("Invalid Date", "End time must be after start time.")
                return
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
            self.service.add_event(
                title,
                start=start_dt,
                end=end_dt,
                location=location or None,
                tags=tags_list,
                notes=notes or None,
            )
            self.refresh_events()


class _BaseDialog(tk.Toplevel):
    """Base dialog window with common layout utilities."""

    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        self.result = None
        self._body = ttk.Frame(self, padding=20)
        self._body.pack(fill=tk.BOTH, expand=True)
        self._create_body()
        self._create_buttons()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _create_body(self) -> None:
        raise NotImplementedError

    def _create_buttons(self) -> None:
        button_bar = ttk.Frame(self._body)
        button_bar.pack(fill=tk.X, pady=(15, 0))

        submit_btn = ttk.Button(button_bar, text="Save", command=self._submit)
        submit_btn.pack(side=tk.RIGHT)

        cancel_btn = ttk.Button(button_bar, text="Cancel", command=self._cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def _submit(self) -> None:  # pragma: no cover - Tkinter callback
        raise NotImplementedError

    def _cancel(self) -> None:  # pragma: no cover - Tkinter callback
        self.result = None
        self.destroy()


class TaskDialog(_BaseDialog):
    """Dialog for creating a new task."""

    def _create_body(self) -> None:
        form = ttk.Frame(self._body)
        form.pack(fill=tk.BOTH, expand=True)

        self._title_var = tk.StringVar()
        self._due_var = tk.StringVar()
        self._priority_var = tk.StringVar(value="3")
        self._tags_var = tk.StringVar()

        fields = (
            ("Title", self._title_var),
            ("Due (YYYY-MM-DD HH:MM)", self._due_var),
            ("Priority", self._priority_var),
            ("Tags (comma separated)", self._tags_var),
        )
        for idx, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky=tk.W, pady=5)
            ttk.Entry(form, textvariable=variable, width=40).grid(row=idx, column=1, sticky=tk.EW, pady=5)

        ttk.Label(form, text="Notes").grid(row=len(fields), column=0, sticky=tk.NW, pady=5)
        self._notes = tk.Text(form, width=40, height=5)
        self._notes.grid(row=len(fields), column=1, sticky=tk.EW, pady=5)

        form.columnconfigure(1, weight=1)

    def _submit(self) -> None:  # pragma: no cover - Tkinter callback
        title = self._title_var.get().strip()
        if not title:
            messagebox.showerror("Missing Title", "Task title is required.")
            return
        due = self._due_var.get().strip()
        priority = self._priority_var.get().strip()
        tags = self._tags_var.get().strip()
        notes = self._notes.get("1.0", tk.END).strip()
        self.result = (title, due, priority, tags, notes)
        self.destroy()


class EventDialog(_BaseDialog):
    """Dialog for creating a new event."""

    def _create_body(self) -> None:
        form = ttk.Frame(self._body)
        form.pack(fill=tk.BOTH, expand=True)

        self._title_var = tk.StringVar()
        self._start_var = tk.StringVar()
        self._end_var = tk.StringVar()
        self._location_var = tk.StringVar()
        self._tags_var = tk.StringVar()

        fields = (
            ("Title", self._title_var),
            ("Start (YYYY-MM-DD HH:MM)", self._start_var),
            ("End (YYYY-MM-DD HH:MM)", self._end_var),
            ("Location", self._location_var),
            ("Tags (comma separated)", self._tags_var),
        )
        for idx, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky=tk.W, pady=5)
            ttk.Entry(form, textvariable=variable, width=40).grid(row=idx, column=1, sticky=tk.EW, pady=5)

        ttk.Label(form, text="Notes").grid(row=len(fields), column=0, sticky=tk.NW, pady=5)
        self._notes = tk.Text(form, width=40, height=5)
        self._notes.grid(row=len(fields), column=1, sticky=tk.EW, pady=5)

        form.columnconfigure(1, weight=1)

    def _submit(self) -> None:  # pragma: no cover - Tkinter callback
        title = self._title_var.get().strip()
        if not title:
            messagebox.showerror("Missing Title", "Event title is required.")
            return
        start = self._start_var.get().strip()
        end = self._end_var.get().strip()
        location = self._location_var.get().strip()
        tags = self._tags_var.get().strip()
        notes = self._notes.get("1.0", tk.END).strip()
        self.result = (title, start, end, location, tags, notes)
        self.destroy()


def launch_app() -> None:
    """Create the Tkinter root window and start the application loop."""

    app = PlannerApp()
    app.mainloop()
