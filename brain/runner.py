import os
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timezone
import networkx as nx

try:
    import database
except ImportError:
    # If run from backend, it might need backend.database
    try:
        from backend import database
    except ImportError:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        import database

try:
    from models import (
        RunStatus,
        Classification,
        ReportSummary,
        GraphNode,
        GraphEdge,
        GraphData,
        Report,
        ComparisonStatus
    )
except ImportError:
    try:
        from backend.models import (
            RunStatus,
            Classification,
            ReportSummary,
            GraphNode,
            GraphEdge,
            GraphData,
            Report,
            ComparisonStatus
        )
    except ImportError:
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
        from models import (
            RunStatus,
            Classification,
            ReportSummary,
            GraphNode,
            GraphEdge,
            GraphData,
            Report,
            ComparisonStatus
        )

from brain.diff_analyzer import analyze_file_diff, analyze_symbol_diff
from brain.graph_builder import build_graph, save_graph
from brain.blast_radius import compute_blast_radius
from brain.test_selector import select_tests
from brain.sandbox import run_tests_in_sandbox
from brain.comparator import compare_results
from brain.evidence_collector import collect_evidence
from brain.interpreter import generate_narrative


def _extract_zip(zip_path: Path, target_dir: Path):
    """Extract zip contents to target_dir and flatten a single top-level wrapper dir if present."""
    import logging
    logger = logging.getLogger("brain.runner._extract_zip")
    logger.info(f"Extracting {zip_path} to {target_dir}")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, "r") as z:
        logger.info(f"Zip opened. Extracting to {target_dir}")
        z.extractall(target_dir)
        logger.info(f"Extraction complete for {target_dir}")
        
    items = list(target_dir.iterdir())
    if len(items) == 1 and items[0].is_dir():
        wrapper_dir = items[0]
        for child in list(wrapper_dir.iterdir()):
            shutil.move(str(child), str(target_dir / child.name))
        wrapper_dir.rmdir()


def run_pipeline(run_id: str):
    """
    Main orchestrator for the analysis pipeline.
    Sequentially executes TASK-004 through TASK-011.
    """
    import logging
    # Force log output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("brain.runner")
    
    # We must ensure background tasks use asyncio and do not fail on imports or db connections
    logger.info(f"========== STARTING PIPELINE FOR RUN {run_id} ==========")
    try:
        logger.info(f"Unzip Phase for {run_id}")
        # 1. Unzip Phase
        logger.info("Fetching paths from database...")
        try:
            orig_zip_str, migr_zip_str = database.get_run_paths(run_id)
        except Exception as e:
            logger.error(f"Error fetching paths: {e}")
            raise
        logger.info(f"Paths: orig={orig_zip_str}, migr={migr_zip_str}")
        orig_zip_path = Path(orig_zip_str)
        migr_zip_path = Path(migr_zip_str)
        
        run_dir = orig_zip_path.parent
        orig_dir = run_dir / "original"
        migr_dir = run_dir / "migrated"
        
        _extract_zip(orig_zip_path, orig_dir)
        logger.info("Extracted original zip")
        _extract_zip(migr_zip_path, migr_dir)
        logger.info("Extracted migrated zip")
        
        logger.info("2. Analysis Phase")
        # 2. Analysis Phase
        database.update_run_status(run_id, RunStatus.ANALYZING.value)
        
        file_diffs = analyze_file_diff(orig_dir, migr_dir)
        symbol_diffs = analyze_symbol_diff(file_diffs, orig_dir, migr_dir)
        changed_symbols = [sd.symbol_id for sd in symbol_diffs]
        
        graph_migr = build_graph(migr_dir)
        save_graph(graph_migr, run_dir / "graph_migrated.json")
        
        blast_radius = compute_blast_radius(graph_migr, changed_symbols)
        affected_symbols = sorted(list(set(blast_radius.changed_symbols) | set(blast_radius.all_affected)))
        
        selected_tests = select_tests(migr_dir, affected_symbols)
        
        logger.info("3. Execution Phase")
        # 3. Execution Phase
        database.update_run_status(run_id, RunStatus.EXECUTING.value)
        
        orig_results = run_tests_in_sandbox(str(orig_dir), selected_tests)
        migr_results = run_tests_in_sandbox(str(migr_dir), selected_tests)
        
        comparisons = compare_results(orig_results, migr_results)
        
        logger.info("4. Interpretation Phase")
        # 4. Interpretation Phase
        database.update_run_status(run_id, RunStatus.INTERPRETING.value)
        
        evidence_data = collect_evidence(symbol_diffs, blast_radius, selected_tests, comparisons, migr_dir)
        
        # Deterministic Classification Logic
        regressions_count = sum(1 for e in evidence_data if e.comparison == ComparisonStatus.REGRESSION)
        unverified_count = sum(1 for e in evidence_data if e.comparison == ComparisonStatus.UNVERIFIED)
        total_tests_run = comparisons.total_tests
        
        if regressions_count > 0:
            classification = Classification.REGRESSION_DETECTED
        elif total_tests_run == 0 or (len(evidence_data) > 0 and unverified_count == len(evidence_data)):
            classification = Classification.UNVERIFIED
        elif unverified_count > 0:
            classification = Classification.PARTIALLY_VERIFIED
        else:
            classification = Classification.VERIFIED
            
        diff_summary = {
            "total_files_changed": len([f for f in file_diffs if f.status != "unchanged"]),
            "total_symbols_changed": len(symbol_diffs),
        }
        blast_radius_summary = {
            "changed_symbols": len(blast_radius.changed_symbols),
            "directly_affected": len(blast_radius.directly_affected),
            "transitively_affected": len(blast_radius.transitively_affected),
            "total_affected": blast_radius.total_affected_count,
        }
        execution_summary = {
            "total_tests": comparisons.total_tests,
            "regressions": comparisons.regressions_count,
            "fixed": comparisons.fixed_count,
            "unchanged": comparisons.unchanged_count,
            "unverified": comparisons.unverified_count,
        }
        
        ai_interpretation = generate_narrative(
            diff_summary,
            blast_radius_summary,
            execution_summary,
            evidence_data
        )
        
        logger.info(f"AI Interpretation generated")
        # 5. Completion Phase
        graph_nodes = [
            GraphNode(
                id=str(n),
                kind=str(data.get("kind", "unknown")),
                file=str(data.get("file", "unknown"))
            )
            for n, data in graph_migr.nodes(data=True)
        ]
        graph_edges = [
            GraphEdge(
                source=str(u),
                target=str(v),
                kind=str(data.get("kind", "calls"))
            )
            for u, v, data in graph_migr.edges(data=True)
        ]
        graph_data = GraphData(nodes=graph_nodes, edges=graph_edges)
        
        summary = ReportSummary(
            total_files_changed=diff_summary["total_files_changed"],
            total_symbols_changed=diff_summary["total_symbols_changed"],
            total_affected_symbols=blast_radius.total_affected_count,
            total_tests_run=total_tests_run,
            regressions_count=regressions_count
        )
        
        created_at_iso = datetime.now(timezone.utc).isoformat()
        
        report = Report(
            run_id=run_id,
            created_at=created_at_iso,
            classification=classification,
            summary=summary,
            ai_interpretation=ai_interpretation,
            file_diffs=file_diffs,
            symbol_diffs=symbol_diffs,
            blast_radius=blast_radius,
            graph_data=graph_data,
            test_results=comparisons.test_results,
            evidence=evidence_data
        )
        
        report_json = report.model_dump_json(indent=2)
        
        report_file = run_dir / "report.json"
        report_file.write_text(report_json, encoding="utf-8")
        
        database.save_report(run_id, report_json, created_at_iso)
        database.update_run_status(run_id, RunStatus.COMPLETE.value)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"PIPELINE FAILED: {e}\n{traceback.format_exc()}")
        print(f"PIPELINE FAILED: {e}")
        database.update_run_status(run_id, RunStatus.FAILED.value, str(e))
