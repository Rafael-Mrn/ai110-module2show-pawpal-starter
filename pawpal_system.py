"""PawPal+ logic layer.

Backend classes for tracking pets, their care tasks, owner availability,
and producing a daily plan. UI (Streamlit) should import from here.

Skeleton generated from diagrams/uml_draft.mmd — method bodies are stubs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Task:
    """A single pet care responsibility (walk, feeding, meds, etc.)."""

    name: str
    category: str
    priority: int = 0
    duration_minutes: int = 0
    completed: bool = False
    due_time: datetime | None = None

    def mark_complete(self) -> None:
        """Mark this task as done."""
        raise NotImplementedError

    def is_overdue(self) -> bool:
        """Return True if the task is past its due time and not completed."""
        raise NotImplementedError

    def send_alert(self) -> None:
        """Notify the owner about this task."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet being cared for, plus its list of care tasks."""

    name: str
    pet_type: str
    breed: str = ""
    medical_conditions: list[str] = field(default_factory=list)
    weight: float = 0.0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def get_care_suggestions(self) -> list[str]:
        """Return health/care suggestions based on the pet's info."""
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
        """Remove a pet from this owner."""
        raise NotImplementedError

    def update_availability(self, day: str, times: list[str]) -> None:
        """Set the free time slots for a given day."""
        raise NotImplementedError


class Scheduler:
    """Produces a daily plan from an owner's availability and a pet's tasks."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.weekly_availability: dict[str, list[str]] = owner.availability

    def build_daily_plan(self, pet: Pet, day: str) -> list[Task]:
        """Return an ordered list of tasks to do for the pet on a given day."""
        raise NotImplementedError

    def assign_time_of_day(self, task: Task) -> datetime:
        """Pick a time slot for the task based on availability."""
        raise NotImplementedError

    def suggest_activities(self, pet: Pet) -> list[str]:
        """Suggest extra care advice/activities beyond required tasks."""
        raise NotImplementedError

    def explain_plan(self) -> str:
        """Explain why the scheduler chose this plan."""
        raise NotImplementedError
