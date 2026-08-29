import time
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
        
        # Stub step 3: Complete
        database.update_run_status(run_id, RunStatus.COMPLETE.value)
        
    except Exception as e:
        # CRITICAL: If the pipeline fails, record the error so the frontend knows
        database.update_run_status(run_id, RunStatus.FAILED.value, str(e))
