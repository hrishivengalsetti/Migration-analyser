from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid
import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

import database
from models import CreateRunResponse, Run, RunStatus, Report
from brain.runner import run_pipeline

DATA_DIR = Path(__file__).parent / "data" / "runs"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database on startup
    database.init_db()
    yield

app = FastAPI(title="Migration Verifier API", lifespan=lifespan)

# Configure CORS for the frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/runs", response_model=CreateRunResponse)
async def create_run_endpoint(
    background_tasks: BackgroundTasks,
    original: UploadFile = File(...),
    migrated: UploadFile = File(...)
):
    if not original or not migrated:
        raise HTTPException(status_code=400, detail="Both original and migrated zip files are required.")
    
    run_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    status = RunStatus.PENDING.value
    
    # Save files to disk
    run_dir = DATA_DIR / run_id
    os.makedirs(run_dir, exist_ok=True)
    
    original_path = run_dir / "original.zip"
    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(original.file, buffer)
        
    migrated_path = run_dir / "migrated.zip"
    with open(migrated_path, "wb") as buffer:
        shutil.copyfileobj(migrated.file, buffer)
    
    # Store paths in database
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runs (id, created_at, status, original_path, migrated_path) VALUES (?, ?, ?, ?, ?)",
            (run_id, created_at, status, str(original_path), str(migrated_path))
        )
        conn.commit()
    finally:
        conn.close()
    
    # Trigger background pipeline
    background_tasks.add_task(run_pipeline, run_id)
    
    return CreateRunResponse(run_id=run_id, status=status)

@app.get("/api/runs/{run_id}", response_model=Run)
def get_run_endpoint(run_id: str):
    run_data = database.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return Run(
        run_id=run_data["id"],
        created_at=run_data["created_at"],
        status=run_data["status"],
        error=run_data["error"]
    )

@app.get("/api/runs/{run_id}/report", response_model=Report)
def get_report_endpoint(run_id: str):
    run_data = database.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")
        
    report_data = database.get_report(run_id)
    if not report_data or not report_data.get("data"):
        raise HTTPException(status_code=404, detail="Report not found")
        
    return JSONResponse(content=json.loads(report_data["data"]))
