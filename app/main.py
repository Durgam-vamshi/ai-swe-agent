

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.agent import router as agent_router
from app.api.routes.run import router as run_router
from app.api.routes.metrics import router as metrics_router

app = FastAPI(title="AI SWE Agent")

# ✅ CORS (already correct)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# ✅ Routers
app.include_router(agent_router, prefix="/api")
app.include_router(run_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")