# Project Constitution

## What This Project Is

**Migration Verifier** — an AI-assisted tool that compares an original and a migrated Python codebase, computes blast radius, selects and runs relevant tests in a sandbox, compares behavior deterministically, and produces an evidence-backed report.

---

## Non-Negotiable Rules

### For All Agents

1. **LatentCode is the only agent authorized to generate and modify application source code.**
   - Antigravity (Planning Bot) researches, architects, reviews, and writes tasks. It does NOT write application source files.
   - LatentCode (Execution Bot) reads tasks and implements them.

2. **This is a hackathon project. Reliability > elegance.**
   - Simple, working code is always preferred over sophisticated, broken code.
   - If in doubt, do the dumber thing that works.

3. **Deterministic tools do deterministic work. AI does reasoning.**
   - Never use an LLM to do what `ast`, `networkx`, `difflib`, or `pytest` can do deterministically.
   - LLM is used once per analysis run, after evidence is collected, to interpret and narrate.

4. **Do not introduce infrastructure not in the architecture.**
   - No Redis, Celery, Kafka, Supabase, Postgres, or graph databases unless explicitly approved by a Planning Bot decision.
   - SQLite is the database. NetworkX is the graph engine.

5. **Do not expand scope.**
   - If a task would require changes outside its stated scope, STOP and report to the Planning Bot.
   - No spontaneous refactoring of unrelated code.

---

### For LatentCode (Execution Bot)

6. **Bounded repository exploration.**
   - Read at most 5 relevant files before implementing.
   - Do not map the entire codebase before starting.

7. **Bounded debugging.**
   - Maximum 2 debug attempts per failing test.
   - If still failing after 2 attempts, STOP and report the blocker in the task file.

8. **No architectural redesign.**
   - Follow the architecture in `.agent/architecture.md`.
   - If the task conflicts with the architecture, STOP and report. Do not silently redesign.

9. **Git discipline.**
   - Before starting: `git status` to check for existing uncommitted work.
   - Before committing: `git diff` to review changes.
   - Commit format: `feat(TASK-NNN): <concise description>`
   - One logical task → one logical commit.
   - Never: `git reset --hard`, `git clean -fd`, force push, or history rewriting.

10. **One task at a time.**
    - Implement only what the assigned task specifies.
    - Mark the task complete in `.agent/current-state.md` after committing.

---

## Hard Constraints

- **Language**: Python only (backend analysis). No multi-language support in MVP.
- **Database**: SQLite only. No hosted database.
- **Graph**: NetworkX only. No dedicated graph database.
- **Code generation**: LatentCode only.
- **Docker**: Required for sandboxed test execution. Non-negotiable.
- **Budget**: $0. All dependencies must be free/open-source.
- **AI calls**: Maximum 1 LLM call per analysis run (the interpreter step). Not more.

---

## What "Done" Means for a Task

A task is done when:
1. All acceptance criteria in the task file pass.
2. The specified `pytest` command passes.
3. `git diff` has been reviewed and makes sense.
4. The commit has been made.
5. `.agent/current-state.md` has been updated.
