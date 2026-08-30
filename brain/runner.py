import time
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
import networkx as nx

import database
from models import RunStatus
from brain.diff_analyzer import analyze_file_diff, analyze_symbol_diff
from brain.graph_builder import build_graph, save_graph
from brain.blast_radius import compute_blast_radius
from brain.test_selector import select_tests
from brain.sandbox import run_tests_in_sandbox
from brain.comparator import compare_results
from brain.evidence import assemble_evidence

def _extract_zip(zip_path: Path, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
        
    # Flatten if zip contained a single top-level directory
    entries = list(target_dir.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        single_dir = entries[0]
        for item in single_dir.iterdir():
            shutil.move(str(item), str(target_dir / item.name))
        single_dir.rmdir()

def run_pipeline(run_id: str):
    """
    Main orchestrator for the analysis pipeline.
    Runs asynchronously in a FastAPI BackgroundTask.
    """
    try:
        # Phase 1: Analysis
        database.update_run_status(run_id, RunStatus.ANALYZING.value)
        
        run_dir = Path(database.DB_PATH).parent / "runs" / run_id
        original_zip = run_dir / "original.zip"
        migrated_zip = run_dir / "migrated.zip"
        
        original_dir = run_dir / "original"
        migrated_dir = run_dir / "migrated"
        
        _extract_zip(original_zip, original_dir)
        _extract_zip(migrated_zip, migrated_dir)
        
        file_diffs = analyze_file_diff(original_dir, migrated_dir)
        symbol_diffs = analyze_symbol_diff(file_diffs, original_dir, migrated_dir)
        
        graph_original = build_graph(original_dir)
        graph_migrated = build_graph(migrated_dir)
        
        save_graph(graph_original, run_dir / "graph_original.json")
        save_graph(graph_migrated, run_dir / "graph_migrated.json")
        
        changed_symbol_ids = [sd.symbol_id for sd in symbol_diffs]
        blast_radius = compute_blast_radius(graph_migrated, changed_symbol_ids)
        
        affected_symbols = blast_radius.changed_symbols + blast_radius.all_affected
        selected_tests = select_tests(migrated_dir, affected_symbols)
        
        # Phase 2: Execution
        database.update_run_status(run_id, RunStatus.EXECUTING.value)
        
        test_results_original = run_tests_in_sandbox(str(original_dir.resolve()))
        test_results_migrated = run_tests_in_sandbox(str(migrated_dir.resolve()))
        
        comparisons = compare_results(test_results_original, test_results_migrated)
        
        # Phase 3: Interpretation
        database.update_run_status(run_id, RunStatus.INTERPRETING.value)
        
        evidence = assemble_evidence(
            symbol_diffs=symbol_diffs,
            blast_radius=blast_radius,
            graph_migrated=graph_migrated,
            selected_tests=selected_tests,
            comparisons=comparisons
        )
        
        # Construct graph JSON representation for React Flow
        graph_nodes = []
        graph_edges = []
        for n, data in graph_migrated.nodes(data=True):
            graph_nodes.append({
                "id": str(n),
                "label": str(n),
                "file": data.get("file", ""),
                "kind": data.get("kind", "")
            })
        for u, v in graph_migrated.edges():
            graph_edges.append({
                "source": str(u),
                "target": str(v)
            })
            
        report_data = {
            "overall_status": "complete",
            "file_diffs": [fd.model_dump() for fd in file_diffs],
            "symbol_diffs": [sd.model_dump() for sd in symbol_diffs],
            "blast_radius": blast_radius.model_dump(),
            "selected_tests": selected_tests,
            "test_results_original": test_results_original,
            "test_results_migrated": test_results_migrated,
            "comparisons": comparisons.model_dump(),
            "evidence": [ev.model_dump() for ev in evidence],
            "graph": {
                "nodes": graph_nodes,
                "edges": graph_edges
            },
            "ai_interpretation": {
                "summary": "Deterministic migration analysis completed successfully.",
                "risk_level": "low" if comparisons.regressions_count == 0 else "high",
                "risk_score": 0.0 if comparisons.regressions_count == 0 else 0.8,
                "recommendations": ["Review symbol diffs and passing test coverage."]
            }
        }
        
        generated_at = datetime.now(timezone.utc).isoformat()
        database.save_report(run_id, json.dumps(report_data), generated_at)
        
        database.update_run_status(run_id, RunStatus.COMPLETE.value)
        
    except Exception as e:
        database.update_run_status(run_id, RunStatus.FAILED.value, str(e))

