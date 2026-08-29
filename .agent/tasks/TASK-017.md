# TASK-017: Report Page — Tests, Evidence & AI Narrative Tabs

**Milestone**: M9  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-016 (complete)  

---

## Goal

Complete the remaining three tabs of the Report page: Tests, Evidence, and a combined AI Narrative section. The Tests tab shows a table of pytest results comparing original vs migrated runs. The Evidence tab shows per-symbol evidence cards. The AI Narrative tab/card displays the Gemini Flash interpretation.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `frontend/src/pages/ReportPage.jsx` (from TASK-015/TASK-016)
4. `backend/models.py` — understand Evidence, AIInterpretation, and test result structures
5. This task file

---

## Inputs

- `report.comparisons` — list of per-test comparison dicts
- `report.test_results_original` and `report.test_results_migrated` — raw sandbox output dicts
- `report.evidence` — list of Evidence objects
- `report.ai_interpretation` — AIInterpretation object (may be null/fallback)

## Outputs

```
frontend/src/components/TestResults.jsx    ← New file
frontend/src/components/EvidencePanel.jsx  ← New file
frontend/src/components/AINarrative.jsx    ← New file
frontend/src/pages/ReportPage.jsx          ← Updated: all 5 tabs functional
```

---

## Acceptance Criteria

### AC-1: Tests Tab — Comparison table
- Displays a table with columns:
  - **Test Name** (nodeid)
  - **Original** (outcome badge: green "passed", red "failed", gray "skipped"/"missing")
  - **Migrated** (outcome badge: same color coding)
  - **Result** (comparison badge: green "passed_both", red "regression", blue "improvement", gray "failed_both")
- Table is sorted by test name
- Regressions are visually highlighted (red row background or bold red text)
- Shows summary row at the top: "X passed, Y regressions, Z total"

### AC-2: Tests Tab — Empty state
- If no tests were run, display: "No tests were executed for this migration."

### AC-3: Evidence Tab — Per-symbol cards
- Displays a card for each item in `report.evidence`
- Each card shows:
  - **Symbol ID** (e.g., `mypackage.pricing.calculate_discount`)
  - **File** path
  - **Change Kind** badge (added, deleted, body_changed, signature_changed)
  - **Comparison Status** badge:
    - `"verified"` → Green "✓ Verified"
    - `"regression"` → Red "✗ Regression"
    - `"improved"` → Blue "↑ Improved"
    - `"no_tests"` → Gray "? No Tests"
  - **Linked Tests**: list of test names under "Passing Tests" and "Failing Tests" sections
- Cards with regressions should be visually prominent (red border or background)

### AC-4: Evidence Tab — Empty state
- If no evidence exists, display: "No symbol changes detected in this migration."

### AC-5: AI Narrative section
- Displayed as a card/section (either its own tab or a card within the Summary tab — use a dedicated tab)
- Shows:
  - **Migration Intent**: `ai_interpretation.migration_intent`
  - **Risk Summary**: `ai_interpretation.risk_summary`
  - **Key Concerns**: bulleted list of `ai_interpretation.key_concerns`
  - **Confidence**: badge showing confidence level
- If `ai_interpretation` is null or contains the fallback message, display a graceful notice: "AI analysis not available — configure GEMINI_API_KEY for AI-powered insights."
- Clearly labeled as "AI-Generated Analysis" with a subtle disclaimer

### AC-6: All 5 tabs functional
- Summary, Changes, Impact, Tests, Evidence tabs all render without errors
- AI Narrative is either a 6th tab or embedded in Summary (use a tab)
- Tab switching is smooth with no page reloads

### AC-7: Visual consistency
- All tabs follow the same visual design language
- Consistent card styling, spacing, and typography
- Status badges use the same color scheme across all tabs
- Responsive table layout for test results

### AC-8: Build succeeds
- `cd frontend && npm run build` completes without errors

---

## Non-Goals

- Do NOT add filtering or search to the tables
- Do NOT add sorting controls to tables
- Do NOT add pagination
- Do NOT implement PDF export
- Do NOT implement test result details/stack traces

---

## Technical Constraints

- Use Tailwind CSS for all styling
- Use `<table>` elements for the test results table (not CSS grid)
- No external table library
- No external markdown rendering library for AI narrative

---

## Component Interfaces

### TestResults.jsx
```jsx
// Props:
// - comparisons: array of { test_id, original_outcome, migrated_outcome, comparison }
// - originalSummary: { passed, failed, error, total }
// - migratedSummary: { passed, failed, error, total }

function TestResults({ comparisons, originalSummary, migratedSummary }) { ... }
```

### EvidencePanel.jsx
```jsx
// Props:
// - evidence: array of { symbol_id, file, change_kind, comparison, failing_tests, passing_tests }

function EvidencePanel({ evidence }) { ... }
```

### AINarrative.jsx
```jsx
// Props:
// - interpretation: { migration_intent, risk_summary, key_concerns, confidence } | null

function AINarrative({ interpretation }) { ... }
```

---

## Verification

```bash
cd frontend && npm run build
```

Build must complete without errors.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
