import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from typing import Dict, Any
import time
import json
import re
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use absolute imports for local modules
import schemas
from schemas import GenerateReadingLessonRequest, EssaySearchRequest, EssaySearchResponse, EssaySearchResult, EvaluateReadingLessonRequest
import auth, database

# Add Snowflake search service
import snowflake.connector
import json
import os
import logging
from dotenv import load_dotenv

# Add Snowpark imports for the new session-based search
try:
    from snowflake.core import Root
    from snowflake.snowpark import Session
    SNOWPARK_AVAILABLE = True
except ImportError:
    SNOWPARK_AVAILABLE = False
    print("Snowpark not available. Install with: pip install snowflake-snowpark-python")

class EssaySearchService:
    # Constants
    ESSAY_PREVIEW_LENGTH = 200
    DEFAULT_TOP_K = 2
    
    def __init__(self):
        load_dotenv()
        self.connection_params = {
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"), 
            "role": os.getenv("SNOWFLAKE_ROLE"),    
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA")
        }
        self.search_service_name = "ESSAY_SEARCH_SERVICE"
        self._validate_env()

    def _validate_env(self):
        missing = [k for k, v in self.connection_params.items() if not v]
        if missing:
            raise ValueError(f"Missing environment variables: {missing}")

    def get_connection(self):
        try:
            return snowflake.connector.connect(
                **self.connection_params,
                login_timeout=30,
                network_timeout=60
            )
        except Exception:
            logging.exception("Failed to create Snowflake connection")
            raise

    def _validate_json_response(self, data):
        try:
            if isinstance(data, str):
                return json.loads(data)
            return data
        except Exception:
            logging.exception("Invalid JSON returned from Cortex")
            return None

    def _format_essay_result(self, item):
        essay_text = str(item.get("ESSAY_TEXT", "") or item.get("essay_text", ""))

        similarity = item.get("score")
        if similarity is not None:
            similarity = round(float(similarity), 4)

        return EssaySearchResult(
            id=item.get("ID") or item.get("id"),
            grade=item.get("GRADE") or item.get("grade"),
            writing_type=item.get("WRITING_TYPE") or item.get("writing_type"),
            score_level=item.get("SCORE_LEVEL") or item.get("score_level"),
            essay_text=essay_text,
            score_rationale=item.get("SCORE_RATIONALE") or item.get("score_rationale"),
            similarity=similarity
        )

    def search_similar_essays_snowpark(self, query_text, score_level=3, top_k=None):
        """Search for similar essays using the modern Snowpark API"""
        if not SNOWPARK_AVAILABLE:
            logging.warning("Snowpark not available, falling back to SQL approach")
            return []

        if top_k is None:
            top_k = self.DEFAULT_TOP_K

        try:
            # Create Snowpark session
            session = Session.builder.configs(self.connection_params).create()
            root = Root(session)

            # Get the search service
            search_service = (root
                .databases["EDUCATION"]
                .schemas["PUBLIC"]
                .cortex_search_services["ESSAY_SEARCH_SERVICE"]
            )

            # Query the service
            resp = search_service.search(
                query=query_text,
                columns=["ESSAY_TEXT", "GRADE", "WRITING_TYPE", "SCORE_LEVEL", "SCORE_RATIONALE", "ID"],
                limit=top_k * 2 if score_level else top_k,
            )

            # Convert response to JSON
            search_results = json.loads(resp.to_json())
            
            results = []
            
            if 'results' in search_results and search_results['results']:
                for item in search_results['results']:
                    # Apply score_level filter if specified
                    if score_level is not None:
                        item_score = item.get('SCORE_LEVEL')
                        if item_score is not None:
                            try:
                                # Convert string to int for comparison
                                item_score_int = int(item_score)
                                if item_score_int < score_level:
                                    continue
                            except (ValueError, TypeError):
                                # Skip items where score_level can't be converted to int
                                continue
                        
                    results.append(self._format_essay_result(item))
                    
                    # Limit results if score_level filter was applied
                    if len(results) >= top_k:
                        break
            
            logging.info(f"Snowpark search returned {len(results)} results")
            return results
            
        except Exception as e:
            logging.error(f"Snowpark search failed: {str(e)}")
            return []

    def get_search_service_status(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW CORTEX SEARCH SERVICES")
                services = cur.fetchall()
                print("\nCortex Search Services:")
                for s in services:
                    print(" -", s[1])
        except Exception:
            logging.exception("Status check failed")
        finally:
            conn.close()

router = APIRouter()

# Configure DeepSeek client
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Updated to correct DeepSeek endpoint

if not DEEPSEEK_API_KEY:
    logger.warning("[DEBUG] DEEPSEEK_API_KEY is not set in environment variables")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

def call_deepseek_api(prompt: str, temperature: float = 0.7):
    """
    Utility function to call DeepSeek API and return the response content
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        
        text_response = response.choices[0].message.content.strip()
        return text_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling DeepSeek API: {str(e)}"
        )

def extract_json_from_response(text_response: str):
    """
    Utility function to extract JSON from API response
    """
    # Extract JSON from response if it's formatted as a code block
    json_match = re.search(r'```json\n(.*?)\n```', text_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # If no code block, try to extract JSON directly
        start_idx = text_response.find('{')
        end_idx = text_response.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = text_response[start_idx:end_idx]
        else:
            raise ValueError("Could not extract JSON from response")
    
    return json.loads(json_str)

@router.post("/chat")
async def chat_with_ai(data: Dict[str, Any], current_user: dict = Depends(auth.get_current_active_user)):
    logger.info(f"[DEBUG] Chat API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Request data keys: {list(data.keys())}")
    
    try:
        history = data.get("history", [])
        if not history:
            logger.warning("[DEBUG] No chat history provided in request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chat history is required"
            )
        
        logger.info(f"[DEBUG] History length: {len(history)} messages")
        
        # Define the system message for the AI tutor
        system_message = {
            "role": "system",
            "content": "You are a helpful AI Living Tutor for students. You can ONLY discuss topics related to elementary, middle, and high school education (subjects, study tips, homework help, school life). If the user asks about anything else, politely decline and steer the conversation back to education."
        }
        
        # Prepare the messages for the API call
        messages = [system_message] + history
        
        logger.info(f"[DEBUG] Total messages to send to AI: {len(messages)}")
        if len(messages) > 1:
            last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
            logger.info(f"[DEBUG] Last user message: {last_user_message[:100]}{'...' if len(last_user_message) > 100 else ''}")
        
        try:
            logger.info("[DEBUG] Initiating LLM call to DeepSeek API...")
            logger.info(f"[DEBUG] Using model: deepseek-chat, Temperature: 0.7")
            logger.info(f"[DEBUG] Sending {len(messages)} messages to LLM")
            if len(messages) > 1:
                last_user_message = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
                logger.info(f"[DEBUG] Last user message content preview: {last_user_message[:100]}{'...' if len(last_user_message) > 100 else ''}")

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"[DEBUG] LLM call successful. Received response of length: {len(ai_response)}")
            logger.info(f"[DEBUG] AI response preview: {ai_response[:100]}{'...' if len(ai_response) > 100 else ''}")
            
            return {"response": ai_response}
        except Exception as e:
            logger.error(f"[DEBUG] Failed to communicate with LLM. Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error communicating with AI: {str(e)}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat: {str(e)}"
        )


@router.post("/generate-reading-lesson")
async def generate_reading_lesson(
    request: schemas.GenerateReadingLessonRequest,
    current_user: dict = Depends(auth.get_current_active_user)
):
    logger.info(f"[DEBUG] Generate Reading Lesson API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Request level: {request.level}, requested topic: {request.topic}")
    
    try:
        # Define topics for the reading lesson
        topics = [
            "The Future of Artificial Intelligence",
            "Sustainable Living and Minimalist Lifestyles",
            "The History of Coffee Culture",
            "Space Exploration: Mars and Beyond",
            "The Psychology of Happiness",
            "Remote Work: Benefits and Challenges",
            "The Impact of Social Media on Communication",
            "Underwater Ecosystems and Coral Reefs",
            "Traditional vs Modern Education Systems",
            "The Rise of Electric Vehicles"
        ]

        # Select topic based on request or random selection
        selected_topic = request.topic or topics[int.from_bytes(os.urandom(4), byteorder='little') % len(topics)]
        logger.info(f"[DEBUG] Selected topic: {selected_topic}")

        # Create a prompt for generating a reading lesson
        prompt = f"""
        Create a reading comprehension lesson for English learners at {request.level} level.
        Focus on the topic: {selected_topic}.
        
        The response should be in JSON format with this exact structure:
        {{
          "article": {{
            "id": "unique_id",
            "title": "Title of the article",
            "readTime": "Approximate read time (e.g. \"5 min\")",
            "type": "Type of article (e.g. \"News\", \"Blog\", \"Educational\")",
            "content": [
              "Paragraph 1 of the article...",
              "Paragraph 2 of the article...",
              "Continue with more paragraphs as needed..."
            ]
          }},
          "questions": [
            {{
              "id": 1,
              "text": "Question 1 text?",
              "options": [
                {{"id": 1, "label": "A", "text": "Option A"}},
                {{"id": 2, "label": "B", "text": "Option B"}},
                {{"id": 3, "label": "C", "text": "Option C"}},
                {{"id": 4, "label": "D", "text": "Option D"}}
              ],
              "correctId": 1,
              "explanation": "Explanation of why option X is correct"
            }}
          ]
        }}
        
        Please make sure the article is engaging and informative, appropriate for the specified level,
        and the questions effectively test reading comprehension.
        """

        # Generate content using DeepSeek
        logger.info("[DEBUG] Initiating LLM call to generate reading lesson...")
        logger.info(f"[DEBUG] Target level: {request.level}, Topic: {selected_topic}")
        logger.info(f"[DEBUG] Generated prompt length: {len(prompt)} characters")
        
        text_response = call_deepseek_api(prompt, temperature=0.7)
        
        logger.info(f"[DEBUG] LLM call completed. Raw AI response length: {len(text_response)}")
        logger.info(f"[DEBUG] Raw AI response preview: {text_response[:200]}{'...' if len(text_response) > 200 else ''}")
        
        lesson_data = extract_json_from_response(text_response)
        logger.info(f"[DEBUG] Successfully extracted lesson data - Article title: {lesson_data.get('article', {}).get('title', 'Unknown')}")
        
        return lesson_data
        
    except json.JSONDecodeError as e:
        logger.error(f"[DEBUG] JSON decode error: {str(e)}")
        logger.error(f"[DEBUG] Raw response causing error: {text_response}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing AI response: Invalid JSON format"
        )
    except Exception as e:
        logger.error(f"[DEBUG] Error generating reading lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating reading lesson: {str(e)}"
        )


@router.post("/analyze-writing")
async def analyze_writing(
    data: Dict[str, Any],
    current_user: dict = Depends(auth.get_current_active_user)
):
    logger.info(f"[DEBUG] Analyze Writing API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Request data keys: {list(data.keys())}")
    
    try:
        content = data.get("content", "")
        if not content:
            logger.warning("[DEBUG] No content provided for writing analysis")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is required for analysis"
            )
        
        logger.info(f"[DEBUG] Writing content length: {len(content)} characters")
        logger.info(f"[DEBUG] Writing content preview: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        prompt = f"""
        Analyze this piece of writing for English learners. Focus on style, structure, and clarity.
        
        Writing sample:
        {content}
        
        Provide your feedback in the following format:
        {{
          "style": {{
            "strengths": ["List of style strengths"],
            "areas_for_improvement": ["List of areas to improve"],
            "suggestions": ["Specific suggestions"]
          }}
        }}
        """
        
        logger.info("[DEBUG] Initiating LLM call for writing analysis...")
        logger.info(f"[DEBUG] Writing sample length: {len(content)} characters")
        logger.info(f"[DEBUG] Analysis prompt length: {len(prompt)} characters")
        
        text_response = call_deepseek_api(prompt, temperature=0.5)
        
        logger.info(f"[DEBUG] LLM call completed. Raw AI response length: {len(text_response)}")
        logger.info(f"[DEBUG] Raw AI response preview: {text_response[:200]}{'...' if len(text_response) > 200 else ''}")
        
        analysis_data = extract_json_from_response(text_response)
        logger.info("[DEBUG] Successfully extracted writing analysis data")
        
        return analysis_data
        
    except json.JSONDecodeError as e:
        logger.error(f"[DEBUG] JSON decode error in writing analysis: {str(e)}")
        logger.error(f"[DEBUG] Raw response causing error: {text_response}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing AI response: Invalid JSON format"
        )
    except Exception as e:
        logger.error(f"[DEBUG] Error analyzing writing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing writing: {str(e)}"
        )


@router.post("/full-analyze-writing")
async def full_analyze_writing(
    data: Dict[str, Any],
    current_user: dict = Depends(auth.get_current_active_user)
):
    logger.info(f"[DEBUG] Full Analyze Writing API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Request data keys: {list(data.keys())}")
    
    try:
        writing_sample = data.get("writing_sample", "")
        if not writing_sample:
            logger.warning("[DEBUG] No writing sample provided for full analysis")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Writing sample is required for analysis"
            )
        
        logger.info(f"[DEBUG] Full writing analysis requested")
        logger.info(f"[DEBUG] Writing sample length: {len(writing_sample)} characters")
        logger.info(f"[DEBUG] Writing sample preview: {writing_sample[:100]}{'...' if len(writing_sample) > 100 else ''}")
        
        prompt = f"""
        Perform a comprehensive analysis of this writing sample for English learners.
        Focus on (style, structure, clarity), evaluate grammar, vocabulary usage, coherence, and overall effectiveness.
        
        Writing sample:
        {writing_sample}
        
        Provide your analysis in the following format:
        {{
          "style": {{
            "strengths": ["List of style strengths"],
            "areas_for_improvement": ["List of areas to improve"],
            "suggestions": ["Specific suggestions"]
          }},
          "evaluate": {{
            "overall_score": "Score from 1-10",
            "grammar_accuracy": "Comment on grammar accuracy",
            "vocabulary_usage": "Comment on vocabulary usage",
            "coherence_cohesion": "Comment on how well ideas flow together",
            "task_completion": "How well the writing addresses the intended purpose"
          }},
          "improvement": {{
            "key_issues": ["Main issues identified"],
            "priority_fixes": ["Top fixes to make first"]
          }},
          "refiner": {{
            "word_choices": ["Suggestions for better word choices"],
            "sentence_structures": ["Suggestions for sentence improvements"],
            "transitions": ["Suggestions for better transitions between ideas"]
          }},
          "followup": {{
            "learning_resources": ["Resources for improvement"],
            "practice_recommendations": ["Practice exercises recommended"]
          }}
        }}
        """
        
        text_response = call_deepseek_api(prompt, temperature=0.5)
        analysis_data = extract_json_from_response(text_response)
        
        return analysis_data
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing AI response: Invalid JSON format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing full writing analysis: {str(e)}"
        )


# Initialize the essay search service
essay_search_service = EssaySearchService()

@router.post("/sample", response_model=EssaySearchResponse)
async def search_similar_essays(
    request: EssaySearchRequest,
    current_user: dict = Depends(auth.get_current_active_user)
):
    """
    Search for similar essays in Snowflake database.
    Frontend can call this API with text to find similar essays.
    """
    logger.info(f"[DEBUG] Essay search API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Search query: {request.query_text[:100]}{'...' if len(request.query_text) > 100 else ''}")
    logger.info(f"[DEBUG] Score level filter: {request.score_level}, Top K: {request.top_k}")
    
    try:
        # Validate input
        if not request.query_text or len(request.query_text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query text is required"
            )
        
        # Perform the search using Snowflake
        results = essay_search_service.search_similar_essays_snowpark(
            query_text=request.query_text,
            score_level=request.score_level,
            top_k=request.top_k
        )
        
        logger.info(f"[DEBUG] Essay search completed. Found {len(results)} results")
        
        return EssaySearchResponse(results=results)
        
    except Exception as e:
        logger.error(f"[DEBUG] Error in essay search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching essays: {str(e)}"
        )


@router.post("/evaluate-reading-lesson")
async def evaluate_reading_lesson(
    request: EvaluateReadingLessonRequest,
    current_user: dict = Depends(auth.get_current_active_user)
):
    logger.info(f"[DEBUG] Evaluate Reading Lesson API called by user: {current_user.get('email', current_user.get('id', 'unknown'))}")
    logger.info(f"[DEBUG] Request level: {request.level}")
    
    try:
        # Construct the prompt with the article, questions, and user answers
        article_content = "\n".join(request.article.content)
        user_answers_formatted = ""
        
        for i, answer in enumerate(request.user_answers):
            question_id = answer.get("question_id")
            selected_answer_id = answer.get("selected_answer_id")
            
            # Find the corresponding question and selected option
            question = next((q for q in request.questions if q.id == question_id), None)
            selected_option = None
            if question:
                selected_option = next((opt for opt in question.options if opt.id == selected_answer_id), None)
            
            if question and selected_option:
                user_answers_formatted += f"Q{i+1}: {question.text}\n"
                user_answers_formatted += f"User Answer: {selected_option.label}. {selected_option.text}\n"
                user_answers_formatted += f"Correct Answer: {next(opt.text for opt in question.options if opt.id == question.correctId).strip()}\n\n"
        
        # Create a prompt for evaluating the reading lesson
        prompt = f"""
        Using the article and the learner's answers, act as an English reading coach and provide detailed, actionable suggestions to help improve the learner's reading comprehension, vocabulary development, and overall reading skills.
        
        Article Title: {request.article.title}
        Article Content: {article_content}
        
        Learner Level: {request.level}
        
        Learner's Answers:
        {user_answers_formatted}
        
        Please provide:
        1. An assessment of the learner's performance
        2. Detailed feedback on each answer
        3. Suggestions for improving reading comprehension
        4. Vocabulary development recommendations based on the article
        5. Overall reading skill improvement strategies
        """
        
        logger.info("[DEBUG] Initiating LLM call to evaluate reading lesson...")
        logger.info(f"[DEBUG] Prompt length: {len(prompt)} characters")
        
        # Call DeepSeek API with the constructed prompt
        text_response = call_deepseek_api(prompt, temperature=0.7)
        
        logger.info(f"[DEBUG] LLM call completed. Raw AI response length: {len(text_response)}")
        logger.info(f"[DEBUG] Raw AI response preview: {text_response[:200]}{'...' if len(text_response) > 200 else ''}")
        
        return {"evaluation": text_response}
        
    except Exception as e:
        logger.error(f"[DEBUG] Error evaluating reading lesson: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating reading lesson: {str(e)}"
        )
