# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
============================================
  Today's Schedule for Rafael (Tue)
============================================
Plan for Tue:
Scheduled 4 task(s), highest priority first:
  - 07:30  Kidney meds (priority 10, 10min)
  - 18:00  Dinner (priority 8, 15min)
  - 07:40  Evening feeding (priority 7, 10min)
  - 07:50  Morning walk (priority 6, 45min)
Spare time available — optional suggestions:
  - Look up breed-specific needs for a Beagle.
  - Add an enrichment activity to keep Rex stimulated.
  - Monitor Mochi's kidney disease; check with the vet about managing it.
  - Look up breed-specific needs for a Tabby.
  - Add an enrichment activity to keep Mochi stimulated.
```


## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest

# Run a specific file, verbose:
python -m pytest test_pawpal.py -v
```

### What the tests cover

`test_pawpal.py` holds **29 tests** (grouped by behavior) that exercise the scheduling logic in `pawpal_system.py`:

- **Sorting** — tasks come back in chronological order, untimed tasks sort last, and equal times keep insertion order (stable sort).
- **Recurrence** — completing a `daily` task creates the next occurrence at +1 day, `weekly` at +7 days, and one-off tasks return `None`; also covers the `datetime.now()` fallback when a task has no `due_time`.
- **Conflict detection** — overlapping times are flagged, two pets booked at the exact same minute clash, and back-to-back tasks (end == start) correctly do **not**.
- **Priority scheduling** — highest priority is placed first, over-capacity tasks are deferred, preferred times are honored when they fit, and the generated plan is itself conflict-free.
- **Filtering** — by pet name and by completion status.
- **Edge cases** — owner with no pets, pet with no tasks, no availability at all, and malformed time strings — all handled without crashing.

### Confidence Level: ⭐⭐⭐⭐☆ (4/5)

All 29 tests pass. The core scheduling behaviors — sorting, recurrence, conflict detection, priority placement, and deferral — are directly verified, including the tricky boundary cases (same-minute ties, half-open overlaps, empty inputs). Held back from 5/5 because the tests anchor on the real system clock rather than a frozen time, and the Streamlit UI layer (`main.py` / `app.py`) is exercised only through the logic it calls, not end-to-end.

Sample test output:

```
(.venv) PS C:\Users\Rafael\Documents\Codepath-AI110\ai110-module2show-pawpal-starter> python -m pytest test_pawpal.py -v
================================================================================================== test session starts ===================================================================================================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Rafael\Documents\Codepath-AI110\ai110-module2show-pawpal-starter\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Rafael\Documents\Codepath-AI110\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 29 items                                                                                                                                                                                                        

test_pawpal.py::TestSorting::test_tasks_returned_in_chronological_order PASSED                                                                                                                                      [  3%]
test_pawpal.py::TestSorting::test_untimed_tasks_sort_last PASSED                                                                                                                                                    [  6%]
test_pawpal.py::TestSorting::test_same_time_sort_is_stable PASSED                                                                                                                                                   [ 10%]
test_pawpal.py::TestSorting::test_sort_empty_returns_empty PASSED                                                                                                                                                   [ 13%]
test_pawpal.py::TestRecurrence::test_daily_completion_creates_task_for_next_day PASSED                                                                                                                              [ 17%]
test_pawpal.py::TestRecurrence::test_weekly_completion_advances_seven_days PASSED                                                                                                                                   [ 20%]
test_pawpal.py::TestRecurrence::test_one_off_task_does_not_repeat PASSED                                                                                                                                            [ 24%]
test_pawpal.py::TestRecurrence::test_next_occurrence_preserves_pet PASSED                                                                                                                                           [ 27%]
test_pawpal.py::TestRecurrence::test_recurring_task_with_no_due_time_bases_next_on_now PASSED                                                                                                                       [ 31%]
test_pawpal.py::TestRecurrence::test_one_off_with_no_due_time_still_returns_none PASSED                                                                                                                             [ 34%]
test_pawpal.py::TestConflictDetection::test_two_tasks_at_exact_same_time_conflict PASSED                                                                                                                            [ 37%]
test_pawpal.py::TestConflictDetection::test_overlapping_ranges_conflict PASSED                                                                                                                                      [ 41%]
test_pawpal.py::TestConflictDetection::test_touching_end_to_start_is_not_a_conflict PASSED                                                                                                                          [ 44%]
test_pawpal.py::TestConflictDetection::test_non_overlapping_tasks_no_conflict PASSED                                                                                                                                [ 48%]
test_pawpal.py::TestConflictDetection::test_untimed_occurrences_skipped PASSED                                                                                                                                      [ 51%]
test_pawpal.py::TestConflictDetection::test_empty_list_never_raises PASSED                                                                                                                                          [ 55%]
test_pawpal.py::TestDailyPlan::test_higher_priority_scheduled_before_lower PASSED                                                                                                                                   [ 58%]
test_pawpal.py::TestDailyPlan::test_generated_plan_has_no_internal_conflicts PASSED                                                                                                                                 [ 62%]
test_pawpal.py::TestDailyPlan::test_tasks_over_capacity_are_deferred PASSED                                                                                                                                         [ 65%]
test_pawpal.py::TestDailyPlan::test_preferred_time_is_honored_when_it_fits PASSED                                                                                                                                   [ 68%]
test_pawpal.py::TestDailyPlan::test_frequency_per_day_creates_multiple_occurrences PASSED                                                                                                                           [ 72%]
test_pawpal.py::TestFiltering::test_filter_by_pet_name PASSED                                                                                                                                                       [ 75%]
test_pawpal.py::TestFiltering::test_filter_by_completion_status PASSED                                                                                                                                              [ 79%]
test_pawpal.py::TestFiltering::test_no_criteria_returns_copy PASSED                                                                                                                                                 [ 82%]
test_pawpal.py::TestEdgeCases::test_owner_with_no_pets_builds_empty_plan PASSED                                                                                                                                     [ 86%]
test_pawpal.py::TestEdgeCases::test_pet_with_no_tasks PASSED                                                                                                                                                        [ 89%]
test_pawpal.py::TestEdgeCases::test_no_availability_defers_everything PASSED                                                                                                                                        [ 93%]
test_pawpal.py::TestEdgeCases::test_malformed_time_string_parses_to_none PASSED                                                                                                                                     [ 96%]
test_pawpal.py::TestEdgeCases::test_suggestions_only_when_free_time_left PASSED                                                                                                                                     [100%]

=================================================================================================== 29 passed in 0.09s ===================================================================================================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time` | Orders tasks by preferred time of day (earliest first); untimed tasks sort last. Sorts the zero-padded `"HH:MM"` strings directly via a lambda key. |
| Filtering | `Scheduler.filter_tasks` | Returns the subset of tasks matching a pet name and/or completion status. Completion lives on `PlannedTask`, so the status filter only matches per-day occurrences. |
| Conflict handling | `Scheduler.detect_conflicts` | Lightweight pairwise check across all pets; flags occurrences whose `[start, start+duration)` intervals overlap. Returns warning strings (empty list if none) and never crashes. |
| Recurring tasks | `PlannedTask.mark_complete` / `next_occurrence` | Completing a recurring task auto-creates its next occurrence using `timedelta` (daily → +1 day, weekly → +7 days); one-off tasks return `None`. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
