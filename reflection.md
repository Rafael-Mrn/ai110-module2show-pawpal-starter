# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.  
  My initial UML design will include classes to support three main actions. The first action the user should be able to perform is track pet care tasks by seeing a checklist of items to complete everyday for their pet. The second action should be to upload information on their pet to personalize their experience. Lastly, they should also be able to produce and choose a plan that was automated. 
- What classes did you include, and what responsibilities did you assign to each?  
  1. Owner - store information of the owner. Name, availability, contacts/co-owners attributes. Ability to add/remove pets. 
  2. Pet - track name, pet type, breed, medical conditions, and weight attributes. Provide health/care suggestions based on info. 
  3. Task - responsibilities include tracking pet care tasks walks, feeding, medications, grooming, enrichment as attributes. Create a list of daily tasks, update list based on completion, send alerts.
  4. Scheduler - produce a plan based on pet owner's availability. Set time of day for walks + suggest. Weekly availability attitribute (what days and specific times the pet owner is free). Aside from scheduling required tasks, the plan can introduce pet care advice and activities.
  

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
  Yes, I had to split Task into a recurring template (Task) and a per-day instance (PlannedTask). Completion and timing state were living on the same object stored in Pet.tasks. If the scheduler handed those same objects to the daily plan, calling mark_complete() would mutate the master list — so "feed the dog" would stay completed forever and the next day's plan would be wrong.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?  
  My scheduler works within three constraints: the owner's free-time windows, each task's priority, and each task's preferred time of day. Free time is a hard limit since a task simply can't be placed if there's no room, so it acts as the outer boundary. Within that boundary, priority decides ordering and preferred time is honored when it happens to fit.
- How did you decide which constraints mattered most?
  I decided that available time mattered most because it's a physical limit. The owner can't be in two places at once so nothing can be scheduled outside their windows. Priority came next since medication and feeding must win over optional enrichment when time is short, and preferred time ranked last because it's a nice-to-have that shouldn't block a higher-priority task from being placed.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  It uses a greedy, first-fit placement: it sorts tasks by priority and drops each one into the earliest window it fits, never backtracking to reshuffle earlier choices. This means a high-priority task can claim an early slot that a preferred-time task wanted, and that preferred task then gets bumped to first-fit elsewhere or deferred.
- Why is that tradeoff reasonable for this scenario?
  For a daily pet-care list of a handful of tasks, a greedy pass is fast, predictable, and easy to explain to the owner, and it guarantees the most important tasks are placed first. A globally optimal schedule would add real complexity for little benefit at this scale, so guaranteeing the critical tasks land beats squeezing out a perfect arrangement.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?  
  AI supported me throughout the entire build for this project. During the design and brainstorming phase, I used structured prompts so that the AI could propose a class structure that meant the minimum requirements. Once the minimum requirements were met, I went back and forth with Claude Code to implement logical features that should be found in a pet tracker. Debugging and refactoring was done in the later part of the projec when polishing the UI. I found that Claude Code didn't implement all the features it build in the backend so this was were I gave much longer and more detailed custom prompts. 
- What kinds of prompts or questions were most helpful?  
  Questions that asked for context and an explanation of the code were the most helpful as they helped me stay on top of the build. I found that building with Claude Code can go at a fast pace so it is important to take time to understand the current code and pay attention to the suggestions/explanations that Claude was giving me.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.  
  A moment where I did not accept an AI suggestion as-is was when building out the Schedular. Claude assumed that the all tasks were given 30-minute blocks and should be scheduled as so however, I ensured that the feature would allow the user to define the length of each time. The algorithmic layer made use of these times and streamlined the experience for the user (conflict deteciton and filtering). 
- How did you evaluate or verify what the AI suggested?  
While tests and main.py helped verify the logic of the features, much of my criticsm towards AI suggestions was based on the Streamlit UI. Claude not only left out core features in the UI even after requesting it to do so, but also encountered a bug. I found that testing the user interface was the most helpful in ensuring that the app provided a smooth experience and served its purpose.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?  
  Claude wrote 29 tests in `test_pawpal.py` covering the five core scheduler behaviors which were chronological sorting (including stable ties and untimed-last), recurrence (daily +1 day, weekly +7 days, one-offs returning `None`), conflict detection, priority-based placement with deferral, and filtering by pet and completion status.
- Why were these tests important?  
  These are the behaviors the whole app depends on, so verifying them directly gave me confidence that the logic layer is correct before wiring it into the UI. I deliberately included edge cases like empty inputs, exact-time ties, and half-open boundary overlaps to ensure the Schedular worked even through user error.

**b. Confidence**

- How confident are you that your scheduler works correctly?  
  I am quite confident since all 29 tests pass and the core scheduling logic is directly verified. While the tests verify the backend logic, a manual check of the Streamlit UI and a thorough check by Claude when debugging makes me condfident in the final state of the system.
- What edge cases would you test next if you had more time?  
  I'd freeze the clock to make the `datetime.now()` fallback fully deterministic, and add end-to-end UI tests for `app.py` (e.g. adding a pet then generating a schedule) plus overlapping owner availability windows and tasks whose preferred time falls outside the free window.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?  
  I am most satisfied with the UI of the project since it was the final aspect of the system that most users would find as most important. Having many core features built out first, then being able to implement them in a UI was the most satisfying part as it ensured that the behavior was well thought out and resilient.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?  
  If I had another iteration, I would improve the structure of the app by implementing a calendar feature to better visualize the tasks, especially those that may occur weekly or monthly. However, I figured that using a table for daily tasks is the most useful since a pet owner is mostly concerned in making sure they track the tasks of that day. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?  
I learned that context and scaffolding are some of the best ways to use Claude code. My prior experience was using AI through a website rather than integrating it directly into my workflow. While context helps the AI understand the code and avoid the extra time needed to explain the codebase or issue at hand, scaffolding avoided what would have otherwise been many rough patches. Being in charge of design made it so Claude was simply responsible for execution and making any possible suggestions. As a result, I figure that this is the best way to use AI for coding.
