# TASK-014: Upload Page Component & Progress Polling

**Milestone**: M9  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-013 (complete)  

---

## Goal

Build the file upload interface with drag-and-drop zip file inputs, form submission to the backend API, and real-time status polling with a progress bar. When the pipeline completes, automatically navigate to the report page. When it fails, display an error banner.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 8: Frontend Architecture)
3. `frontend/src/App.jsx` (from TASK-013)
4. `frontend/src/pages/UploadPage.jsx` (from TASK-013)
5. This task file

---

## Inputs

- Scaffolded frontend from TASK-013

## Outputs

```
frontend/src/pages/UploadPage.jsx            ← Updated: full implementation
frontend/src/components/FileUploader.jsx     ← New file
frontend/src/components/StatusProgress.jsx   ← New file
```

---

## Acceptance Criteria

### AC-1: File upload inputs
- Two separate file input areas for `original.zip` and `migrated.zip`
- Each input accepts only `.zip` files (`accept=".zip"`)
- Supports both click-to-select and drag-and-drop
- Displays the selected filename after selection
- Visual feedback on drag-over (border color change)

### AC-2: Submit button
- "Analyze Migration" button visible when both files are selected
- Button is disabled until both files are selected
- Button shows loading state during submission

### AC-3: Form submission
- On submit, sends `POST /api/runs` with `multipart/form-data`
- Form fields: `original` (zip file), `migrated` (zip file)
- Uses `fetch` API (do NOT add axios)
- On success (HTTP 200), extracts `run_id` from response and starts polling

### AC-4: Status polling
- After submission, polls `GET /api/runs/{run_id}` every 2 seconds
- Displays a progress bar reflecting the current status:
  - `pending` → 10% (gray)
  - `analyzing` → 30% (blue)
  - `executing` → 60% (blue)
  - `interpreting` → 85% (blue)
  - `complete` → 100% (green)
- Displays the current status text below the progress bar

### AC-5: Automatic redirect
- When status reaches `"complete"`, stops polling and navigates to `/report/{run_id}` using React Router's `useNavigate()`
- Small delay (500ms) before redirect to show 100% completion

### AC-6: Error handling
- When status reaches `"failed"`, stops polling and displays a red error banner
- Error banner shows the error message from the API response
- "Try Again" button resets the form to initial state

### AC-7: Visual design
- Clean, modern UI with Tailwind CSS
- Card-based layout centered on the page
- Upload areas have dashed borders and upload icon indicators
- Progress bar has smooth CSS transitions
- Responsive layout (works on desktop widths, mobile not required)

### AC-8: StatusProgress component
- `StatusProgress.jsx` is a reusable component:
  ```jsx
  <StatusProgress status="analyzing" error={null} />
  ```
- Accepts `status` (string) and `error` (string or null) props

---

## Non-Goals

- Do NOT implement the report page (that is TASK-015)
- Do NOT implement file validation beyond `.zip` extension check
- Do NOT implement file size limits
- Do NOT implement multi-run history
- Do NOT use WebSockets — polling is sufficient

---

## Technical Constraints

- Use `fetch` API for HTTP requests (no axios)
- Use `react-router-dom` `useNavigate` for navigation
- Use Tailwind CSS for all styling
- Polling interval: 2 seconds
- Clear polling interval on unmount (use `useEffect` cleanup)

---

## Component Structure

### FileUploader.jsx
```jsx
// Props:
// - label: string ("Original Codebase" or "Migrated Codebase")
// - onFileSelect: (file: File) => void
// - accept: string (".zip")
// - selectedFile: File | null

function FileUploader({ label, onFileSelect, accept, selectedFile }) {
  // Drag-and-drop zone with click-to-select fallback
  // Shows filename when file is selected
  // Visual drag-over feedback
}
```

### StatusProgress.jsx
```jsx
// Props:
// - status: string ("pending" | "analyzing" | "executing" | "interpreting" | "complete" | "failed")
// - error: string | null

function StatusProgress({ status, error }) {
  // Maps status to progress percentage
  // Renders progress bar with label
  // Shows error banner if status is "failed"
}
```

---

## Verification

```bash
cd frontend && npm run build
```

Build must complete without errors. Manual verification of upload flow in browser.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
