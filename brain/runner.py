import time
import json
from datetime import datetime, timezone
import database
from models import RunStatus

def run_pipeline(run_id: str):
    """
    Main orchestrator for the analysis pipeline.
    Runs asynchronously in a FastAPI BackgroundTask.
    """
    try:
        # Stub step 1: Analyzing
        database.update_run_status(run_id, RunStatus.ANALYZING.value)
        time.sleep(1)  # Simulate work
        
        # Stub step 2: Executing
        database.update_run_status(run_id, RunStatus.EXECUTING.value)
        time.sleep(1)  # Simulate work
        
        # Generate dummy report data for stub
        dummy_report = {
            "overall_status": "complete",
            "diff": [],
            "graph": {"nodes": [], "edges": []},
            "tests": [],
            "evidence": [],
            "ai_interpretation": {
                "summary": "Migration completed successfully.",
                "risk_level": "low",
                "risk_score": 0.0,
                "recommendations": []
            }
        }
        
        generated_at = datetime.now(timezone.utc).isoformat()
        database.save_report(run_id, json.dumps(dummy_report), generated_at)
        
        # Stub step 3: Complete
        database.update_run_status(run_id, RunStatus.COMPLETE.value)
        
    except Exception as e:
        # CRITICAL: If the pipeline fails, record the error so the frontend knows
        database.update_run_status(run_id, RunStatus.FAILED.value, str(e))
