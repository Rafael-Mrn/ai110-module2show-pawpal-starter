"""PawPal+ logic layer.

Backend classes for tracking pets, their care tasks, owner availability,
and producing a daily plan. UI (Streamlit) should import from here.

Design notes:
  * Task is a recurring *template*; PlannedTask is a per-day *instance* that
    carries completion/timing state, so completion never leaks across days.
  * Scheduling is owner-level: one shared pool of free time across all pets, so
    the same minute can't be double-booked for two pets.
  * Availability is expressed as time *windows* (start, end) that the owner
    gives us. A task consumes its own duration_minutes out of a window; nothing
    about slot size is assumed here. The UI collects these windows.
  * build_daily_plan returns a DailyPlan so the rationale, assigned times, and
    deferred tasks survive instead of being thrown away.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

# Weekday name (first 3 letters, lowercased) -> Python's date.weekday() index.
WEEKDAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

# Recurrence interval -> number of days until the next occurrence. Anything not
# in here (e.g. "none") is treated as a one-off that does not repeat.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


@dataclass
class Task:
    """A recurring pet care responsibility (walk, feeding, meds, etc.).

    This is a *template*: it has no completion state and is never mutated by
    the planner. The scheduler stamps out per-day PlannedTask instances from it.
    """

    name: str
    category: str
    priority: int = 0
    duration_minutes: int = 0
    frequency_per_day: int = 1
    preferred_time_of_day: str | None = None  # "08:00" or None
    # How often this task repeats across days: "none", "daily", or "weekly".
    # Completing a recurring occurrence auto-creates the next one.
    recurrence: str = "none"


@dataclass
class PlannedTask:
    """A single occurrence of a Task on a specific day, with its own state."""

    task: Task
    due_time: datetime | None = None
    completed: bool = False
    # Which pet this occurrence is for. Set when the scheduler stamps it out,
    # so we can filter a plan's occurrences by pet name.
    pet: Pet | None = None

    def mark_complete(self) -> "PlannedTask | None":
        """Mark this occurrence done; return its next occurrence (None if one-off)."""
        self.completed = True
        return self.next_occurrence()

    def next_occurrence(self) -> "PlannedTask | None":
        """Return the next occurrence for a recurring task (daily +1d, weekly +7d), else None."""
        days = RECURRENCE_DAYS.get(self.task.recurrence)
        if days is None:
            return None
        base = self.due_time if self.due_time is not None else datetime.now()
        return PlannedTask(
            task=self.task,
            due_time=base + timedelta(days=days),
            pet=self.pet,
        )

    def is_overdue(self) -> bool:
        """Return True if past due_time and not completed."""
        return (
            self.due_time is not None
            and not self.completed
            and datetime.now() > self.due_time
        )

    def send_alert(self) -> None:
        """Notify the owner about this occurrence."""
        when = self.due_time.strftime("%H:%M") if self.due_time else "soon"
        print(f"[PawPal+] Reminder: '{self.task.name}' is due at {when}.")


@dataclass(eq=False)
class Pet:
    """A pet being cared for, plus its recurring care-task templates.

    eq=False so identity (not field values) is used for equality, letting an
    owner hold two pets with the same name/type without remove_pet ambiguity.
    """

    name: str
    pet_type: str
    breed: str = ""
    medical_conditions: list[str] = field(default_factory=list)
    weight: float = 0.0
    tasks: list[Task] = field(default_factory=list)
    pet_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def add_task(self, task: Task) -> None:
        """Attach a recurring care task to this pet."""
        self.tasks.append(task)

    def get_care_suggestions(self) -> list[str]:
        """Return candidate health/care suggestions based on this pet's attributes."""
        suggestions: list[str] = []
        for condition in self.medical_conditions:
            suggestions.append(
                f"Monitor {self.name}'s {condition}; check with the vet about managing it."
            )
        if self.weight <= 0:
            suggestions.append(f"Record {self.name}'s weight to tailor care.")
        if self.breed:
            suggestions.append(f"Look up breed-specific needs for a {self.breed}.")
        suggestions.append(f"Add an enrichment activity to keep {self.name} stimulated.")
        return suggestions


@dataclass
class Owner:
    """The pet owner, their weekly availability, and the pets they own."""

    name: str
    # day -> list of (start, end) windows the owner is free, e.g.
    #   {"Mon": [("08:00", "10:00"), ("18:00", "19:00")]}
    availability: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    contacts: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet by identity (see Pet.pet_id)."""
        self.pets = [p for p in self.pets if p.pet_id != pet.pet_id]

    def update_availability(self, day: str, windows: list[tuple[str, str]]) -> None:
        """Set the free (start, end) windows for a given day."""
        self.availability[day] = [tuple(w) for w in windows]


@dataclass
class DailyPlan:
    """The output of a scheduling run: what got scheduled, what didn't, and why."""

    day: str
    scheduled: list[PlannedTask] = field(default_factory=list)
    deferred: list[PlannedTask] = field(default_factory=list)  # didn't fit available time
    suggestions: list[str] = field(default_factory=list)  # extras when time is left over
    rationale: str = ""


@dataclass
class _FreeWindow:
    """A window of free time on a given day, with a moving cursor.

    `cursor` is the next still-free moment in the window; it advances as tasks
    are placed. The leftover (end - cursor) is the unbooked time.
    """

    start: datetime
    end: datetime
    cursor: datetime


class Scheduler:
    """Produces an owner-level daily plan across all pets and one pool of time."""

    def __init__(self, owner: Owner) -> None:
        # Read availability through the owner so the two never drift apart.
        self.owner = owner

    def build_daily_plan(self, day: str) -> DailyPlan:
        """Build a DailyPlan placing all pets' tasks into the owner's free windows by priority."""
        plan_date = self._date_for_day(day)
        windows = self._free_windows(day, plan_date)
        scheduled: list[PlannedTask] = []
        deferred: list[PlannedTask] = []

        # 1. Expand every pet's recurring templates into per-day occurrences.
        occurrences: list[PlannedTask] = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                for _ in range(max(1, task.frequency_per_day)):
                    occurrences.append(PlannedTask(task=task, pet=pet))

        # 2. Highest priority first; sorted() is stable so ties keep input order.
        occurrences.sort(key=lambda p: p.task.priority, reverse=True)

        # 3. Place each occurrence into the shared free windows.
        for planned in occurrences:
            start = self.assign_time_of_day(planned, day, windows)
            if start is None:
                deferred.append(planned)
            else:
                planned.due_time = start
                scheduled.append(planned)

        # 4. Offer care suggestions only when free time is actually left.
        free_minutes = sum(
            int((w.end - w.cursor).total_seconds() // 60) for w in windows
        )
        suggestions: list[str] = []
        for pet in self.owner.pets:
            suggestions.extend(self.suggest_activities(pet, free_minutes))

        plan = DailyPlan(
            day=day, scheduled=scheduled, deferred=deferred, suggestions=suggestions
        )
        plan.rationale = self.explain_plan(plan)
        return plan

    def sort_by_time(self, tasks=None) -> list:
        """Return tasks sorted by preferred time of day, earliest first (untimed last).

        Sorts the owner's tasks when `tasks` is None. 'HH:MM' strings are
        zero-padded, so the lambda key can compare them as plain strings.
        """
        if tasks is None:
            tasks = [t for pet in self.owner.pets for t in pet.tasks]
        return sorted(tasks, key=lambda item: self._time_key(item))

    def filter_tasks(self, tasks, pet_name=None, completed=None) -> list:
        """Return the tasks matching the given pet name and/or completion status.

        Completion lives on PlannedTask, so a `completed` filter only matches
        occurrences, not bare Task templates. No criteria returns a copy.
        """
        result = list(tasks)
        if pet_name is not None:
            result = [t for t in result if self._pet_name(t) == pet_name]
        if completed is not None:
            result = [
                t
                for t in result
                if isinstance(t, PlannedTask) and t.completed == completed
            ]
        return result

    def detect_conflicts(self, planned_tasks) -> list[str]:
        """Return warning messages for any occurrences whose scheduled times overlap.

        Lightweight pairwise check across all pets; occurrences with no due_time
        are skipped. Returns an empty list when there are none — never raises.
        """
        timed = [p for p in planned_tasks if p.due_time is not None]
        warnings: list[str] = []
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                a_end = a.due_time + timedelta(
                    minutes=max(0, a.task.duration_minutes)
                )
                b_end = b.due_time + timedelta(
                    minutes=max(0, b.task.duration_minutes)
                )
                # Half-open overlap test: touching end-to-start is not a clash.
                if a.due_time < b_end and b.due_time < a_end:
                    warnings.append(self._conflict_message(a, a_end, b, b_end))
        return warnings

    @staticmethod
    def _conflict_message(a, a_end, b, b_end) -> str:
        """Build a human-readable warning for an overlapping pair."""
        def label(p, end) -> str:
            pet = p.pet.name if p.pet else "?"
            span = f"{p.due_time:%H:%M}-{end:%H:%M}"
            return f"'{p.task.name}' ({pet}, {span})"

        return f"WARNING: {label(a, a_end)} overlaps {label(b, b_end)}"

    @staticmethod
    def _time_key(item) -> str:
        """Return the 'HH:MM' sort key for a Task or PlannedTask."""
        task = item.task if isinstance(item, PlannedTask) else item
        return task.preferred_time_of_day or "99:99"

    def _pet_name(self, item) -> str | None:
        """Return the owning pet's name for a Task or PlannedTask, or None."""
        if isinstance(item, PlannedTask):
            return item.pet.name if item.pet else None
        # Bare Task template: find which pet's list holds this exact object.
        for pet in self.owner.pets:
            if any(item is t for t in pet.tasks):
                return pet.name
        return None

    def assign_time_of_day(
        self, planned: PlannedTask, day: str, windows: list[_FreeWindow]
    ) -> datetime | None:
        """Reserve the task's duration in a free window and return its start, or None if it doesn't fit."""
        duration = timedelta(minutes=max(0, planned.task.duration_minutes))

        # 1. Honor an exact preferred start time when it fits in a window.
        preferred = planned.task.preferred_time_of_day
        if preferred:
            pref_time = self._parse_time(preferred)
            if pref_time is not None:
                for w in windows:
                    pref_dt = datetime.combine(w.start.date(), pref_time)
                    if w.cursor <= pref_dt and pref_dt + duration <= w.end:
                        w.cursor = pref_dt + duration
                        return pref_dt

        # 2. First-fit: earliest window with enough remaining time.
        for w in windows:
            if w.cursor + duration <= w.end:
                start = w.cursor
                w.cursor = w.cursor + duration
                return start
        return None

    def suggest_activities(self, pet: Pet, free_minutes: int) -> list[str]:
        """Return the pet's care suggestions, but only when free time is left over."""
        if free_minutes <= 0:
            return []
        return pet.get_care_suggestions()

    def explain_plan(self, plan: DailyPlan) -> str:
        """Explain why the scheduler chose this plan (priorities, available time)."""
        lines = [f"Plan for {plan.day}:"]
        if plan.scheduled:
            lines.append(f"Scheduled {len(plan.scheduled)} task(s), highest priority first:")
            for p in plan.scheduled:
                when = p.due_time.strftime("%H:%M") if p.due_time else "unscheduled"
                lines.append(
                    f"  - {when}  {p.task.name} "
                    f"(priority {p.task.priority}, {p.task.duration_minutes}min)"
                )
        if plan.deferred:
            lines.append(f"Deferred {len(plan.deferred)} task(s) — not enough free time:")
            for p in plan.deferred:
                lines.append(
                    f"  - {p.task.name} "
                    f"(priority {p.task.priority}, {p.task.duration_minutes}min)"
                )
        if plan.suggestions:
            lines.append("Spare time available — optional suggestions:")
            for s in plan.suggestions:
                lines.append(f"  - {s}")
        return "\n".join(lines)

    # --- helpers -------------------------------------------------------------

    def _free_windows(self, day: str, plan_date: date) -> list[_FreeWindow]:
        """Build mutable free-time windows for `day`, sorted by start time."""
        windows: list[_FreeWindow] = []
        for start_str, end_str in self.owner.availability.get(day, []):
            start = datetime.combine(plan_date, self._parse_time(start_str))
            end = datetime.combine(plan_date, self._parse_time(end_str))
            windows.append(_FreeWindow(start=start, end=end, cursor=start))
        windows.sort(key=lambda w: w.start)
        return windows

    @staticmethod
    def _parse_time(value: str):
        """Parse an 'HH:MM' string into a time, or None if malformed."""
        try:
            return datetime.strptime(value, "%H:%M").time()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _date_for_day(day: str) -> date:
        """Return the next date (today or later) matching weekday `day`, else today."""
        target = WEEKDAY_INDEX.get(day.strip().lower()[:3])
        today = date.today()
        if target is None:
            return today
        days_ahead = (target - today.weekday()) % 7
        return today + timedelta(days=days_ahead)
