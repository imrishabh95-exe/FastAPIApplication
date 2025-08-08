import os
from dotenv import load_dotenv

load_dotenv()

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "XXXXXX123")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "XXXXXX123YYYY")
SECRET_KEY = os.getenv("SECRET_KEY", "121212XXXXXX123YYYY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
