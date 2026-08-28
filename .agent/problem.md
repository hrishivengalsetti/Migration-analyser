# Problem Statement

## The Problem

Software migrations introduce behavioral regressions that are invisible to compilers and to existing test suites. The failure mode is:

> "It compiled. Tests passed. We shipped. Something subtly broke."

Developers lack tooling that answers the question:

> **"After this migration, what could have been affected, and do we have deterministic evidence that the migrated version still behaves correctly?"**

## Why This Is Hard

1. **Existing tests may not cover the changed code paths.**
   A migration can change behavior in code that is never exercised by the current test suite. Tests pass not because behavior is preserved, but because the changed code is never reached.

2. **Code diffs don't reveal impact.**
   A developer can see what changed. But without a dependency graph, they cannot easily determine what else could be affected — transitively.

3. **Code review is insufficient.**
   Human reviewers cannot exhaustively trace all call chains from a changed function. They focus on what's visible, not on what's reachable.

4. **"It works" is not evidence.**
   Without running the old and new versions under the same conditions and comparing their behavior, "it works" is a belief, not a finding.

## What the System Must Provide

1. A structured analysis of what changed (file-level and symbol-level).
2. A dependency/call graph showing what is reachable from the changed code.
3. A blast radius: every symbol and module potentially affected by the change.
4. A set of relevant tests selected by static analysis.
5. Actual execution of those tests against both the original and migrated versions.
6. A deterministic behavioral comparison: what passed, what failed, what regressed.
7. An evidence record: structured, inspectable, not an AI opinion.
8. An AI-assisted interpretation: migration intent, risk narrative, key concerns.
9. A final classification: Verified / Partially Verified / Regression Detected / Unverified.

## What the System Does NOT Do

- It does not guarantee correctness of the migration.
- It does not replace code review.
- It does not generate tests (MVP).
- It does not support non-Python codebases (MVP).
- It does not give AI opinions as primary evidence. AI interprets evidence; it does not produce it.
