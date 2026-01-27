import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from routes import essays
from auth import get_current_active_user
import schemas
import uuid
from datetime import datetime


@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "id": "12345",
        "email": "test@example.com",
        "user_metadata": {},
        "app_metadata": {},
        "role": "authenticated",
        "created_at": datetime.now()
    }


@pytest.fixture
def mock_essay_data():
    """Mock essay data"""
    return {
        "id": str(uuid.uuid4()),
        "user_id": "12345",
        "content": "This is a sample essay content.",
        "file_url": "https://example.com/file.pdf",
        "ai_style_analysis": {"style": "formal", "tone": "academic"},
        "ai_evaluation": {"score": 85},
        "ai_improvement": {"suggestions": ["improve introduction", "add examples"]},
        "ai_refinement": {"refined_text": "Refined version of the essay."},
        "ai_followup": {"questions": ["What could be improved?", "How to make it more concise?"]},
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_article_data():
    """Mock article data"""
    return [
        {
            "id": 1,
            "article_id": "article-1",
            "title": "Sample News Article",
            "url": "https://example.com/article1",
            "source": "Test News",
            "type": "News",
            "is_pushed_to_client": True,
            "pulled_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "id": 2,
            "article_id": "article-2",
            "title": "Sample Blog Post",
            "url": "https://example.com/article2",
            "source": "Test Blog",
            "type": "Blog",
            "is_pushed_to_client": True,
            "pulled_at": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]


def test_get_user_essays_success(mock_user, mock_essay_data):
    """Test successful retrieval of user essays"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [mock_essay_data]
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_response

        result = essays.get_user_essays(current_user=mock_user, skip=0, limit=100)

        assert result == [mock_essay_data]
        mock_supabase.assert_called_once()
        mock_supabase.return_value.table.assert_called_with('essays')


def test_get_user_essays_error():
    """Test error handling in get_user_essays"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an exception being raised
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            essays.get_user_essays(current_user={"id": "12345"}, skip=0, limit=100)

        assert exc_info.value.status_code == 500


def test_create_essay_success(mock_user, mock_essay_data):
    """Test successful creation of an essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        with patch('routes.essays.uuid.uuid4', return_value=uuid.UUID(mock_essay_data["id"])):
            with patch('routes.essays.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = datetime(2023, 1, 1)

                # Prepare the input schema
                essay_create = schemas.EssayCreate(
                    content=mock_essay_data["content"],
                    file_url=mock_essay_data["file_url"],
                    ai_style_analysis=mock_essay_data["ai_style_analysis"],
                    ai_evaluation=mock_essay_data["ai_evaluation"],
                    ai_improvement=mock_essay_data["ai_improvement"],
                    ai_refinement=mock_essay_data["ai_refinement"],
                    ai_followup=mock_essay_data["ai_followup"]
                )

                # Mock the response
                mock_response = MagicMock()
                mock_response.data = [mock_essay_data]
                mock_supabase.return_value.table.return_value.insert.return_value.execute.return_value = mock_response

                result = essays.create_essay(essay=essay_create, current_user=mock_user)

                # Check that the insert was called with correct data
                expected_data = {
                    "id": mock_essay_data["id"],
                    "user_id": mock_user["id"],
                    "content": mock_essay_data["content"],
                    "file_url": mock_essay_data["file_url"],
                    "ai_style_analysis": mock_essay_data["ai_style_analysis"],
                    "ai_evaluation": mock_essay_data["ai_evaluation"],
                    "ai_improvement": mock_essay_data["ai_improvement"],
                    "ai_refinement": mock_essay_data["ai_refinement"],
                    "ai_followup": mock_essay_data["ai_followup"],
                    "created_at": "2023-01-01T00:00:00"
                }

                mock_supabase.return_value.table.return_value.insert.assert_called_once_with(expected_data)
                assert result == mock_essay_data


def test_create_essay_error(mock_user):
    """Test error handling in create_essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an exception being raised
        mock_supabase.return_value.table.return_value.insert.return_value.execute.side_effect = Exception("Database error")

        essay_create = schemas.EssayCreate(
            content="test content",
            file_url=None
        )

        with pytest.raises(HTTPException) as exc_info:
            essays.create_essay(essay=essay_create, current_user=mock_user)

        assert exc_info.value.status_code == 500


def test_get_essay_success(mock_user, mock_essay_data):
    """Test successful retrieval of a specific essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [mock_essay_data]
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        result = essays.get_essay(essay_id=mock_essay_data["id"], current_user=mock_user)

        assert result == mock_essay_data
        mock_supabase.return_value.table.assert_called_with('essays')


def test_get_essay_not_found(mock_user):
    """Test handling when essay is not found"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an empty response
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            essays.get_essay(essay_id="non-existent-id", current_user=mock_user)

        assert exc_info.value.status_code == 404


def test_get_essay_error(mock_user):
    """Test error handling in get_essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an exception being raised
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            essays.get_essay(essay_id="some-id", current_user=mock_user)

        assert exc_info.value.status_code == 500


def test_update_essay_success(mock_user, mock_essay_data):
    """Test successful update of an essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [mock_essay_data]
        mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        # Create an update schema instance
        essay_update = schemas.EssayUpdate(
            content="Updated content",
            ai_style_analysis={"style": "casual", "tone": "informal"}
        )

        result = essays.update_essay(essay_id=mock_essay_data["id"], essay_update=essay_update, current_user=mock_user)

        # Check that update was called with correct parameters
        expected_update_data = {
            "content": "Updated content",
            "ai_style_analysis": {"style": "casual", "tone": "informal"}
        }
        mock_supabase.return_value.table.return_value.update.assert_called_once_with(expected_update_data)
        mock_supabase.return_value.table.return_value.update.return_value.eq.assert_called_once_with('id', mock_essay_data["id"])
        assert result == mock_essay_data


def test_update_essay_partial_update(mock_user, mock_essay_data):
    """Test partial update of an essay (only some fields)"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [mock_essay_data]
        mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        # Create an update schema with only content field
        essay_update = schemas.EssayUpdate(content="Only content updated")

        result = essays.update_essay(essay_id=mock_essay_data["id"], essay_update=essay_update, current_user=mock_user)

        # Check that update was called with only the content field
        expected_update_data = {"content": "Only content updated"}
        mock_supabase.return_value.table.return_value.update.assert_called_once_with(expected_update_data)
        assert result == mock_essay_data


def test_update_essay_not_found(mock_user):
    """Test handling when essay to update is not found"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an empty response
        mock_response = MagicMock()
        mock_response.data = []
        mock_supabase.return_value.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        essay_update = schemas.EssayUpdate(content="Updated content")

        with pytest.raises(HTTPException) as exc_info:
            essays.update_essay(essay_id="non-existent-id", essay_update=essay_update, current_user=mock_user)

        assert exc_info.value.status_code == 404


def test_delete_essay_success(mock_user):
    """Test successful deletion of an essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [{"id": "some-id"}]  # Non-empty response means deletion successful
        mock_supabase.return_value.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        result = essays.delete_essay(essay_id="some-id", current_user=mock_user)

        # Check that delete was called with correct parameters
        mock_supabase.return_value.table.return_value.delete.assert_called_once()
        assert result == {"message": "Essay deleted successfully"}


def test_delete_essay_not_found(mock_user):
    """Test handling when essay to delete is not found"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an empty response
        mock_response = MagicMock()
        mock_response.data = []  # Empty response means no rows were deleted
        mock_supabase.return_value.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response

        with pytest.raises(HTTPException) as exc_info:
            essays.delete_essay(essay_id="non-existent-id", current_user=mock_user)

        assert exc_info.value.status_code == 404


def test_delete_essay_error(mock_user):
    """Test error handling in delete_essay"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Mock an exception being raised
        mock_supabase.return_value.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            essays.delete_essay(essay_id="some-id", current_user=mock_user)

        assert exc_info.value.status_code == 500


def test_get_recommended_news_success(mock_article_data):
    """Test successful retrieval of recommended news"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Filter only news articles
        news_articles = [article for article in mock_article_data if article["type"] == "News"]
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = news_articles
        mock_execute = mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value.execute
        mock_execute.return_value = mock_response

        result = essays.get_recommended_news(skip=0, limit=3)

        # Check that the table method was called with 'recommended_articles'
        mock_supabase.return_value.table.assert_called_with('recommended_articles')
        # Check that eq was called twice (once for type='News', once for is_pushed_to_client=True)
        assert mock_supabase.return_value.table.return_value.select.return_value.eq.call_count == 2
        assert result == news_articles


def test_get_recommended_blogs_success(mock_article_data):
    """Test successful retrieval of recommended blogs"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Filter only blog articles
        blog_articles = [article for article in mock_article_data if article["type"] == "Blog"]
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.data = blog_articles
        mock_execute = mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.range.return_value.execute
        mock_execute.return_value = mock_response

        result = essays.get_recommended_blogs(skip=0, limit=3)

        # Check that the table method was called with 'recommended_articles'
        mock_supabase.return_value.table.assert_called_with('recommended_articles')
        # Check that eq was called twice (once for type='Blog', once for is_pushed_to_client=True)
        assert mock_supabase.return_value.table.return_value.select.return_value.eq.call_count == 2
        assert result == blog_articles


def test_get_all_recommended_success(mock_article_data):
    """Test successful retrieval of all recommended articles"""
    with patch('routes.essays.database.get_supabase_client') as mock_supabase:
        # Separate news and blog articles
        news_articles = [article for article in mock_article_data if article["type"] == "News"]
        blog_articles = [article for article in mock_article_data if article["type"] == "Blog"]
        
        # Mock the response for both calls
        mock_news_response = MagicMock()
        mock_news_response.data = news_articles
        mock_blog_response = MagicMock()
        mock_blog_response.data = blog_articles
        
        # Configure side_effect to return different values for the two calls
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = [
            mock_news_response,
            mock_blog_response
        ]

        result = essays.get_all_recommended()

        # Check that the result contains both news and blogs
        assert "news" in result
        assert "blogs" in result
        assert result["news"] == news_articles
        assert result["blogs"] == blog_articles


if __name__ == "__main__":
    pytest.main()