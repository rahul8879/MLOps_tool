from fastapi import FastAPI
from routers import experiments, runs

app = FastAPI(
    title="AstraZeneca MLOps MVP",
    version="0.1.0 — Sprint 1"
)

app.include_router(experiments.router)
app.include_router(runs.router)        

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "sprint": "Sprint 1"}