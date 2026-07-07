"""PawPal+ demo script.

Builds a small owner/pets/tasks setup using the logic layer in
pawpal_system.py and prints today's care schedule to the terminal.
"""

from datetime import date, datetime, time

from pawpal_system import Owner, Pet, PlannedTask, Scheduler, Task

# Map Python's weekday index to the names PawPal+ uses for availability.
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def main() -> None:
    today = WEEKDAY_NAMES[date.today().weekday()]

    # 1. Create the owner and the days/times they're free today.
    owner = Owner(name="Rafael")
    owner.update_availability(today, [("07:00", "09:00"), ("17:30", "19:00")])

    # 2. Create at least two pets.
    rex = Pet(name="Rex", pet_type="dog", breed="Beagle", weight=12.5)
    mochi = Pet(name="Mochi", pet_type="cat", breed="Tabby",
                medical_conditions=["kidney disease"], weight=4.2)
    owner.add_pet(rex)
    owner.add_pet(mochi)

    # 3. Add at least three tasks with different preferred times and recurrence.
    rex.add_task(Task("Morning walk", "exercise", priority=6,
                      duration_minutes=45, preferred_time_of_day="07:00",
                      recurrence="daily"))
    rex.add_task(Task("Weekly bath", "grooming", priority=4,
                      duration_minutes=30, preferred_time_of_day="18:00",
                      recurrence="weekly"))
    mochi.add_task(Task("Kidney meds", "medical", priority=10,
                        duration_minutes=10, preferred_time_of_day="07:30",
                        recurrence="daily"))
    mochi.add_task(Task("Evening feeding", "feeding", priority=7,
                        duration_minutes=10, preferred_time_of_day="17:30"))

    # 4. Build and print today's schedule.
    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan(today)

    print("=" * 44)
    print(f"  Today's Schedule for {owner.name} ({today})")
    print("=" * 44)
    print(plan.rationale)

    # 5. Sorting demo — tasks were added out of order (see step 3). sort_by_time
    #    puts them back into clock order regardless of insertion order.
    print("\n" + "=" * 44)
    print("  Tasks in INSERTION order (out of order)")
    print("=" * 44)
    all_tasks = [t for pet in owner.pets for t in pet.tasks]
    for t in all_tasks:
        print(f"  {t.preferred_time_of_day or '--:--'}  {t.name}")

    print("\n" + "=" * 44)
    print("  Tasks SORTED by time (Scheduler.sort_by_time)")
    print("=" * 44)
    for t in scheduler.sort_by_time():
        print(f"  {t.preferred_time_of_day or '--:--'}  {t.name}")

    # 6. Filtering demo. Mark one occurrence complete so the status filter has
    #    something to separate, then filter by pet name and by completion.
    if plan.scheduled:
        plan.scheduled[0].mark_complete()

    print("\n" + "=" * 44)
    print("  Filter by pet name 'Mochi' (Scheduler.filter_tasks)")
    print("=" * 44)
    for p in scheduler.filter_tasks(plan.scheduled, pet_name="Mochi"):
        when = p.due_time.strftime("%H:%M") if p.due_time else "--:--"
        print(f"  {when}  {p.task.name}")

    print("\n" + "=" * 44)
    print("  Filter by status: COMPLETED only")
    print("=" * 44)
    for p in scheduler.filter_tasks(plan.scheduled, completed=True):
        print(f"  {p.task.name} ({p.pet.name})")

    print("\n" + "=" * 44)
    print("  Filter by status: PENDING only")
    print("=" * 44)
    for p in scheduler.filter_tasks(plan.scheduled, completed=False):
        print(f"  {p.task.name} ({p.pet.name})")

    # 7. Recurrence demo. Completing a daily/weekly occurrence automatically
    #    creates the next one (daily -> +1 day, weekly -> +7 days). One-off
    #    tasks return None and simply don't repeat.
    print("\n" + "=" * 44)
    print("  Recurrence: complete a task -> next occurrence")
    print("=" * 44)
    for p in plan.scheduled:
        completed_at = p.due_time.strftime("%a %Y-%m-%d %H:%M") if p.due_time else "--"
        next_occurrence = p.mark_complete()
        if next_occurrence is None:
            print(f"  {p.task.name} ({p.task.recurrence}): one-off, no repeat")
        else:
            next_at = next_occurrence.due_time.strftime("%a %Y-%m-%d %H:%M")
            print(f"  {p.task.name} ({p.task.recurrence}): "
                  f"done {completed_at}  ->  next {next_at}")

    # 8. Conflict detection. The scheduler's own plan never double-books, so to
    #    prove detection works we build two occurrences for different pets at
    #    the SAME time (08:00) and check them.
    print("\n" + "=" * 44)
    print("  Conflict detection (Scheduler.detect_conflicts)")
    print("=" * 44)

    same_time = datetime.combine(date.today(), time(8, 0))
    play = PlannedTask(
        task=Task("Backyard play", "exercise", duration_minutes=20,
                  preferred_time_of_day="08:00"),
        due_time=same_time, pet=rex,
    )
    brush = PlannedTask(
        task=Task("Quick brush", "grooming", duration_minutes=15,
                  preferred_time_of_day="08:00"),
        due_time=same_time, pet=mochi,
    )

    conflicts = scheduler.detect_conflicts([play, brush])
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts.")

    # Sanity check: the real generated plan should be conflict-free.
    print("\n  Checking the generated plan for conflicts...")
    plan_conflicts = scheduler.detect_conflicts(plan.scheduled)
    print(f"  {plan_conflicts[0] if plan_conflicts else 'No conflicts.'}")


if __name__ == "__main__":
    main()
