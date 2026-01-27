from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import uuid
import os
from dotenv import load_dotenv

# Use absolute imports instead of relative imports
import models, schemas, auth, database

load_dotenv()

router = APIRouter()

@router.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user: dict = Depends(auth.get_current_active_user)):
    # Return user data from the verified token
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["user_metadata"].get("name", current_user["email"].split('@')[0] if current_user["email"] else ""),
        "level": current_user["user_metadata"].get("level", "B2 Intermediate"),
        "avatar": current_user["user_metadata"].get("avatar", None),
        "is_active": True,  # Assuming active if authenticated
        "created_at": current_user.get("created_at", "2023-01-01T00:00:00Z")  # Fallback date
    }

@router.put("/profile", response_model=schemas.UserResponse)
def update_profile(
    user_update: schemas.UserUpdate,
    current_user: dict = Depends(auth.get_current_active_user)
):
    supabase = database.get_supabase_client()
    
    try:
        # Prepare update data (only include fields that are set)
        update_data = {}
        if user_update.name is not None:
            update_data["name"] = user_update.name
        if user_update.level is not None:
            update_data["level"] = user_update.level
        if user_update.avatar is not None:
            update_data["avatar"] = user_update.avatar

        # Update user metadata in Supabase Auth
        # This requires a service role key, which is not ideal for security
        # For a more secure approach, we might want to update user data in a separate table
        # rather than in the auth system itself
        
        # In a real implementation, we would likely store extended user data 
        # in a separate table rather than in auth metadata
        user_id = current_user["id"]
        
        # Update the user's extended data in the users table (not auth metadata)
        # First, try to get existing user data
        user_response = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if user_response.data:
            # Update existing user
            updated_user = supabase.table('users').update(update_data).eq('id', user_id).execute()
            user_data = updated_user.data[0]
        else:
            # Create user record if it doesn't exist
            user_data = {
                "id": user_id,
                "email": current_user["email"],
                **update_data
            }
            created_user = supabase.table('users').insert(user_data).execute()
            user_data = created_user.data[0] if created_user.data else user_data

        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )