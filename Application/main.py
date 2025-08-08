from fastapi import FastAPI, Depends, HTTPException, Body, Path, status
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import id_token
from fastapi.security import OAuth2PasswordRequestForm
from Application.auth import (
    Token, User, get_current_user, create_access_token,
    authenticate_user, is_token_blacklisted, blacklist_token,
    UserCreate, UserLogin, create_refresh_token, get_user_by_email
)
from Application.db import init_db, users_collection
from Application.auth import get_password_hash
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from Application.config import JWT_SECRET_KEY
from typing import Annotated
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    await init_db()

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm uses 'username', which will now be the email
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/login", response_model=Token)
async def normal_login(user_data: UserLogin):
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/create-user")
async def create_user(user_data: UserCreate):
    hashed_pw = get_password_hash(user_data.password)
    user = {
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "hashed_password": hashed_pw,
        "joined_on": datetime.utcnow()
    }
    existing = await users_collection.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    result = await users_collection.insert_one(user)
    return {"id": str(result.inserted_id), "email": user_data.email, "joined_on": user["joined_on"]}

@app.delete("/users/{email}")
async def delete_user(
    email: Annotated[str, Path(title="The email of the user to delete")],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.email != email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    
    result = await users_collection.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"message": f"User '{email}' deleted successfully."}

@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Body(...)):
    if await is_token_blacklisted(refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = await get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = create_access_token(data={"sub": email})
        new_refresh_token = create_refresh_token(data={"sub": email})
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
@app.post("/logout")
async def logout(refresh_token: str = Body(...)):
    await blacklist_token(refresh_token)
    return {"message": "Logged out and refresh token revoked"}


@app.post("/users/google-login", response_model=Token)
async def google_login(token: str = Body(...)):
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request())
        google_user_id = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo.get("name", "").split(" ")
        first_name = name[0] if len(name) > 0 else ""
        last_name = name[1] if len(name) > 1 else ""

        user = await users_collection.find_one({"email": email})
        if not user:
            new_user = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "hashed_password": "",
                "joined_on": datetime.utcnow()
            }
            await users_collection.insert_one(new_user)

        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")