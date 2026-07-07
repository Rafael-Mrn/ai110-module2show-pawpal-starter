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
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
