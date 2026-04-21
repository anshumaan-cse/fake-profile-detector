"""
FakeProfileDetector – FastAPI Application Entry Point
"""

import os
from pathlib  import Path
from fastapi  import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses   import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.analysis   import router as analysis_router
from backend.routes.evaluation import router as eval_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FakeProfileDetector API",
    version="2.0.0",
    description="Hybrid AI (Rule-Based + ML) fake social-media profile detection system",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analysis_router)
app.include_router(eval_router)

# ── Static frontend ───────────────────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    return FileResponse(str(FRONTEND_DIR / "dashboard.html"))


@app.get("/research", include_in_schema=False)
def serve_research():
    return FileResponse(str(FRONTEND_DIR / "research.html"))


# ── Startup: auto-train if models missing ────────────────────────────────────
@app.on_event("startup")
def startup_event():
    model_path = Path(__file__).parent / "backend" / "models" / "random_forest.pkl"
    if not model_path.exists():
        print("[Startup] Models not found – training now …")
        from backend.models.trainer import train_models
        train_models()
        print("[Startup] Training complete.")
    else:
        print("[Startup] Models already present – skipping training.")
