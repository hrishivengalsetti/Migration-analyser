# Migration-analyser

## Problem Statement

Software migrations (language upgrades, library replacements, framework changes, API refactors) introduce behavioral regressions that are invisible to the compiler and to existing tests. The failure mode is:

> "It compiles. Tests pass. We shipped. Something subtly broke."

The system must answer:

> **"Given a legacy codebase and a migrated codebase, what changed, what could break, and do we have deterministic evidence that the critical paths still behave equivalently?"**

The output is not an AI opinion. It is an evidence report backed by actual execution results, structured diffs, and reachability analysis.

## Core Features (MVP)

*   **Language Support**: Python only.
*   **Analysis**: File-level diff, function-level diff via AST parsing.
*   **Dependency Graph**: Intra-project import graph.
*   **Blast Radius**: Transitive call/import reachability from changed symbols.
*   **Test Selection**: Map existing `pytest` tests to changed symbols via static analysis.
*   **Execution**: Run test suite (old and new) inside a Docker sandbox, capturing pass/fail + stdout/stderr.
*   **Behavioral Comparison**: Deterministic comparison of test results, captured outputs, and exit codes.
*   **Report**: Structured JSON evidence and a rendered React single-page application.
*   **AI Interpretation**: Uses Google Gemini Flash to interpret migration intent, explain failures, and classify risk.

## Tech Stack

*   **Frontend**: React + Vite + JS + Tailwind CSS + shadcn
*   **Backend**: Python + FastAPI
*   **Graph Processing**: NetworkX
*   **AI**: Google Gemini Flash (`google-generativeai`)
*   **Execution Environment**: Docker
*   **Database**: SQLite

## Architecture

The system operates by receiving two `.zip` files (original and migrated). A FastAPI backend processes these files asynchronously via a pipeline that includes AST analysis, dependency graph building, and Docker-sandboxed execution of tests. The results are deterministic and presented on a React frontend, augmented with AI interpretation of the changes and failures.

## Quick Start (Development)

Requires Docker, Node.js (for frontend), and Python 3.10+ (for backend). Set up your Gemini API key in `.env`.

*Note: The project is currently under active development. See `architecture-revised.md` for the full implementation plan and milestones.*
