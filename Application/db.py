from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
import os

MONGO_DETAILS = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "auth_db")

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client[DB_NAME]


users_collection = db.get_collection("users")
token_blacklist_collection = db.get_collection("token_blacklist")
user_code_collection = db.get_collection("user_code")

# Ensure index for username (optional)
async def init_db():
    # Ensure unique email (case-insensitive)
    await users_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        collation={"locale": "en", "strength": 2}  # Makes it case-insensitive
    )

    # Prevent duplicate verification code entries per email
    await user_code_collection.create_index([("email", ASCENDING)], unique=True)
