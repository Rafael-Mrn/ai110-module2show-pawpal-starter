"""Automated test suite for the PawPal+ logic layer (pawpal_system.py).

Covers the five core behaviors and the edge cases that actually break pet
schedulers: empty inputs, exact-time ties, half-open boundary overlaps, mixing
timed/untimed tasks, and capacity overflow.

Run with:  pytest test_pawpal.py -v
"""

from datetime import date, datetime, time, timedelta

import pytest

from pawpal_system import (
    DailyPlan,
    Owner,
    Pet,
    PlannedTask,
    Scheduler,
    Task,
)

# The scheduler plans for the next matching weekday, so anchor tests on that
# same date to keep due_time comparisons deterministic.
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def today_day_name() -> str:
    return WEEKDAY_NAMES[date.today().weekday()]


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def owner() -> Owner:
    """An owner free 07:00-09:00 and 17:30-19:00 today, no pets yet."""
    o = Owner(name="Rafael")
    o.update_availability(today_day_name(), [("07:00", "09:00"), ("17:30", "19:00")])
    return o


@pytest.fixture
def scheduler(owner: Owner) -> Scheduler:
    return Scheduler(owner)


def make_planned(name: str, hhmm: str, duration: int, pet: Pet) -> PlannedTask:
    """Build a timed PlannedTask on today's date for conflict tests."""
    t = Task(name, "misc", duration_minutes=duration, preferred_time_of_day=hhmm)
    hh, mm = map(int, hhmm.split(":"))
    return PlannedTask(task=t, due_time=datetime.combine(date.today(), time(hh, mm)), pet=pet)


# --------------------------------------------------------------------------- #
# 1. Sorting correctness
# --------------------------------------------------------------------------- #
class TestSorting:
    def test_tasks_returned_in_chronological_order(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog")
        # Added deliberately out of clock order.
        pet.add_task(Task("Evening", "feeding", preferred_time_of_day="18:00"))
        pet.add_task(Task("Morning", "walk", preferred_time_of_day="07:00"))
        pet.add_task(Task("Noon", "play", preferred_time_of_day="12:30"))
        owner.add_pet(pet)

        times = [t.preferred_time_of_day for t in scheduler.sort_by_time()]
        assert times == ["07:00", "12:30", "18:00"]

    def test_untimed_tasks_sort_last(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(Task("No time", "misc", preferred_time_of_day=None))
        pet.add_task(Task("Early", "walk", preferred_time_of_day="06:00"))
        owner.add_pet(pet)

        names = [t.name for t in scheduler.sort_by_time()]
        assert names == ["Early", "No time"]

    def test_same_time_sort_is_stable(self, scheduler, owner):
        """Ties must preserve insertion order so the UI doesn't reshuffle."""
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(Task("First", "a", preferred_time_of_day="08:00"))
        pet.add_task(Task("Second", "b", preferred_time_of_day="08:00"))
        pet.add_task(Task("Third", "c", preferred_time_of_day="08:00"))
        owner.add_pet(pet)

        assert [t.name for t in scheduler.sort_by_time()] == ["First", "Second", "Third"]

    def test_sort_empty_returns_empty(self, scheduler):
        assert scheduler.sort_by_time([]) == []


# --------------------------------------------------------------------------- #
# 2. Recurrence logic
# --------------------------------------------------------------------------- #
class TestRecurrence:
    def test_daily_completion_creates_task_for_next_day(self):
        due = datetime(2026, 7, 6, 7, 0)
        p = PlannedTask(task=Task("Walk", "walk", recurrence="daily"), due_time=due)

        nxt = p.mark_complete()

        assert p.completed is True
        assert nxt is not None
        assert nxt.due_time == due + timedelta(days=1)
        assert nxt.completed is False  # the new occurrence starts fresh
        assert nxt.task is p.task  # same template reused

    def test_weekly_completion_advances_seven_days(self):
        due = datetime(2026, 7, 6, 18, 0)
        p = PlannedTask(task=Task("Bath", "grooming", recurrence="weekly"), due_time=due)

        nxt = p.mark_complete()
        assert nxt is not None
        assert nxt.due_time == due + timedelta(days=7)

    def test_one_off_task_does_not_repeat(self):
        p = PlannedTask(
            task=Task("Vet visit", "medical", recurrence="none"),
            due_time=datetime(2026, 7, 6, 9, 0),
        )
        assert p.mark_complete() is None
        assert p.completed is True

    def test_next_occurrence_preserves_pet(self):
        pet = Pet(name="Mochi", pet_type="cat")
        p = PlannedTask(
            task=Task("Meds", "medical", recurrence="daily"),
            due_time=datetime(2026, 7, 6, 7, 30),
            pet=pet,
        )
        assert p.mark_complete().pet is pet

    def test_recurring_task_with_no_due_time_bases_next_on_now(self):
        """When due_time is None, next_occurrence falls back to datetime.now().

        We can't freeze the clock without a new dependency, so bracket the call
        with real now() readings and assert the result lands one day past that
        window — deterministic to within the test's own runtime.
        """
        p = PlannedTask(task=Task("Walk", "walk", recurrence="daily"), due_time=None)

        before = datetime.now()
        nxt = p.mark_complete()
        after = datetime.now()

        assert nxt is not None
        assert before + timedelta(days=1) <= nxt.due_time <= after + timedelta(days=1)

    def test_one_off_with_no_due_time_still_returns_none(self):
        """recurrence='none' short-circuits before touching now(), so due_time
        being None must not matter."""
        p = PlannedTask(task=Task("Vet", "medical", recurrence="none"), due_time=None)
        assert p.mark_complete() is None


# --------------------------------------------------------------------------- #
# 3. Conflict detection
# --------------------------------------------------------------------------- #
class TestConflictDetection:
    def test_two_tasks_at_exact_same_time_conflict(self, scheduler):
        rex = Pet(name="Rex", pet_type="dog")
        mochi = Pet(name="Mochi", pet_type="cat")
        a = make_planned("Play", "08:00", 20, rex)
        b = make_planned("Brush", "08:00", 15, mochi)

        warnings = scheduler.detect_conflicts([a, b])
        assert len(warnings) == 1
        assert "overlaps" in warnings[0]

    def test_overlapping_ranges_conflict(self, scheduler):
        rex = Pet(name="Rex", pet_type="dog")
        # 08:00-08:30 vs 08:15-08:45 overlap.
        a = make_planned("Walk", "08:00", 30, rex)
        b = make_planned("Feed", "08:15", 30, rex)
        assert len(scheduler.detect_conflicts([a, b])) == 1

    def test_touching_end_to_start_is_not_a_conflict(self, scheduler):
        """Half-open: A ends exactly when B starts -> no clash."""
        rex = Pet(name="Rex", pet_type="dog")
        a = make_planned("Walk", "08:00", 30, rex)  # 08:00-08:30
        b = make_planned("Feed", "08:30", 15, rex)  # 08:30-08:45
        assert scheduler.detect_conflicts([a, b]) == []

    def test_non_overlapping_tasks_no_conflict(self, scheduler):
        rex = Pet(name="Rex", pet_type="dog")
        a = make_planned("Walk", "08:00", 20, rex)
        b = make_planned("Feed", "12:00", 20, rex)
        assert scheduler.detect_conflicts([a, b]) == []

    def test_untimed_occurrences_skipped(self, scheduler):
        rex = Pet(name="Rex", pet_type="dog")
        timed = make_planned("Walk", "08:00", 20, rex)
        untimed = PlannedTask(task=Task("Whenever", "misc"), due_time=None, pet=rex)
        assert scheduler.detect_conflicts([timed, untimed]) == []

    def test_empty_list_never_raises(self, scheduler):
        assert scheduler.detect_conflicts([]) == []


# --------------------------------------------------------------------------- #
# 4. Priority scheduling & deferral (build_daily_plan)
# --------------------------------------------------------------------------- #
class TestDailyPlan:
    def test_higher_priority_scheduled_before_lower(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(Task("Low", "misc", priority=1, duration_minutes=30))
        pet.add_task(Task("High", "medical", priority=10, duration_minutes=30))
        owner.add_pet(pet)

        plan = scheduler.build_daily_plan(today_day_name())
        assert [p.task.name for p in plan.scheduled][0] == "High"

    def test_generated_plan_has_no_internal_conflicts(self, scheduler, owner):
        rex = Pet(name="Rex", pet_type="dog")
        mochi = Pet(name="Mochi", pet_type="cat")
        rex.add_task(Task("Walk", "walk", priority=6, duration_minutes=45))
        mochi.add_task(Task("Meds", "medical", priority=10, duration_minutes=10))
        owner.add_pet(rex)
        owner.add_pet(mochi)

        plan = scheduler.build_daily_plan(today_day_name())
        assert scheduler.detect_conflicts(plan.scheduled) == []

    def test_tasks_over_capacity_are_deferred(self, scheduler, owner):
        """Windows hold 3.5h; ask for 5x90min = 7.5h so some must defer."""
        pet = Pet(name="Rex", pet_type="dog")
        for i in range(5):
            pet.add_task(Task(f"Big{i}", "misc", priority=5, duration_minutes=90))
        owner.add_pet(pet)

        plan = scheduler.build_daily_plan(today_day_name())
        assert len(plan.deferred) > 0
        assert len(plan.scheduled) + len(plan.deferred) == 5

    def test_preferred_time_is_honored_when_it_fits(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(
            Task("Walk", "walk", priority=5, duration_minutes=30,
                 preferred_time_of_day="08:00")
        )
        owner.add_pet(pet)

        plan = scheduler.build_daily_plan(today_day_name())
        assert plan.scheduled[0].due_time.strftime("%H:%M") == "08:00"

    def test_frequency_per_day_creates_multiple_occurrences(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(Task("Walk", "walk", priority=5, duration_minutes=15,
                          frequency_per_day=3))
        owner.add_pet(pet)

        plan = scheduler.build_daily_plan(today_day_name())
        assert len(plan.scheduled) + len(plan.deferred) == 3


# --------------------------------------------------------------------------- #
# 5. Filtering
# --------------------------------------------------------------------------- #
class TestFiltering:
    def _plan_with_two_pets(self, scheduler, owner):
        rex = Pet(name="Rex", pet_type="dog")
        mochi = Pet(name="Mochi", pet_type="cat")
        rex.add_task(Task("Walk", "walk", priority=6, duration_minutes=20))
        mochi.add_task(Task("Meds", "medical", priority=10, duration_minutes=10))
        owner.add_pet(rex)
        owner.add_pet(mochi)
        return scheduler.build_daily_plan(today_day_name())

    def test_filter_by_pet_name(self, scheduler, owner):
        plan = self._plan_with_two_pets(scheduler, owner)
        mochi_only = scheduler.filter_tasks(plan.scheduled, pet_name="Mochi")
        assert mochi_only  # non-empty
        assert all(p.pet.name == "Mochi" for p in mochi_only)

    def test_filter_by_completion_status(self, scheduler, owner):
        plan = self._plan_with_two_pets(scheduler, owner)
        plan.scheduled[0].mark_complete()

        done = scheduler.filter_tasks(plan.scheduled, completed=True)
        pending = scheduler.filter_tasks(plan.scheduled, completed=False)
        assert len(done) == 1
        assert len(pending) == len(plan.scheduled) - 1

    def test_no_criteria_returns_copy(self, scheduler, owner):
        plan = self._plan_with_two_pets(scheduler, owner)
        result = scheduler.filter_tasks(plan.scheduled)
        assert result == plan.scheduled
        assert result is not plan.scheduled  # a copy, not the same list


# --------------------------------------------------------------------------- #
# 6. Edge cases: empty / degenerate inputs
# --------------------------------------------------------------------------- #
class TestEdgeCases:
    def test_owner_with_no_pets_builds_empty_plan(self, scheduler):
        plan = scheduler.build_daily_plan(today_day_name())
        assert isinstance(plan, DailyPlan)
        assert plan.scheduled == []
        assert plan.deferred == []

    def test_pet_with_no_tasks(self, scheduler, owner):
        owner.add_pet(Pet(name="Empty", pet_type="fish"))
        plan = scheduler.build_daily_plan(today_day_name())
        assert plan.scheduled == []
        assert plan.deferred == []

    def test_no_availability_defers_everything(self):
        owner = Owner(name="Busy")  # no availability set at all
        pet = Pet(name="Rex", pet_type="dog")
        pet.add_task(Task("Walk", "walk", priority=5, duration_minutes=30))
        owner.add_pet(pet)

        plan = Scheduler(owner).build_daily_plan(today_day_name())
        assert plan.scheduled == []
        assert len(plan.deferred) == 1

    def test_malformed_time_string_parses_to_none(self):
        assert Scheduler._parse_time("not-a-time") is None
        assert Scheduler._parse_time("25:99") is None

    def test_suggestions_only_when_free_time_left(self, scheduler, owner):
        pet = Pet(name="Rex", pet_type="dog", medical_conditions=["arthritis"])
        pet.add_task(Task("Quick", "misc", priority=5, duration_minutes=5))
        owner.add_pet(pet)

        plan = scheduler.build_daily_plan(today_day_name())
        # Only 5 min used out of 3.5h -> spare time -> suggestions offered.
        assert plan.suggestions != []
