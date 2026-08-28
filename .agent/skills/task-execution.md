# SKILL: Task Execution

## Purpose

This skill defines the exact workflow LatentCode must follow for every assigned task. Deviation from this workflow is not permitted without explicit Planning Bot approval.

---

## Mandatory Execution Sequence

Execute steps IN ORDER. Do not skip steps.

### Step 1: Read project context

Read the following files IN ORDER before doing anything else:

1. `.agent/constitution.md` — non-negotiable rules
2. `.agent/architecture.md` — technical architecture
3. `.agent/current-state.md` — what's done, what's next

Do NOT read the entire repository. Read only these three files at this step.

### Step 2: Read the assigned task

Read the assigned task file: `.agent/tasks/TASK-NNN.md`

Understand:
- Goal
- Inputs
- Acceptance criteria
- Non-goals
- Verification command

If anything is unclear, STOP and report the ambiguity. Do not guess.

### Step 3: Bounded repository exploration

Explore at most **5 relevant files** to understand context.

Do NOT:
- Read every file in the repository
- Explore unrelated modules
- Trace the entire codebase

Do:
- Read files directly referenced by the task
- Read files you will need to modify
- Read related test files

### Step 4: Write an implementation plan (inline)

In the task file, fill in the "Implementation Plan" section with:
- What files you will create or modify
- What logic you will implement
- What you will NOT do (scope check)

This is for your own clarity and for reviewers. Keep it brief.

### Step 5: Implement

Write the code. Follow the architecture in `.agent/architecture.md`.

Rules:
- No new dependencies without explicit task approval
- No new files outside the task scope
- No refactoring unrelated code
- Follow existing code patterns

### Step 6: Run acceptance tests

Run the exact `pytest` command specified in the task's "Verification" section.

If tests pass → proceed to Step 7.
If tests fail → proceed to bounded debugging.

### Step 7: Bounded debugging

You have **maximum 2 debug attempts**.

Each attempt:
1. Read the error output carefully
2. Identify the most likely root cause
3. Make the minimal fix
4. Re-run the test

After 2 attempts, if still failing:
- STOP
- Fill in the "Blocker" section of the task file with the exact error and what you tried
- Commit your partial work with message: `wip(TASK-NNN): blocked — <brief reason>`
- Update `.agent/current-state.md`
- Report to the Planning Bot

Do NOT:
- Continue debugging past 2 attempts
- Redesign the approach without Planning Bot approval
- Expand scope to work around the failure

### Step 8: Review your diff

Run: `git diff HEAD`

Check:
- Do the changes match the task scope?
- Are there any unintended changes?
- Any debug print statements left in?
- Any commented-out code?

If you see unintended changes, revert them.

### Step 9: Commit

Commit with:
```
git add -A
git commit -m "feat(TASK-NNN): <concise description of what was implemented>"
```

Do NOT:
- Add unrelated files
- Use `git add .` blindly without reviewing what's staged
- Force push
- Amend commits from other tasks

### Step 10: Update current state

Edit `.agent/current-state.md`:
- Mark this task as complete in the "What Is Complete" section
- Update "What Is In Progress" and "Next Task to Assign" sections

### Step 11: STOP

Do not continue to the next task unless explicitly instructed.
Report completion to the Planning Bot.

---

## Failure Modes to Avoid

| Failure | What to do instead |
|---|---|
| Tests fail after 2 attempts | STOP, report blocker |
| Task requires architectural change | STOP, report to Planning Bot |
| Task scope is unclear | STOP, ask for clarification |
| Dependency not in requirements.txt | Add it, but only if the task explicitly requires it |
| You want to refactor something unrelated | Don't. Stay in scope. |
| You want to add a feature not in the task | Don't. That's scope expansion. |
