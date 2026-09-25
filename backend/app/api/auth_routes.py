from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate investigator or admin user."""
    # Simplified authentication for forensic dashboard prototype
    if req.username and req.password:
        return {
            "access_token": "mediadna-fake-jwt-token-investigator-2026",
            "token_type": "bearer",
            "user": {
                "id": "user-investigator-01",
                "username": req.username,
                "full_name": "Inspector R. Sharma",
                "badge_number": "CHD-CYBER-8841",
                "role": "INVESTIGATOR"
            }
        }
    raise HTTPException(status_code=400, detail="Invalid username or password")
