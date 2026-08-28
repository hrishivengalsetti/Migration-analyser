# SKILL: Scope Control

## Purpose

Prevent scope expansion, architectural drift, and endless implementation loops. This is the most important discipline for hackathon execution.

---

## The Core Rule

> **Implement exactly what the task says. Nothing more. Nothing less.**

---

## What Scope Expansion Looks Like

You are in scope expansion if you are about to:

- Add a feature not listed in the task's acceptance criteria
- Refactor code in a file not mentioned in the task
- Add a new dependency without task approval
- Change the database schema in a way not required by the task
- Add logging/monitoring/observability beyond what the task requires
- Redesign an interface because you think it's better
- Add error handling beyond what the task specifies
- Add caching because it might be useful later
- Write tests beyond those specified in the task's verification section
- Write documentation beyond what the task requires

If you are doing any of these, STOP and refocus.

---

## What Architectural Drift Looks Like

You are drifting from architecture if you are about to:

- Use Redis instead of SQLite
- Use Celery instead of BackgroundTasks
- Use SQLAlchemy instead of raw `sqlite3`
- Use TreeSitter instead of `ast`
- Use a different LLM provider than Gemini Flash
- Add a graph database
- Add a message queue
- Add authentication
- Change the API contract without Planning Bot approval

If you notice any of these, STOP and re-read `.agent/architecture.md`.

---

## What "Good Enough" Means in a Hackathon

The goal is a working demo, not production-ready code.

**Good enough is**:
- It passes the acceptance tests
- It handles the happy path for the demo
- It doesn't crash with a reasonable input
- The code is readable

**Good enough is NOT**:
- Perfect error handling for every edge case
- Production-grade performance
- Full test coverage of all branches
- Beautiful abstractions
- Extensive documentation

If you find yourself going beyond "good enough," stop and ask: does this help the demo? If no, skip it.

---

## Stopping Criteria

STOP IMMEDIATELY and report to the Planning Bot if:

1. The task is ambiguous and you cannot determine the correct implementation
2. The task conflicts with the architecture
3. You have failed a test twice and cannot determine why
4. The task requires a technology not in the approved stack
5. You realize the task depends on something that doesn't exist yet
6. Implementing the task would require changes to more than 5 files you didn't expect

Do NOT silently work around these situations. Report them.

---

## The Anti-Loop Rule

> One task. One implementation. Two debug attempts. Then stop.

There is no "try a different approach" after 2 failures. There is only: report the blocker and let the Planning Bot decide.

The Planning Bot can redesign the task, relax constraints, or assign a different approach.
You cannot.
