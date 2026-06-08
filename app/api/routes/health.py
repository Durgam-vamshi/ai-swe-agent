from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"message": "AI SWE Agent Running 🚀"}

@router.get("/health")
def health():
    return {"status": "ok"}