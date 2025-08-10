import os
from dotenv import load_dotenv

load_dotenv()

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "XXXXXX123")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "XXXXXX123YYYY")
SECRET_KEY = os.getenv("SECRET_KEY", "121212XXXXXX123YYYY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# EMAIL CONFIGURATION
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
