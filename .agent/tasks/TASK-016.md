# TASK-016: Report Page — Impact Tab (React Flow Blast Radius Graph)

**Milestone**: M9  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-015 (complete)  

---

## Goal

Build the interactive blast radius graph visualization using React Flow in the Impact tab of the Report page. Transform the NetworkX graph data (included in the report JSON) into React Flow nodes and edges, with color-coded styling based on whether a symbol was changed, directly affected, or transitively affected. Include an explicit static analysis disclaimer banner.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 5: Code Graph)
3. `frontend/src/pages/ReportPage.jsx` (from TASK-015)
4. `backend/models.py` — understand BlastRadius and graph_data structure
5. This task file

---

## Inputs

- `report.graph_data` — NetworkX `node_link_data()` format: `{ "nodes": [...], "links": [...] }`
- `report.blast_radius` — `{ "changed_symbols": [...], "directly_affected": [...], "transitively_affected": [...] }`

## Outputs

```
frontend/src/components/GraphView.jsx   ← New file
frontend/src/pages/ReportPage.jsx       ← Updated: Impact tab renders GraphView
frontend/package.json                    ← Updated: add @xyflow/react dependency
```

---

## Acceptance Criteria

### AC-1: React Flow installed
- `@xyflow/react` installed as a dependency
- Imported and used in `GraphView.jsx`

### AC-2: Graph data transformation
- Transform NetworkX `node_link_data` format to React Flow format:
  - Each NetworkX node becomes a React Flow node with:
    - `id`: node's symbol ID
    - `data.label`: symbol name (last part of symbol ID, e.g., "calculate_discount")
    - `position`: auto-laid out (see AC-3)
    - `style`: color-coded border based on blast radius category
  - Each NetworkX link becomes a React Flow edge with:
    - `source`: link's source node ID
    - `target`: link's target node ID
    - `animated`: true for edges to changed symbols
    - `label`: edge kind ("imports" or "calls")

### AC-3: Node layout
- Nodes are positioned using a simple automatic layout algorithm
- Use a basic grid/tree layout or dagre-style layout:
  - Option A: Install `dagre` for automatic DAG layout (preferred if simple)
  - Option B: Simple columnar layout — changed symbols in center, directly affected left, transitively affected right, with y-spacing
- Nodes should not overlap

### AC-4: Node styling by blast radius category
- **Changed symbols** (`blast_radius.changed_symbols`): Red/orange border, bold
- **Directly affected** (`blast_radius.directly_affected`): Yellow border
- **Transitively affected** (`blast_radius.transitively_affected`): Blue border
- **Other nodes** (unaffected): Gray border, dimmed
- All nodes show the symbol name as label

### AC-5: Interactivity
- Zoom and pan controls enabled (React Flow built-in)
- Minimap displayed in corner (React Flow `<MiniMap />` component)
- Clicking a node highlights its connected edges and adjacent nodes

### AC-6: Static analysis disclaimer
- A banner/notice is displayed above or below the graph:
  - Text: "⚠️ Static AST Analysis — dynamic calls, reflection, and runtime dispatch are not captured in this graph."
  - Styled as a subtle info/warning banner (yellow or gray background)

### AC-7: Handles empty graph
- If `report.graph_data` is null or has no nodes, display a message: "No graph data available for this run."

### AC-8: Build succeeds
- `cd frontend && npm run build` completes without errors

---

## Non-Goals

- Do NOT implement node detail panel (clicking a node just highlights, no side panel)
- Do NOT implement edge filtering
- Do NOT implement graph search
- Do NOT implement graph export

---

## Technical Constraints

- `@xyflow/react` (React Flow v11+) — add to `package.json`
- Optional: `dagre` for layout — add only if needed
- React Flow CSS must be imported: `import '@xyflow/react/dist/style.css'`
- Graph must render within the tab content area (not full-page)

---

## Data Transformation Reference

```javascript
// NetworkX node_link_data format:
{
  "nodes": [
    {"id": "mypackage.pricing.calculate_discount", "kind": "function", "file": "pricing.py", "line_start": 10},
    ...
  ],
  "links": [
    {"source": "mypackage.api.checkout", "target": "mypackage.pricing.calculate_discount", "kind": "calls"},
    ...
  ]
}

// React Flow format:
const nodes = graphData.nodes.map((n, i) => ({
  id: n.id,
  data: { label: n.id.split('.').pop() },
  position: { x: ..., y: ... },
  style: { border: getBorderColor(n.id, blastRadius) },
}));

const edges = graphData.links.map((e, i) => ({
  id: `edge-${i}`,
  source: e.source,
  target: e.target,
  label: e.kind,
  animated: blastRadius.changed_symbols.includes(e.target),
}));
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
