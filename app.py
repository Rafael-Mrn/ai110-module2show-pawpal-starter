import pandas as pd
import streamlit as st
from datetime import date, datetime, time

# Bring the logic layer into the UI.
from pawpal_system import (
    RECURRENCE_OPTIONS,
    Owner,
    Pet,
    PlannedTask,
    Scheduler,
    Task,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# The UI shows friendly priority labels; the scheduler ranks by number.
PRIORITY_MAP = {"low": 1, "medium": 5, "high": 10}
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Streamlit reruns this whole script on every click. Keeping a single Owner in
# session_state is what makes the pets/tasks we create actually persist.
if "owner" not in st.session_state:
    # Start blank; the owner fills in their own name below.
    st.session_state.owner = Owner(name="")
owner: Owner = st.session_state.owner

# One scheduler over the session's owner; used for sorting, filtering, and
# conflict detection throughout the UI.
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")
owner.name = st.text_input(
    "Owner name", value=owner.name, placeholder="e.g. Jordan"
)

st.divider()

# --- Adding a Pet --------------------------------------------------------------
st.subheader("Add a Pet")

col1, col2 = st.columns(2)
with col1:
    new_pet_name = st.text_input("Pet name", value="", placeholder="e.g. Mochi")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
with col2:
    new_pet_breed = st.text_input("Breed", value="")
    new_pet_weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0, step=0.1)

if st.button("Add pet"):
    if new_pet_name.strip():
        # Real Pet object, stored on the Owner that lives in session_state.
        owner.add_pet(
            Pet(
                name=new_pet_name.strip(),
                pet_type=new_pet_species,
                breed=new_pet_breed.strip(),
                weight=float(new_pet_weight),
            )
        )
        st.success(f"Added {new_pet_name.strip()} to {owner.name}'s pets.")
    else:
        st.error("Please enter a pet name.")

if owner.pets:
    st.write("Current pets:")
    st.table(
        [
            {
                "Name": p.name,
                "Species": p.pet_type,
                "Breed": p.breed or "—",
                "Tasks": len(p.tasks),
            }
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Scheduling a Task ---------------------------------------------------------
st.subheader("Add a Task")

if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    # Select by index, not by Pet object: Streamlit doesn't reliably hand back
    # the same object identity for object-valued options, so mutating a returned
    # Pet can silently update a throwaway copy. Looking the pet up by index in
    # owner.pets guarantees we attach tasks to the real, persisted object.
    pet_index = st.selectbox(
        "Which pet?",
        options=range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    target_pet = owner.pets[pet_index]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input(
            "Task title", value="", placeholder="e.g. Morning walk"
        )
        task_category = st.selectbox(
            "Category", ["walk", "feeding", "medication", "grooming", "enrichment"]
        )
    with col2:
        task_duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
        task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        preferred = st.time_input("Preferred time", value=time(8, 0))
        task_recurrence = st.selectbox("Repeats", list(RECURRENCE_OPTIONS))

    if st.button("Add task"):
        if task_title.strip():
            target_pet.add_task(
                Task(
                    name=task_title.strip(),
                    category=task_category,
                    priority=PRIORITY_MAP[task_priority],
                    duration_minutes=int(task_duration),
                    preferred_time_of_day=preferred.strftime("%H:%M"),
                    recurrence=task_recurrence,
                )
            )
            st.success(f"Added '{task_title.strip()}' to {target_pet.name}.")
        else:
            st.error("Please enter a task title.")

    # --- Current tasks: sorted by time, filterable, with a conflict pre-check -
    all_tasks = [t for p in owner.pets for t in p.tasks]
    task_to_pet = {id(t): p for p in owner.pets for t in p.tasks}

    if all_tasks:
        st.write("**Current tasks**")

        # Filter by pet (reuses Scheduler.filter_tasks).
        pet_filter = st.selectbox(
            "Show tasks for",
            ["All pets"] + [p.name for p in owner.pets],
            key="task_pet_filter",
        )
        shown = all_tasks
        if pet_filter != "All pets":
            shown = scheduler.filter_tasks(all_tasks, pet_name=pet_filter)

        # Sort chronologically by preferred time (Scheduler.sort_by_time).
        shown = scheduler.sort_by_time(shown)

        st.table(
            [
                {
                    "Pet": task_to_pet[id(t)].name,
                    "Task": t.name,
                    "Category": t.category,
                    "Priority": t.priority,
                    "Duration": f"{t.duration_minutes} min",
                    "Preferred": t.preferred_time_of_day or "—",
                    "Repeats": t.recurrence,
                }
                for t in shown
            ]
        )

        # Conflict pre-check: warn if two tasks *want* overlapping times, before
        # the scheduler quietly spaces them out. Build occurrences at each task's
        # preferred time and let Scheduler.detect_conflicts compare them.
        today = date.today()
        wants = [
            PlannedTask(
                task=t,
                due_time=datetime.combine(
                    today, datetime.strptime(t.preferred_time_of_day, "%H:%M").time()
                ),
                pet=task_to_pet[id(t)],
            )
            for t in all_tasks
            if t.preferred_time_of_day
        ]
        conflicts = scheduler.detect_conflicts(wants)
        if conflicts:
            st.warning(
                "⚠️ Some tasks want overlapping times. The scheduler will space "
                "them out automatically, but you may prefer to adjust their times:"
            )
            for c in conflicts:
                st.markdown(f"- {c.replace('WARNING: ', '')}")
        else:
            st.success("✅ No overlapping preferred times.")

st.divider()

# --- Build Schedule ------------------------------------------------------------
st.subheader("Build Schedule")

sched_col1, sched_col2, sched_col3 = st.columns(3)
with sched_col1:
    plan_day = st.selectbox(
        "Day", WEEKDAY_NAMES, index=date.today().weekday()
    )
with sched_col2:
    free_from = st.time_input("Free from", value=time(7, 0))
with sched_col3:
    free_until = st.time_input("Free until", value=time(19, 0))

if st.button("Generate schedule"):
    if not owner.pets:
        st.error("Add a pet with some tasks first.")
    else:
        # Record when the owner is free, then let the scheduler build the plan.
        # Store it in session_state so the filters/checkboxes below stay live
        # across Streamlit reruns without rebuilding the plan each time.
        owner.update_availability(
            plan_day, [(free_from.strftime("%H:%M"), free_until.strftime("%H:%M"))]
        )
        st.session_state.plan = scheduler.build_daily_plan(plan_day)

plan = st.session_state.get("plan")
if plan:
    st.markdown(f"#### 📅 Schedule for {plan.day}")

    if not plan.scheduled:
        # Nothing fit — say *why* and let the deferred list below show the
        # tasks, so a generated schedule is never just an empty confirmation.
        st.warning(
            "None of your tasks could be placed in the free window you set. "
            "Make sure each task's preferred time falls inside your "
            "**Free from / Free until** range (or widen that range), then "
            "generate again."
        )
    else:
        # Conflict banner only makes sense once something is actually scheduled.
        conflicts = scheduler.detect_conflicts(plan.scheduled)
        if conflicts:
            for c in conflicts:
                st.warning(f"⚠️ {c.replace('WARNING: ', '')}")
        else:
            st.success(
                "✅ No scheduling conflicts — every task has its own time slot."
            )

        # Filters: by pet and by completion status (Scheduler.filter_tasks).
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            sched_pet = st.selectbox(
                "Filter by pet",
                ["All pets"] + [p.name for p in owner.pets],
                key="sched_pet_filter",
            )
        with fcol2:
            status = st.radio(
                "Status", ["All", "Pending", "Done"], horizontal=True,
                key="sched_status_filter",
            )

        shown = plan.scheduled
        if sched_pet != "All pets":
            shown = scheduler.filter_tasks(shown, pet_name=sched_pet)
        if status == "Pending":
            shown = scheduler.filter_tasks(shown, completed=False)
        elif status == "Done":
            shown = scheduler.filter_tasks(shown, completed=True)

        # Chronological order by the time actually assigned.
        shown = sorted(shown, key=lambda p: p.due_time or datetime.max)

        if not shown:
            st.info("No tasks match this filter.")
        else:
            # Interactive schedule table: the owner checks tasks off right in
            # the table (the Done column is editable; everything else is not).
            table = pd.DataFrame(
                [
                    {
                        "Done": p.completed,
                        "Time": p.due_time.strftime("%H:%M") if p.due_time else "—",
                        "Pet": p.pet.name if p.pet else "—",
                        "Task": p.task.name,
                        "Category": p.task.category,
                        "Priority": p.task.priority,
                        "Duration (min)": p.task.duration_minutes,
                        "Repeats": p.task.recurrence,
                    }
                    for p in shown
                ]
            )
            edited = st.data_editor(
                table,
                hide_index=True,
                width="stretch",
                disabled=[
                    "Time", "Pet", "Task", "Category",
                    "Priority", "Duration (min)", "Repeats",
                ],
                column_config={
                    "Done": st.column_config.CheckboxColumn(
                        "Done", help="Tick when this task is finished."
                    )
                },
                # Vary the key with the filter so edits always map to the rows
                # actually on screen.
                key=f"schedule_editor_{sched_pet}_{status}",
            )

            # Push the checkbox edits back onto the plan's occurrences.
            for p, is_done in zip(shown, edited["Done"]):
                p.completed = bool(is_done)

    # Completing a recurring task auto-creates its next occurrence. Shown for
    # every completed recurring task, regardless of the filter above.
    for p in plan.scheduled:
        if p.completed:
            nxt = p.next_occurrence()
            if nxt is not None:
                st.info(
                    f"↻ '{p.task.name}' repeats {p.task.recurrence} — "
                    f"next on {nxt.due_time:%a %Y-%m-%d %H:%M}."
                )

    if plan.deferred:
        st.warning(
            "Didn't fit in the available time: "
            + ", ".join(p.task.name for p in plan.deferred)
        )

    if plan.suggestions:
        st.markdown("**Spare time — suggestions:**")
        for s in plan.suggestions:
            st.markdown(f"- {s}")

    with st.expander("Why this plan?"):
        st.code(plan.rationale)
