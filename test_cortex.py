import snowflake.connector
import json
import os
import time
import threading
import logging
import glob
from datetime import datetime, timedelta
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
    DEFAULT_TARGET_LAG = '1 hour'
    DEFAULT_TOP_K = 2
    
    def __init__(self):
        load_dotenv()
        self.connection_params = {
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'warehouse': os.getenv('COMPUTE_WH'),
            'role': os.getenv('ACCOUNTADMIN'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA')
        }
        # Remove embeddings_cache and refresh logic - Cortex handles this
        self.search_service_name = 'essay_search_service'
        
    def get_connection(self):
        """Create Snowflake connection with proper error handling"""
        try:
            return snowflake.connector.connect(**self.connection_params)
        except Exception as e:
            print(f"Failed to create Snowflake connection: {str(e)}", exc_info=True)
            raise
    
    def _validate_json_response(self, json_data):
        """Validate and parse JSON response safely"""
        try:
            if isinstance(json_data, str):
                return json.loads(json_data)
            return json_data
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Invalid JSON response: {str(e)}")
            return None
    
    def _format_essay_result(self, item):
        """Format essay result with consistent structure"""
        essay_text = item.get('essay_text', '') or item.get('ESSAY_TEXT', '')
        truncated_text = (essay_text[:self.ESSAY_PREVIEW_LENGTH] + "..." 
                         if len(essay_text) > self.ESSAY_PREVIEW_LENGTH 
                         else essay_text)
        
        return {
            'id': item.get('id') or item.get('ID'),
            'grade': item.get('grade') or item.get('GRADE'),
            'writing_type': item.get('writing_type') or item.get('WRITING_TYPE'),
            'score_level': item.get('score_level') or item.get('SCORE_LEVEL'),
            'essay_text': truncated_text,
            'score_rationale': item.get('score_rationale') or item.get('SCORE_RATIONALE'),
            'similarity': item.get('score', 'N/A')
        }
    
    def search_similar_essays(self, query_text, score_level=None, top_k=None):
        """Search for similar essays using Cortex Search Service"""
        if top_k is None:
            top_k = self.DEFAULT_TOP_K
            
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("USE DATABASE education")
            cur.execute("USE SCHEMA public")
            
            # Use json.dumps to ensure double quotes and valid JSON formatting
            columns = ["essay_text", "grade", "writing_type", "score_level", "score_rationale", "id"]
            limit = top_k * 2 if score_level is not None else top_k
            
            query_payload = {
                "query": query_text,
                "columns": columns,
                "limit": limit
            }
            
            json_query = json.dumps(query_payload)
            
            search_sql = """
                SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                    'EDUCATION.PUBLIC.ESSAY_SEARCH_SERVICE',
                    %s
                )
            """
            
            cur.execute(search_sql, (json_query,))
            result = cur.fetchone()
            
            # Parse the JSON result
            if result and result[0]:
                search_results = self._validate_json_response(result[0])
                if not search_results:
                    print("Invalid search response format")
                    return []
                    
                        
                # Extract the results from the JSON response
                similar_essays = []
                if 'results' in search_results and search_results['results']:
                    for item in search_results['results']:
                        # Apply score_level filter if specified (since we got more results)
                        if score_level is not None and item.get('score_level') != score_level:
                            continue
                            
                        similar_essays.append(self._format_essay_result(item))
                        
                        # Limit results if score_level filter was applied
                        if len(similar_essays) >= top_k:
                            break
                
                print(f"SQL search returned {len(similar_essays)} results")
                return similar_essays
            else:
                print("No results returned from search")
                return []
            
        except Exception as e:
            print(f"SQL search failed: {str(e)}", exc_info=True)
            return []
        finally:
            cur.close()
            conn.close()
    
    
    def get_search_service_status(self):
        """Check Cortex Search Service status"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("USE DATABASE education")
            cur.execute("USE SCHEMA public")
            cur.execute("SHOW CORTEX SEARCH SERVICES")
            services = cur.fetchall()
            
            print("Cortex Search Services:")
            for service in services:
                print(f"  - {service}")
                
            # Also check if our specific service exists
            cur.execute("DESCRIBE CORTEX SEARCH SERVICE essay_search_service")
            service_details = cur.fetchall()
            print(f"Service Details for {self.search_service_name}:")
            for detail in service_details:
                print(f"  - {detail}")
                    
        except Exception as e:
            print(f"Status check failed: {str(e)}", exc_info=True)
        finally:
            cur.close()
            conn.close()
    
    # Remove start_auto_refresh method - Cortex handles refresh automatically

   
    


# Example usage and testing
if __name__ == "__main__":
    search_service = EssaySearchService()
    search_service.get_search_service_status()
    text_sample = "In the book The Rogue Wave by Theodore Taylor, " \
    "Scoot and her older brother go on a sailboat named the Old Sea Dog on the Pacific Ocean. " \
    "Sully, her older brother, was teaching her how to sail. On their adventure, " \
    "they hit a huge rogue wave and the boat flipped upside down. " \
    "They both got stuck in different places and Scoot blacked out. " \
    "Sully wasn't able to hear her so he was absolutely terrified and worried." \
    " He was banging on the wall but Scoot was still blacked out. " \
    "Eventually, Scoot woke up and was banging on the wall and he heard the banging but couldn't hear her voice." \
    " Sully had already tried the door but it was jammed, therefore he was unable to get to her any sooner. " \
    "She was also unable to open the door from the other side. Scoot looked around and found a tool box with a screw in it. " \
    "She opened the window and some nearby fishermen on a boat named the Red Rooster saved them."
    results = search_service.search_similar_essays(text_query=text_sample, score_level=4, top_k=1)
    print("Search Results:")
    for res in results:
        print(res)  
    
    

