from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel
from typing import List

from Application.auth import get_current_user, User
from Application.db import transactional_groups_collection, chats_collection

router = APIRouter(prefix="/transactional-group", tags=["Transactional Group"])

# --- Models ---
class TransactionalGroupCreateRequest(BaseModel):
    title: str
    description: str
    color: str

class TransactionalGroupResponse(BaseModel):
    transactional_group_id: str
    owner_id: str
    title: str
    shared_with: List[str]
    created_on: datetime
    is_active: bool
    description: str
    chat_id: str
    color: str


# --- Create Transactional Group ---
@router.post("/create", response_model=TransactionalGroupResponse)
async def create_transactional_group(
    request: TransactionalGroupCreateRequest,
    current_user: User = Depends(get_current_user)
):
    # Step 1: Create a chat for the group
    chat_id = str(ObjectId())
    chat_data = {
        "chat_id": chat_id,
        "transactional_group_id": None,  # will be linked after group creation
        "participants": [{
            "user_id": current_user.id,
            "user_first_name": current_user.first_name,
            "user_last_name": current_user.last_name,
            "user_email": current_user.email
        }],
        "messages": []
    }
    await chats_collection.insert_one(chat_data)

    # Step 2: Create transactional group and link chat_id
    group_id = str(ObjectId())
    group_data = {
        "transactional_group_id": group_id,
        "owner_id": current_user.id,
        "title": request.title,
        "shared_with": [],
        "created_on": datetime.utcnow(),
        "is_active": True,
        "description": request.description,
        "chat_id": chat_id,
        "color": request.color
    }
    await transactional_groups_collection.insert_one(group_data)

    # Step 3: Update chat with the transactional_group_id
    await chats_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"transactional_group_id": group_id}}
    )

    return group_data


# --- Get all transactional groups for logged-in user ---
@router.get("/my-transactional-groups")
async def get_my_transactional_groups(current_user: User = Depends(get_current_user)):
    """Returns transactional groups owned by and shared with the current user."""

    owned_groups = await transactional_groups_collection.find(
        {"owner_id": current_user.id}
    ).to_list(length=None)

    shared_groups = await transactional_groups_collection.find(
        {"shared_with": {"$in": [current_user.id]}}
    ).to_list(length=None)

    def serialize(doc):
        doc["_id"] = str(doc["_id"])
        return doc

    return {
        "owned": [serialize(g) for g in owned_groups],
        "shared_access": [serialize(g) for g in shared_groups]
    }
