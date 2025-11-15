"""
Simple admin authentication for document management
For production, use proper OAuth/JWT
"""

import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv
import secrets

load_dotenv()

security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Verify admin credentials using HTTP Basic Auth

    For production, replace with:
    - OAuth2/JWT tokens
    - Database user management
    - Proper password hashing (bcrypt)
    """
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return True

def get_admin_token(username: str, password: str) -> dict:
    """
    Simple login endpoint
    Returns success if credentials are correct
    """
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return {
            "success": True,
            "username": username,
            "message": "Login successful"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
