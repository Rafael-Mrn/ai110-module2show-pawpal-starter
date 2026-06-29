"""PawPal+ logic layer.

Backend classes for tracking pets, their care tasks, owner availability,
and producing a daily plan. UI (Streamlit) should import from here.

Skeleton generated from diagrams/uml_draft.mmd — method bodies are stubs.

Design notes:
  * Task is a recurring *template*; PlannedTask is a per-day *instance* that
    carries completion/timing state, so completion never leaks across days.
  * Scheduling is owner-level: one shared time budget across all pets, so the
    same slot can't be double-booked for two pets.
  * build_daily_plan returns a DailyPlan so the rationale, assigned times, and
    deferred tasks survive instead of being thrown away.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


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
    preferred_time_of_day: str | None = None  # "morning" / "08:00" / None


@dataclass
class PlannedTask:
    """A single occurrence of a Task on a specific day, with its own state."""

    task: Task
    due_time: datetime | None = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this occurrence as done (does not touch the Task template)."""
        raise NotImplementedError

    def is_overdue(self) -> bool:
        """Return True if past due_time and not completed."""
        raise NotImplementedError

    def send_alert(self) -> None:
        """Notify the owner about this occurrence."""
        raise NotImplementedError


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
        raise NotImplementedError

    def get_care_suggestions(self) -> list[str]:
        """Health/care suggestions derived from this pet's own attributes.

        Returns candidate suggestions only; the Scheduler decides which (if any)
        actually fit in the day's open time via suggest_activities().
        """
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner, their weekly availability, and the pets they own."""

    name: str
    # day -> list of free time slots, e.g. {"Mon": ["08:00", "18:00"]}
    availability: dict[str, list[str]] = field(default_factory=dict)
    contacts: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet by identity (see Pet.pet_id)."""
        raise NotImplementedError

    def update_availability(self, day: str, times: list[str]) -> None:
        """Set the free time slots for a given day."""
        raise NotImplementedError


@dataclass
class DailyPlan:
    """The output of a scheduling run: what got scheduled, what didn't, and why."""

    day: str
    scheduled: list[PlannedTask] = field(default_factory=list)
    deferred: list[PlannedTask] = field(default_factory=list)  # didn't fit time budget
    suggestions: list[str] = field(default_factory=list)  # extras that fit spare time
    rationale: str = ""


class Scheduler:
    """Produces an owner-level daily plan across all pets and one time budget."""

    def __init__(self, owner: Owner) -> None:
        # Read availability through the owner so the two never drift apart.
        self.owner = owner

    def build_daily_plan(self, day: str) -> DailyPlan:
        """Plan every pet's tasks for `day` against the owner's shared time budget.

        Gathers tasks from all owner.pets, expands them into PlannedTasks,
        places them by priority within available minutes, defers overflow, and
        records the rationale.
        """
        raise NotImplementedError

    def assign_time_of_day(
        self, planned: PlannedTask, day: str, taken: list[datetime]
    ) -> datetime | None:
        """Pick a free slot for `planned`, avoiding `taken` slots.

        Returns the chosen time, or None if no slot is available that day.
        """
        raise NotImplementedError

    def suggest_activities(self, pet: Pet, free_minutes: int) -> list[str]:
        """Filter pet.get_care_suggestions() down to what fits in free_minutes.

        Suggestions are only surfaced to the user when there is open time left.
        """
        raise NotImplementedError

    def explain_plan(self, plan: DailyPlan) -> str:
        """Explain why the scheduler chose this plan (priorities, time budget)."""
        raise NotImplementedError
