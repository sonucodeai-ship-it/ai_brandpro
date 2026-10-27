"""Configuration for the Google Business Profile review integration."""
import os

GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "").strip()
GOOGLE_FRONTEND_URL = os.getenv("GOOGLE_FRONTEND_URL", "https://aibrandplus.com").strip().rstrip("/")
GOOGLE_TOKEN_ENCRYPTION_KEY = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY", "").strip()

GOOGLE_BUSINESS_SCOPE = "https://www.googleapis.com/auth/business.manage"
GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ACCOUNT_API = "https://mybusinessaccountmanagement.googleapis.com/v1"
GOOGLE_LOCATION_API = "https://mybusinessbusinessinformation.googleapis.com/v1"
GOOGLE_REVIEW_API = "https://mybusiness.googleapis.com/v4"

OAUTH_STATE_MINUTES = int(os.getenv("GOOGLE_OAUTH_STATE_MINUTES", "10"))
GOOGLE_HTTP_TIMEOUT_SECONDS = int(os.getenv("GOOGLE_HTTP_TIMEOUT_SECONDS", "30"))


def validate_oauth_configuration() -> None:
    """Fail closed instead of silently falling back to a localhost callback."""
    required = {
        "GOOGLE_OAUTH_CLIENT_ID": GOOGLE_OAUTH_CLIENT_ID,
        "GOOGLE_OAUTH_CLIENT_SECRET": GOOGLE_OAUTH_CLIENT_SECRET,
        "GOOGLE_OAUTH_REDIRECT_URI": GOOGLE_OAUTH_REDIRECT_URI,
        "GOOGLE_FRONTEND_URL": GOOGLE_FRONTEND_URL,
        "GOOGLE_TOKEN_ENCRYPTION_KEY": GOOGLE_TOKEN_ENCRYPTION_KEY,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Google Business Profile integration is not configured. Missing: "
            + ", ".join(missing)
        )
    if not GOOGLE_OAUTH_REDIRECT_URI.startswith("https://") and not (
        os.getenv("APP_ENV", "production").lower() != "production"
        and GOOGLE_OAUTH_REDIRECT_URI.startswith("http://127.0.0.1:")
    ):
        raise RuntimeError("Production GOOGLE_OAUTH_REDIRECT_URI must use HTTPS.")
