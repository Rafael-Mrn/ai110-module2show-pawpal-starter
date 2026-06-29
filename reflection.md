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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
