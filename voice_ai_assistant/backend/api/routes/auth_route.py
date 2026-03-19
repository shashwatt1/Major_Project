from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def auth_status():
    return {"status": "auth route placeholder"}
