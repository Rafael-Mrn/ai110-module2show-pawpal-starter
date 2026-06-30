"""Simple tests for the PawPal+ logic layer."""

import os
import sys

# Make the project root importable so `pawpal_system` is found when pytest
# runs from inside the tests/ folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, PlannedTask, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task occurrence from not-done to done."""
    planned = PlannedTask(task=Task("Walk", "exercise"))

    assert planned.completed is False  # starts incomplete

    planned.mark_complete()

    assert planned.completed is True  # now marked done


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet grows that pet's task list by one."""
    pet = Pet(name="Rex", pet_type="dog")

    assert len(pet.tasks) == 0  # no tasks yet

    pet.add_task(Task("Feed", "feeding"))

    assert len(pet.tasks) == 1  # one task after adding
