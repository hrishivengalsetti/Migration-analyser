# Dummy Backend for Frontend Testing

This folder provides a mock backend that matches the frontend's expected API contract so the UI can be tested without the real backend.

## Start the server

```bash
cd "dummy backend"
python -m pip install -r requirements.txt
python server.py
```

The app runs on http://localhost:8000 and is configured to support the frontend's Vite proxy at /api.

## API Contract

- POST /api/runs
- GET /api/runs/{run_id}
- GET /api/runs/{run_id}/report

## Notes

- This is intentionally a mock service for local UI testing.
- It is safe to delete later when the real backend is connected.
