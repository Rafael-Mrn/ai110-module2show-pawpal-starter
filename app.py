import streamlit as st
from datetime import date, time

# Bring the logic layer into the UI.
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# The UI shows friendly priority labels; the scheduler ranks by number.
PRIORITY_MAP = {"low": 1, "medium": 5, "high": 10}
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Streamlit reruns this whole script on every click. Keeping a single Owner in
# session_state is what makes the pets/tasks we create actually persist.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")
owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# --- Adding a Pet --------------------------------------------------------------
st.subheader("Add a Pet")

col1, col2 = st.columns(2)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
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
    # Return the actual Pet object so we can call pet.add_task on it directly.
    target_pet = st.selectbox(
        "Which pet?", options=owner.pets, format_func=lambda p: p.name
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
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

    if st.button("Add task"):
        target_pet.add_task(
            Task(
                name=task_title.strip() or "Untitled task",
                category=task_category,
                priority=PRIORITY_MAP[task_priority],
                duration_minutes=int(task_duration),
                preferred_time_of_day=preferred.strftime("%H:%M"),
            )
        )
        st.success(f"Added '{task_title.strip()}' to {target_pet.name}.")

    # Show every pet's current tasks.
    rows = [
        {
            "Pet": p.name,
            "Task": t.name,
            "Category": t.category,
            "Duration": f"{t.duration_minutes} min",
            "Preferred": t.preferred_time_of_day or "—",
        }
        for p in owner.pets
        for t in p.tasks
    ]
    if rows:
        st.write("Current tasks:")
        st.table(rows)

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
        owner.update_availability(
            plan_day, [(free_from.strftime("%H:%M"), free_until.strftime("%H:%M"))]
        )
        plan = Scheduler(owner).build_daily_plan(plan_day)

        st.markdown(f"#### Today's Schedule ({plan.day})")
        if plan.scheduled:
            st.table(
                [
                    {
                        "Time": p.due_time.strftime("%H:%M") if p.due_time else "—",
                        "Task": p.task.name,
                        "Priority": p.task.priority,
                        "Duration": f"{p.task.duration_minutes} min",
                    }
                    for p in plan.scheduled
                ]
            )
        else:
            st.info("Nothing could be scheduled in the available time.")

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
