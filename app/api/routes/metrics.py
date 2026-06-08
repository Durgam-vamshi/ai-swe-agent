from fastapi import APIRouter
from app.store.metrics_store import get_metrics

router = APIRouter()


@router.get("/metrics")
def metrics():
    return get_metrics()