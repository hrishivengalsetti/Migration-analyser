# SKILL: Git Discipline

## Purpose

Prevent destructive Git operations and ensure clean, reviewable commits.

---

## Before Starting Any Task

```bash
git status
```

Check for:
- Uncommitted changes from a previous task
- Untracked files that shouldn't be there
- Any `wip` commits that need attention

If you see unexpected changes, STOP and report to the Planning Bot. Do not overwrite them.

---

## Before Committing

### 1. Review the diff

```bash
git diff HEAD
```

Check:
- Changes are limited to files the task was supposed to touch
- No debug `print()` statements left in
- No commented-out code blocks
- No accidentally included secrets or API keys
- No changes to unrelated files

### 2. Review diff statistics

```bash
git diff --stat HEAD
```

Sanity check: does the scope of changes look reasonable for this task?

---

## Making a Commit

```bash
git add -A
git diff --cached  # review what's staged
git commit -m "feat(TASK-NNN): <concise description>"
```

### Commit Message Format

```
feat(TASK-001): FastAPI scaffold with SQLite schema and run CRUD endpoints
```

- Start with `feat(TASK-NNN):` for completed work
- Start with `wip(TASK-NNN): blocked — <reason>` for blockers
- Keep the description under 72 characters
- Use present tense ("add", "fix", "implement" not "added", "fixed")

---

## Forbidden Git Commands

Never use these without explicit human approval:

```bash
git reset --hard
git clean -fd
git push --force
git push -f
git rebase -i
git commit --amend  # only on commits from this session, and only if not pushed
```

---

## One Task, One Commit

- Do not batch multiple tasks into one commit
- Do not split one task into many commits (unless explicitly needed for a large task)
- Each task file `TASK-NNN.md` maps to exactly one commit

---

## If Something Goes Wrong

If you accidentally staged something you shouldn't have:
```bash
git reset HEAD <file>  # unstage a specific file
```

If you committed something wrong (and it's NOT pushed):
Discuss with the Planning Bot before amending.

If you committed something wrong (and it IS pushed):
STOP. Do not try to fix it with force push or history rewriting. Report to the human.
