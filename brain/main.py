from fastapi import FastAPI

app = FastAPI(title="Migration Verifier Brain API")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "brain"}
