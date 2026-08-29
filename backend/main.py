from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
from datetime import datetime, timezone

import database
from models import CreateRunResponse, Run, RunStatus

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
    original: UploadFile = File(...),
    migrated: UploadFile = File(...)
):
    if not original or not migrated:
        raise HTTPException(status_code=400, detail="Both original and migrated zip files are required.")
    
    run_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    status = RunStatus.PENDING.value
    
    database.create_run(run_id, created_at, status)
    
    # Returning the response without firing a background task (that is TASK-002)
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
