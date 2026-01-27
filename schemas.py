from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    name: str
    level: str = "B2 Intermediate"
    avatar: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Essay schemas
class EssayBase(BaseModel):
    content: str
    file_url: Optional[str] = None
    ai_style_analysis: Optional[Dict[str, Any]] = None
    ai_evaluation: Optional[Dict[str, Any]] = None
    ai_improvement: Optional[Dict[str, Any]] = None
    ai_refinement: Optional[Dict[str, Any]] = None
    ai_followup: Optional[Dict[str, Any]] = None


class EssayCreate(EssayBase):
    pass


class EssayUpdate(BaseModel):
    content: Optional[str] = None
    ai_style_analysis: Optional[Dict[str, Any]] = None
    ai_evaluation: Optional[Dict[str, Any]] = None
    ai_improvement: Optional[Dict[str, Any]] = None
    ai_refinement: Optional[Dict[str, Any]] = None
    ai_followup: Optional[Dict[str, Any]] = None


class EssayResponse(EssayBase):
    id: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Recommended Article schemas
class RecommendedArticleBase(BaseModel):
    article_id: str
    title: str
    url: str
    source: str
    image_url: Optional[str] = None
    type: str  # 'News' or 'Blog'
    level: Optional[str] = None
    snippet: Optional[str] = None
    published_at: Optional[datetime] = None
    is_pushed_to_client: bool = False
    pushed_at: Optional[datetime] = None


class RecommendedArticleCreate(RecommendedArticleBase):
    pass


class RecommendedArticleUpdate(BaseModel):
    is_pushed_to_client: Optional[bool] = None
    pushed_at: Optional[datetime] = None


class RecommendedArticleResponse(RecommendedArticleBase):
    id: int
    pulled_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Login request/response
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


# Article and Lesson schemas
class ArticleContent(BaseModel):
    id: str
    title: str
    readTime: str
    type: str
    content: List[str]


class QuestionOption(BaseModel):
    id: int
    label: str
    text: str


class Question(BaseModel):
    id: int
    text: str
    options: List[QuestionOption]
    correctId: int
    explanation: str


class GeneratedLesson(BaseModel):
    article: ArticleContent
    questions: List[Question]


# Request for generating reading lesson
class GenerateReadingLessonRequest(BaseModel):
    level: str
    topic: Optional[str] = None

# Essay Search schemas
class EssaySearchRequest(BaseModel):
    query_text: str
    score_level: Optional[int] = None
    top_k: Optional[int] = 2

class EssaySearchResult(BaseModel):
    id: str
    grade: str
    writing_type: str
    score_level: str
    essay_text: str
    score_rationale: Optional[str] = None
    similarity: Optional[float] = None

class EssaySearchResponse(BaseModel):
    results: List[EssaySearchResult]
