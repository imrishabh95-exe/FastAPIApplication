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
dashboards_collection = db.get_collection("dashboards")
chats_collection = db.get_collection("chats")
transactional_groups_collection = db.get_collection("transactional_groups")

async def init_db():
    # 🔹 Remove old username index if it exists
    indexes = await users_collection.index_information()
    if "username_1" in indexes:
        print("[DB INIT] Removing old 'username_1' index to avoid duplicate key errors.")
        await users_collection.drop_index("username_1")

    # 🔹 Ensure unique email (case-insensitive)
    await users_collection.create_index(
        [("email", ASCENDING)],
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    # 🔹 Prevent duplicate verification code entries per email
    await user_code_collection.create_index([("email", ASCENDING)], unique=True)
    await dashboards_collection.create_index([("owner_id", ASCENDING)])
