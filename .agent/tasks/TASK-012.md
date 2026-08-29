# TASK-012: Full Pipeline Wiring & End-to-End Integration Test

**Milestone**: M8  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-011 (complete)  

---

## Goal

Wire all pipeline modules sequentially into `runner.py`, replacing the stub from TASK-002 with real pipeline execution. Each stage calls the appropriate module, passes data forward, updates the run status in SQLite, and handles errors. Write a full end-to-end integration test that uploads zip files, waits for the pipeline, and verifies the generated report.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/runner.py` (current stub from TASK-002)
4. `backend/pipeline/` (all modules)
5. This task file

---

## Inputs

- All pipeline modules from TASK-003 through TASK-011

## Outputs

```
backend/pipeline/runner.py           ← Updated: replace stub with full pipeline
backend/tests/test_integration.py    ← New file
```

---

## Acceptance Criteria

### AC-1: Pipeline execution sequence
`run_pipeline(run_id: str)` must execute in this exact order:

```python
def run_pipeline(run_id: str):
    try:
        # Phase 1: Analysis
        update_run_status(run_id, "analyzing")
        
        # 1a. Extract zip files
        run_dir = Path(f"backend/data/runs/{run_id}")
        original_dir = run_dir / "original"
        migrated_dir = run_dir / "migrated"
        _extract_zip(run_dir / "original.zip", original_dir)
        _extract_zip(run_dir / "migrated.zip", migrated_dir)
        
        # 1b. File-level diff
        file_diffs = analyze_file_diff(original_dir, migrated_dir)
        
        # 1c. Symbol-level diff
        symbol_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
        
        # 1d. Build code graphs
        graph_original = build_graph(original_dir)
        graph_migrated = build_graph(migrated_dir)
        save_graph(graph_original, run_dir / "graph_original.json")
        save_graph(graph_migrated, run_dir / "graph_migrated.json")
        
        # 1e. Blast radius (using migrated graph)
        changed_symbol_ids = [sd.symbol_id for sd in symbol_diffs]
        blast_radius = compute_blast_radius(graph_migrated, changed_symbol_ids)
        
        # 1f. Test selection
        affected_symbols = blast_radius.changed_symbols + blast_radius.all_affected
        selected_tests = select_tests(migrated_dir, affected_symbols)
        
        # Phase 2: Execution
        update_run_status(run_id, "executing")
        
        # 2a. Run tests in sandboxes
        test_results_original = run_tests_in_sandbox(str(original_dir.resolve()))
        test_results_migrated = run_tests_in_sandbox(str(migrated_dir.resolve()))
        
        # 2b. Compare results
        comparisons = compare_results(test_results_original, test_results_migrated)
        
        # Phase 3: Interpretation
        update_run_status(run_id, "interpreting")
        
        # 3a. Collect evidence
        evidence = collect_evidence(symbol_diffs, blast_radius, selected_tests, comparisons, test_to_symbols_map)
        
        # 3b. Classify
        tests_run = test_results_migrated.get("summary", {}).get("total", 0)
        classification = classify(evidence, tests_run)
        
        # 3c. AI interpretation
        ai_interpretation = interpret_migration(...)
        
        # 3d. Assemble report
        report = assemble_report(
            run_id=run_id,
            file_diffs=file_diffs,
            symbol_diffs=symbol_diffs,
            blast_radius=blast_radius,
            test_results_original=test_results_original,
            test_results_migrated=test_results_migrated,
            comparisons=comparisons,
            evidence=evidence,
            classification=classification,
            ai_interpretation=ai_interpretation,
            graph_data=nx.node_link_data(graph_migrated),
        )
        
        # 3e. Save report
        save_report(run_id, report)
        
        update_run_status(run_id, "complete")
        
    except Exception as e:
        update_run_status(run_id, "failed", str(e))
```

### AC-2: Zip extraction
- Implement `_extract_zip(zip_path: Path, target_dir: Path)` helper
- Uses `zipfile.ZipFile` from stdlib
- Extracts to `target_dir`
- Handles the case where zip contents are inside a top-level directory (flatten if needed)

### AC-3: Global error handling
- The entire pipeline is wrapped in `try / except Exception as e`
- On ANY exception, `update_run_status(run_id, "failed", str(e))` is called
- The exception message is stored in the database

### AC-4: Status transitions
- Status progresses: `"pending"` → `"analyzing"` → `"executing"` → `"interpreting"` → `"complete"`
- On error at any stage: status is set to `"failed"`

### AC-5: Data flow integrity
- Each module receives the output of the previous module
- No data is lost between stages
- The final report contains all intermediate results

### AC-6: All tests pass
- `cd backend && pytest tests/test_integration.py -v` exits with code 0

---

## Non-Goals

- Do NOT redesign any pipeline module — just wire them together
- Do NOT add new pipeline stages
- Do NOT implement retry logic
- Do NOT implement parallelism — sequential execution only
- Do NOT modify the API endpoints (except to ensure they work with the new pipeline)

---

## Technical Constraints

- `zipfile` stdlib for extraction
- All imports must reference the actual module paths
- The runner must work with FastAPI `BackgroundTasks`

---

## Test Requirements

Write tests in `backend/tests/test_integration.py`:

**Important**: This test requires Docker to be running for sandbox execution. Mark with `@pytest.mark.skipif` if Docker is unavailable.

1. `test_full_pipeline_end_to_end`:
   - Create two simple Python project directories (original and migrated) with a deliberate difference
   - Zip both directories into `BytesIO` objects
   - `POST /api/runs` with both zips via `TestClient`
   - After the post returns, query `GET /api/runs/{run_id}` → status should reach `"complete"` (TestClient runs BackgroundTasks synchronously)
   - Query `GET /api/runs/{run_id}/report` → verify:
     - Response is 200
     - Report JSON contains `classification`, `file_diffs`, `symbol_diffs`, `evidence`
     - At least one `file_diff` exists
     - Classification is one of the valid enum values

2. `test_pipeline_handles_error_gracefully`:
   - Submit invalid zip files (not real zip content)
   - Verify run status becomes `"failed"` with an error message

3. `test_pipeline_status_progression`:
   - Submit valid zips
   - After completion, verify the final status is `"complete"` (or `"failed"` if Docker is unavailable — this is acceptable)

---

## Verification

```bash
cd backend && pytest tests/test_integration.py -v
```

Note: Tests will be skipped if Docker is not available. This is acceptable for the integration test.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
