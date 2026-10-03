import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.app.config import get_settings
from backend.app.logging_config import get_logger

logger = get_logger("api.auth")
router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class LoginIn(BaseModel):
    username: str
    password: str


def create_token(username: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": username, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def require_auth(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    """Dependency for protected endpoints. Returns the username or raises 401."""
    if creds is None:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(creds.credentials, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


@router.post("/login")
def login(body: LoginIn):
    settings = get_settings()
    # compare_digest avoids timing attacks when comparing secrets.
    user_ok = hmac.compare_digest(body.username, settings.admin_username)
    pass_ok = hmac.compare_digest(body.password, settings.admin_password)
    if not (user_ok and pass_ok):
        logger.warning("Failed login attempt for user %s", body.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    logger.info("User %s logged in", body.username)
    return {"access_token": create_token(body.username), "token_type": "bearer"}