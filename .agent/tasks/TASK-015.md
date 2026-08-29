# TASK-015: Report Page — Summary & Changes Tabs

**Milestone**: M9  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-014 (complete)  

---

## Goal

Build the Report Viewer page with a tabbed interface. Implement the Summary tab with classification badge and execution metrics, and the Changes tab with a diff viewer for modified files and symbols. The report data is fetched from the backend API.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 8: Frontend Architecture)
3. `frontend/src/pages/ReportPage.jsx` (from TASK-013)
4. `backend/models.py` — understand the Report model structure
5. This task file

---

## Inputs

- Report JSON from `GET /api/runs/{run_id}/report`

## Outputs

```
frontend/src/pages/ReportPage.jsx                ← Updated: full implementation with tabs
frontend/src/components/ClassificationBadge.jsx  ← New file
frontend/src/components/DiffViewer.jsx           ← New file
```

---

## Acceptance Criteria

### AC-1: Report data fetching
- On mount, fetches report from `GET /api/runs/{run_id}/report` (runId from URL params)
- Shows loading spinner while fetching
- Shows error message if fetch fails or returns 404
- Stores report data in React state

### AC-2: Tab navigation
- Report page has 5 tabs: Summary, Changes, Impact, Tests, Evidence
- Only Summary and Changes tabs are implemented in this task (Impact, Tests, Evidence are placeholders showing "Coming soon")
- Active tab is visually highlighted
- Tabs are horizontal navigation at the top of the report content area

### AC-3: Classification badge component
- `ClassificationBadge.jsx` renders a colored badge based on classification:
  - `"verified"` → Green badge with checkmark icon, text "VERIFIED"
  - `"partially_verified"` → Yellow/amber badge with warning icon, text "PARTIALLY VERIFIED"
  - `"regression_detected"` → Red badge with X icon, text "REGRESSION DETECTED"
  - `"unverified"` → Gray badge with question mark icon, text "UNVERIFIED"
- Badge is prominently displayed at the top of the report

### AC-4: Summary tab content
- Displays at the top:
  - Classification badge (large, prominent)
  - Run ID
- Summary metrics in a card grid:
  - "Files Changed" — `report.summary.files_changed`
  - "Symbols Changed" — `report.summary.symbols_changed`
  - "Blast Radius" — `report.summary.blast_radius_count`
  - "Regressions" — `report.summary.regressions` (red if > 0)
  - "Tests Run" — `report.summary.tests_run`
- Each metric displayed as a card with a large number and label

### AC-5: Changes tab — File diff list
- Lists all files from `report.file_diffs`
- Each file shows:
  - File path
  - Status badge (ADDED = green, DELETED = red, MODIFIED = yellow)
- Clicking a file expands to show the diff

### AC-6: Changes tab — DiffViewer component
- `DiffViewer.jsx` displays a unified diff view for modified files
- Shows `original_content` and `migrated_content` side-by-side or in unified format
- Basic syntax highlighting for Python (use `<pre>` with monospace font, line numbers)
- Color-coded: removed lines in red background, added lines in green background
- For symbol diffs: show the symbol name, change kind, and source code diff

### AC-7: Visual design
- Clean, modern dark or light theme with Tailwind CSS
- Cards with subtle shadows and rounded corners
- Consistent spacing and typography
- The classification badge should be the visual centerpiece

### AC-8: Build succeeds
- `cd frontend && npm run build` completes without errors

---

## Non-Goals

- Do NOT implement the Impact tab (React Flow graph — that is TASK-016)
- Do NOT implement the Tests tab (that is TASK-017)
- Do NOT implement the Evidence tab (that is TASK-017)
- Do NOT implement AI Narrative display (that is TASK-017)
- Do NOT use a third-party diff library — implement a simple diff view
- Do NOT implement syntax highlighting library — basic `<pre>` formatting is sufficient

---

## Technical Constraints

- Use `fetch` API for data loading
- Use `react-router-dom` `useParams()` for extracting `runId`
- Use Tailwind CSS for all styling
- Use `useState` and `useEffect` for state management
- No external diff/syntax highlighting libraries

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
