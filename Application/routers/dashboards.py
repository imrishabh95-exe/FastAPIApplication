from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Dict, Any

from Application.auth import get_current_user, User
from Application.db import dashboards_collection

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# Request model for creating a dashboard
class DashboardCreateRequest(BaseModel):
    title: str
    description: str
    theme_color: str

# Response model
class DashboardResponse(BaseModel):
    dashboard_id: str
    owner_id: str
    title: str
    shared_with: List[str]
    bank_accounts: List[Dict[str, Any]]
    defaults: Dict[str, Any]
    created_on: datetime
    description: str
    theme_color: str
    credit_cards: List[Dict[str, Any]]

@router.post("/create", response_model=DashboardResponse)
async def create_dashboard(
    request: DashboardCreateRequest,
    current_user: User = Depends(get_current_user)
):
    dashboard_data = {
        "dashboard_id": str(ObjectId()),
        "owner_id": current_user.id,
        "title": request.title,
        "shared_with": [],
        "bank_accounts": [],
        "defaults": {},
        "created_on": datetime.utcnow(),
        "description": request.description,
        "theme_color": request.theme_color,
        "credit_cards": []
    }

    await dashboards_collection.insert_one(dashboard_data)

    return dashboard_data
