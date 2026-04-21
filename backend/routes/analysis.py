"""
Analysis API Routes
POST /api/analyze  – full hybrid analysis
GET  /api/health   – health check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing   import Optional

from backend.services.hybrid_engine import analyze_profile

router = APIRouter(prefix="/api", tags=["analysis"])


class ProfileRequest(BaseModel):
    username:            str   = Field(default="",  description="Social media handle")
    bio:                 str   = Field(default="",  description="Profile bio text")
    caption:             str   = Field(default="",  description="Recent post caption")
    followers_count:     int   = Field(default=0,   ge=0)
    following_count:     int   = Field(default=0,   ge=0)
    account_age_days:    int   = Field(default=0,   ge=0)
    total_posts:         int   = Field(default=0,   ge=0)
    avg_likes:           int   = Field(default=0,   ge=0)
    avg_comments:        int   = Field(default=0,   ge=0)
    has_profile_picture: bool  = Field(default=False)


@router.get("/health")
def health():
    return {"status": "ok", "service": "FakeProfileDetector API"}


@router.post("/analyze")
def analyze(req: ProfileRequest):
    try:
        result = analyze_profile(req.model_dump())
        return {"success": True, "data": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
