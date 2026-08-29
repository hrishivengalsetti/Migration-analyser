# Implementation Plan Review Request

## Your Role

You are a **senior software architect and hackathon strategist**.

You have deep experience in:
- Python backend systems (FastAPI, async, background workers)
- Static code analysis (AST, call graphs, dependency graphs)
- Docker sandboxing and security
- React frontend architecture
- AI/LLM integration patterns
- Hackathon execution under aggressive timelines

---

## Context

We are building an **AI-Assisted Migration Verifier** for a hackathon.

**The core product answers:**
> "After this migration, what could have been affected, and do we have deterministic evidence that the migrated version still behaves correctly?"

**Key constraints:**
- $0 budget — all tools must be free/open-source
- Small team, aggressive hackathon timeline
- Goal is a working, impressive demo — not a production system
- Code generation is handled by a separate agent (LatentCode) that receives small, explicit task files
- Reliability > architectural elegance

**Finalized decisions already made:**
- Python only (MVP)
- FastAPI + SQLite (no ORM)
- Python `ast` stdlib for parsing (no Tree-sitter)
- NetworkX for graph (JSON-serialized, not a graph DB)
- Docker sandbox (pre-built image, read-only bind mount)
- Google Gemini Flash for AI (1 call per run)
- React + Vite + JavaScript (no TypeScript) + Tailwind + shadcn/ui
- React Flow for graph visualization
- Zip file upload for codebase submission
- Purpose-built demo project with baked-in regression

---

## The Implementation Plan

The full implementation plan follows below. Read it carefully in its entirety before responding.

---

[PASTE THE FULL IMPLEMENTATION PLAN HERE]

---

## Your Task

Critically review the implementation plan above. Be aggressive and honest.

For each issue you find, state:
1. **What the problem is** — be specific, reference the exact section
2. **Why it's a problem** — technical risk, timeline risk, demo risk, or correctness issue
3. **How to fix it** — concrete recommendation

Structure your response under these categories:

### 1. Correctness Issues
Technical mistakes, wrong assumptions, or things that simply won't work as described.
> Example: "The blast radius algorithm in Section 8 uses `descendants()` but should use `ancestors()` — descendants are symbols the changed code calls, not callers of the changed code."

### 2. Completeness Gaps
Important things that are missing from the plan that will cause problems during implementation.
> Example: "There is no plan for how the unzipped temp directories are cleaned up after a run. This will fill disk."

### 3. Scope / Timeline Risk
Things that are more complex than they appear, likely to blow up the timeline, or that should be cut/simplified.
> Example: "The test selector (TASK-007) is described as mapping test functions to symbols via static analysis. This is significantly harder than it sounds — static resolution of which symbols a test exercises requires full import resolution, which the plan does not fully account for."

### 4. Inconsistencies
Places where the plan contradicts itself or where a decision made in one section is not reflected in another.
> Example: "Section 2 says the demo uses 'two local directories' but Section 14 says it uses zip file upload. These need to be consistent."

### 5. Minor Issues / Improvements
Small things worth fixing but not blockers.
> Example: "The `FileDiff` model in Section 5 includes a `hunks` field but hunks are never mentioned in the pipeline steps. Either use it or remove it."

---

## Constraints on Your Response

- Be specific — reference exact section numbers, field names, and function names
- Do NOT praise the plan — only flag issues
- Do NOT suggest adding features — only flag problems with what's already planned
- Do NOT suggest architectural changes that contradict the finalized decisions listed above
- Keep each issue concise — bullet points preferred over paragraphs
- If something is genuinely fine, do not mention it
- Prioritize by severity: correctness > completeness > scope risk > inconsistency > minor
