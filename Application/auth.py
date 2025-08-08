from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from db import users_collection
from db import token_blacklist_collection
from bson.objectid import ObjectId
from config import PASSWORD_SALT, JWT_SECRET_KEY

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Save refresh token to blacklist
async def blacklist_token(token: str):
    await token_blacklist_collection.insert_one({"token": token})

# Check if a refresh token is blacklisted
async def is_token_blacklisted(token: str) -> bool:
    token_doc = await token_blacklist_collection.find_one({"token": token})
    return token_doc is not None

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    joined_on: datetime | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    joined_on: datetime | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

class TokenData(BaseModel):
    email: EmailStr | None = None

# Utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    salted_password = PASSWORD_SALT + plain_password
    return pwd_context.verify(salted_password, hashed_password)

def get_password_hash(password: str) -> str:
    salted_password = PASSWORD_SALT + password
    return pwd_context.hash(salted_password)

# Updated function to get user by email
async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    if user:
        return UserInDB(
            id=str(user["_id"]),
            email=user["email"],
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            hashed_password=user["hashed_password"],
            joined_on=user.get("joined_on")
        )
    return None

# Updated authentication function
async def authenticate_user(email: str, password: str):
    user = await get_user_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
        user = await get_user_by_email(email)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception