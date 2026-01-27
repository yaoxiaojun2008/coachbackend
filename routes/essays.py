from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid
from datetime import datetime
import json

# Use absolute imports instead of relative imports
import models, schemas, auth, database

router = APIRouter()

async def get_current_user_data():
    # This would be populated by the auth dependency
    # For now, we'll rely on the get_current_active_user function
    pass

@router.get("/", response_model=List[schemas.EssayResponse])
async def get_user_essays(
    current_user: dict = Depends(auth.get_current_active_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Get all essays for the current user
    """
    supabase = database.get_supabase_client()
    try:
        response = supabase.table('essays').select('*').eq('user_id', current_user['id']).order('created_at', desc=True).range(skip, skip + limit - 1).execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching essays: {str(e)}"
        )


@router.post("/", response_model=schemas.EssayResponse)
async def create_essay(
    essay: schemas.EssayCreate,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Create a new essay for the current user
    """
    essay_id = str(uuid.uuid4())
    
    supabase = database.get_supabase_client()
    try:
        essay_data = {
            "id": essay_id,
            "user_id": current_user['id'],
            "content": essay.content,
            "file_url": essay.file_url,
            "ai_style_analysis": essay.ai_style_analysis,
            "ai_evaluation": essay.ai_evaluation,
            "ai_improvement": essay.ai_improvement,
            "ai_refinement": essay.ai_refinement,
            "ai_followup": essay.ai_followup,
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table('essays').insert(essay_data).execute()
        return response.data[0] if response.data else essay_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating essay: {str(e)}"
        )


@router.get("/{essay_id}", response_model=schemas.EssayResponse)
async def get_essay(
    essay_id: str,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Get a specific essay by ID
    """
    supabase = database.get_supabase_client()
    try:
        response = supabase.table('essays').select('*').eq('id', essay_id).eq('user_id', current_user['id']).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Essay not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching essay: {str(e)}"
        )


@router.put("/{essay_id}", response_model=schemas.EssayResponse)
async def update_essay(
    essay_id: str,
    essay_update: schemas.EssayUpdate,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Update a specific essay
    """
    supabase = database.get_supabase_client()
    try:
        # Prepare update data (only include fields that are set)
        update_data = {}
        if essay_update.content is not None:
            update_data["content"] = essay_update.content
        if essay_update.ai_style_analysis is not None:
            update_data["ai_style_analysis"] = essay_update.ai_style_analysis
        if essay_update.ai_evaluation is not None:
            update_data["ai_evaluation"] = essay_update.ai_evaluation
        if essay_update.ai_improvement is not None:
            update_data["ai_improvement"] = essay_update.ai_improvement
        if essay_update.ai_refinement is not None:
            update_data["ai_refinement"] = essay_update.ai_refinement
        if essay_update.ai_followup is not None:
            update_data["ai_followup"] = essay_update.ai_followup
        
        response = supabase.table('essays').update(update_data).eq('id', essay_id).eq('user_id', current_user['id']).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Essay not found"
            )
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating essay: {str(e)}"
        )


@router.delete("/{essay_id}")
async def delete_essay(
    essay_id: str,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Delete a specific essay
    """
    supabase = database.get_supabase_client()
    try:
        response = supabase.table('essays').delete().eq('id', essay_id).eq('user_id', current_user['id']).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Essay not found"
            )
        
        return {"message": "Essay deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting essay: {str(e)}"
        )


# Recommended Articles Routes
@router.get("/recommended/news", response_model=List[schemas.RecommendedArticleResponse])
async def get_recommended_news(
    skip: int = 0,
    limit: int = 3
):
    """
    Get recommended news articles that have been pushed to clients
    """
    supabase = database.get_supabase_client()
    try:
        response = (supabase.table('recommended_articles')
                    .select('*')
                    .eq('type', 'News')
                    .eq('is_pushed_to_client', True)
                    .order('pulled_at', desc=True)
                    .range(skip, skip + limit - 1)
                    .execute())
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recommended news: {str(e)}"
        )


@router.get("/recommended/blogs", response_model=List[schemas.RecommendedArticleResponse])
async def get_recommended_blogs(
    skip: int = 0,
    limit: int = 3
):
    """
    Get recommended blog articles that have been pushed to clients
    """
    supabase = database.get_supabase_client()
    try:
        response = (supabase.table('recommended_articles')
                    .select('*')
                    .eq('type', 'Blog')
                    .eq('is_pushed_to_client', True)
                    .order('pulled_at', desc=True)
                    .range(skip, skip + limit - 1)
                    .execute())
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recommended blogs: {str(e)}"
        )


@router.get("/recommended/all", response_model=dict)
async def get_all_recommended():
    """
    Get all recommended articles (both news and blogs) that have been pushed to clients
    """
    supabase = database.get_supabase_client()
    try:
        news_response = (supabase.table('recommended_articles')
                         .select('*')
                         .eq('type', 'News')
                         .eq('is_pushed_to_client', True)
                         .order('pulled_at', desc=True)
                         .limit(3)
                         .execute())
        
        blog_response = (supabase.table('recommended_articles')
                         .select('*')
                         .eq('type', 'Blog')
                         .eq('is_pushed_to_client', True)
                         .order('pulled_at', desc=True)
                         .limit(3)
                         .execute())
        
        return {
            "news": news_response.data,
            "blogs": blog_response.data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recommended articles: {str(e)}"
        )