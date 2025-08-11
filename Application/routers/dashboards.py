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


# ---------------- Get all dashboards for logged-in user ----------------
@router.get("/my-dashboards")
async def get_my_dashboards(current_user: User = Depends(get_current_user)):
    """Returns dashboards owned by and shared with the current user."""
    
    owned_dashboards = await dashboards_collection.find(
        {"owner_id": current_user.id}
    ).to_list(length=None)

    shared_dashboards = await dashboards_collection.find(
        {"shared_with": {"$in": [current_user.id]}}
    ).to_list(length=None)

    # Convert ObjectId to str in MongoDB results
    def serialize(doc):
        doc["_id"] = str(doc["_id"])
        return doc

    return {
        "owned": [serialize(d) for d in owned_dashboards],
        "shared_access": [serialize(d) for d in shared_dashboards]
    }
