from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Use absolute imports instead of relative imports
import auth, database

load_dotenv()

router = APIRouter()

@router.get("/test-token", response_model=Dict[str, Any])
def test_token(current_user: dict = Depends(auth.get_current_active_user)):
    """
    Test endpoint to verify Bearer token authentication.
    Returns user information if token is valid.
    """
    return {
        "message": "Token is valid",
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "user_metadata": current_user.get("user_metadata", {}),
        "token_issued_at": current_user.get("iat"),
        "token_expires_at": current_user.get("exp"),
        "audience": current_user.get("aud")
    }

@router.get("/token-info", response_model=Dict[str, Any])
def get_token_info():
    """
    Get information about how to obtain and use Bearer tokens.
    """
    return {
        "message": "How to get HTTP Bearer tokens for this API",
        "steps": [
            "1. Sign in to Supabase using your frontend application",
            "2. Get the access token from the Supabase session",
            "3. Use the token in API requests with the Authorization header",
            "4. Format: 'Authorization: Bearer YOUR_ACCESS_TOKEN'"
        ],
        "example_headers": {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "Content-Type": "application/json"
        },
        "protected_endpoints": [
            "/api/ai/chat",
            "/api/ai/generate-reading-lesson", 
            "/api/ai/analyze-writing",
            "/api/ai/full-analyze-writing",
            "/api/users/profile",
            "/api/users/profile (PUT)",
            "/api/essays",
            "/api/essays (POST)",
            "/api/essays/{id}",
            "/api/essays/{id} (PUT)",
            "/api/essays/{id} (DELETE)"
        ],
        "note": "This endpoint does not require authentication"
    }

@router.post("/validate-token", response_model=Dict[str, Any])
def validate_token_endpoint(token_data: Dict[str, str], current_user: dict = Depends(auth.get_current_active_user)):
    """
    Validate a specific token (for testing purposes).
    This endpoint is protected, so if you can access it, your token is valid.
    """
    return {
        "message": "Token validation successful",
        "user_info": {
            "user_id": current_user.get("sub"),
            "email": current_user.get("email"),
            "name": current_user.get("user_metadata", {}).get("name"),
            "level": current_user.get("user_metadata", {}).get("level")
        },
        "token_details": {
            "issued_at": current_user.get("iat"),
            "expires_at": current_user.get("exp"),
            "audience": current_user.get("aud")
        }
    }