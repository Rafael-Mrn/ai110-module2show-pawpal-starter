"""PawPal+ demo script.

Builds a small owner/pets/tasks setup using the logic layer in
pawpal_system.py and prints today's care schedule to the terminal.
"""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

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

    # 3. Add at least three tasks with different preferred times.
    rex.add_task(Task("Morning walk", "exercise", priority=6,
                      duration_minutes=45, preferred_time_of_day="07:00"))
    rex.add_task(Task("Dinner", "feeding", priority=8,
                      duration_minutes=15, preferred_time_of_day="18:00"))
    mochi.add_task(Task("Kidney meds", "medical", priority=10,
                        duration_minutes=10, preferred_time_of_day="07:30"))
    mochi.add_task(Task("Evening feeding", "feeding", priority=7,
                        duration_minutes=10, preferred_time_of_day="17:30"))

    # 4. Build and print today's schedule.
    scheduler = Scheduler(owner)
    plan = scheduler.build_daily_plan(today)

    print("=" * 44)
    print(f"  Today's Schedule for {owner.name} ({today})")
    print("=" * 44)
    print(plan.rationale)


if __name__ == "__main__":
    main()
