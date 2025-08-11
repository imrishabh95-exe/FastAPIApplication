from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from Application.auth import get_current_user, User
from Application.db import chats_collection

router = APIRouter(prefix="/chat", tags=["Chat"])

# --- Models ---
class ChatParticipant(BaseModel):
    user_id: str
    user_first_name: str
    user_last_name: str
    user_email: str

class ChatMessage(BaseModel):
    message_id: str
    sender: Dict[str, str]  # id, first_name, last_name, email
    seen_by: List[str]
    text: str
    message_type: str
    time_stamp: datetime

class ChatCreateRequest(BaseModel):
    participants: List[ChatParticipant]

class ChatResponse(BaseModel):
    chat_id: str
    participants: List[ChatParticipant]
    messages: List[ChatMessage]

# --- Create Chat (internal use for transactional groups) ---
@router.post("/create", response_model=ChatResponse)
async def create_chat(
    request: ChatCreateRequest,
    current_user: User = Depends(get_current_user)
):
    chat_data = {
        "chat_id": str(ObjectId()),
        "participants": [p.dict() for p in request.participants],
        "messages": []
    }

    await chats_collection.insert_one(chat_data)
    return chat_data

# --- Get Chat by Transactional Group ID ---
@router.get("/from-transactional-group/{transactional_group_id}", response_model=ChatResponse)
async def get_chat_from_group(transactional_group_id: str, current_user: User = Depends(get_current_user)):
    chat_doc = await chats_collection.find_one({"transactional_group_id": transactional_group_id})
    if not chat_doc:
        raise HTTPException(status_code=404, detail="Chat not found for this group")
    return chat_doc
