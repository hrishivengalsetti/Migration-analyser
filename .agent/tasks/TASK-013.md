# TASK-013: Frontend Scaffold — Vite, React, Tailwind CSS & shadcn/ui

**Milestone**: M9  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-012 (complete)  

---

## Goal

Scaffold the React frontend application using Vite + React (JavaScript) + Tailwind CSS + shadcn/ui. Set up routing between Upload and Report pages. Configure the Vite dev server to proxy API requests to the FastAPI backend at `http://localhost:8000`.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 8: Frontend Architecture)
3. This task file

---

## Inputs

- Empty `frontend/` directory (to be created)

## Outputs

```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── index.css
│   ├── pages/
│   │   ├── UploadPage.jsx      ← Placeholder
│   │   └── ReportPage.jsx      ← Placeholder
│   └── components/
│       └── .gitkeep
└── .gitignore
```

---

## Acceptance Criteria

### AC-1: Project scaffolded with Vite + React
- `frontend/` directory exists with a working Vite + React project
- Uses JavaScript (NOT TypeScript)
- Created via `npx -y create-vite@latest ./ --template react` (or equivalent non-interactive command)

### AC-2: Tailwind CSS configured
- Tailwind CSS v3 installed and configured
- `tailwind.config.js` includes content paths for `./src/**/*.{js,jsx}`
- `postcss.config.js` exists with tailwindcss and autoprefixer plugins
- `src/index.css` includes Tailwind directives:
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```

### AC-3: shadcn/ui initialized
- shadcn/ui components utility set up (at minimum the `cn()` utility function in `src/lib/utils.js`)
- If full shadcn init is complex, at minimum install `clsx` and `tailwind-merge` and create the `cn()` utility manually

### AC-4: React Router configured
- `react-router-dom` installed
- Routes configured in `App.jsx`:
  - `/` → `UploadPage` component
  - `/report/:runId` → `ReportPage` component

### AC-5: Vite proxy configured
- `vite.config.js` proxies `/api` requests to `http://localhost:8000`:
  ```js
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
  ```

### AC-6: Placeholder pages exist
- `src/pages/UploadPage.jsx` — renders a div with text "Upload Page" (placeholder)
- `src/pages/ReportPage.jsx` — renders a div with text "Report Page" and reads `runId` from URL params

### AC-7: Dev server starts
- `cd frontend && npm install && npm run dev` starts without errors
- Navigating to `http://localhost:5173` shows the Upload Page placeholder
- Navigating to `http://localhost:5173/report/test-id` shows the Report Page placeholder

### AC-8: Build succeeds
- `cd frontend && npm run build` completes without errors

---

## Non-Goals

- Do NOT implement any real UI components yet (that is TASK-014+)
- Do NOT implement API calls
- Do NOT style the pages beyond basic Tailwind setup
- Do NOT add testing framework yet
- Do NOT use TypeScript

---

## Technical Constraints

- Vite (latest)
- React 18+ (JavaScript)
- Tailwind CSS v3
- `react-router-dom` v6+
- `@xyflow/react` — do NOT install yet (that is TASK-016)
- Dev server port: 5173 (Vite default)
- Backend API port: 8000

---

## Verification

```bash
cd frontend && npm install && npm run build
```

Build must complete with zero errors.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
