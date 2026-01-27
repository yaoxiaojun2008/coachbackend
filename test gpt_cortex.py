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


# ---------------------------------------------------
# Logging Configuration
# ---------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class EssaySearchService:
    # -----------------------
    # Constants
    # -----------------------
    ESSAY_PREVIEW_LENGTH = 200
    DEFAULT_TOP_K = 2
    SCORE_LEVEL = 3

    # -----------------------
    # Initialization
    # -----------------------
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

    # -----------------------
    # Environment Validation
    # -----------------------
    def _validate_env(self):
        missing = [k for k, v in self.connection_params.items() if not v]
        if missing:
            raise ValueError(f"Missing environment variables: {missing}")

    # -----------------------
    # Connection
    # -----------------------
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

    # -----------------------
    # JSON Validation
    # -----------------------
    def _validate_json_response(self, data):
        try:
            if isinstance(data, str):
                return json.loads(data)
            return data
        except Exception:
            logging.exception("Invalid JSON returned from Cortex")
            return None

    # -----------------------
    # Result Formatting
    # -----------------------
    def _format_essay_result(self, item):
        essay_text = str(item.get("ESSAY_TEXT", "") or item.get("essay_text", ""))

        if len(essay_text) > self.ESSAY_PREVIEW_LENGTH:
            essay_text = essay_text[:self.ESSAY_PREVIEW_LENGTH] + "..."

        similarity = item.get("score")
        if similarity is not None:
            similarity = round(float(similarity), 4)

        return {
            "id": item.get("ID") or item.get("id"),
            "grade": item.get("GRADE") or item.get("grade"),
            "writing_type": item.get("WRITING_TYPE") or item.get("writing_type"),
            "score_level": item.get("SCORE_LEVEL") or item.get("score_level"),
            "essay_text": essay_text,
            "score_rationale": item.get("SCORE_RATIONALE") or item.get("score_rationale"),
            "similarity": similarity
        }

    # -----------------------
    # Search using Snowpark API (Modern Approach)
    # -----------------------
    def search_similar_essays_snowpark(self, query_text, score_level=None, top_k=None):
        """Search for similar essays using the modern Snowpark API,essay's score_level greater than or equal to the specified score_level """
        if not SNOWPARK_AVAILABLE:
            logging.warning("Snowpark not available, falling back to SQL approach")
            return self.search_similar_essays(query_text, score_level, top_k)

        if top_k is None:
            top_k = self.DEFAULT_TOP_K
        
        if score_level is None:
            score_level = self.SCORE_LEVEL

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
            return "no results"



  
    # -----------------------
    # Service Status
    # -----------------------
    def get_search_service_status(self):

        conn = self.get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("SHOW CORTEX SEARCH SERVICES")
                services = cur.fetchall()

                print("\nCortex Search Services:")
                for s in services:
                    print(" -", s[1])

                cur.execute(
                    f"DESCRIBE CORTEX SEARCH SERVICE {self.search_service_name}"
                )

                details = cur.fetchall()
                print(f"\nService Details: {self.search_service_name}")
                for d in details:
                    print(" -", d)

        except Exception:
            logging.exception("Status check failed")

        finally:
            conn.close()


# ---------------------------------------------------
# Example Usage
# ---------------------------------------------------
if __name__ == "__main__":

    search_service = EssaySearchService()
    search_service.get_search_service_status()

    text_sample = (
        "In the book The Rogue Wave by Theodore Taylor, "
        "Scoot and her older brother go on a sailboat named the Old Sea Dog "
        "on the Pacific Ocean. Sully, her older brother, was teaching her how "
        "to sail. On their adventure, they hit a huge rogue wave and the boat "
        "flipped upside down. They both got stuck in different places and "
        "Scoot blacked out. Sully wasn't able to hear her so he was absolutely "
        "terrified and worried. Eventually, Scoot woke up and was banging on "
        "the wall. Some nearby fishermen saved them."
    )

    # Try Snowpark approach first, fall back to SQL if needed
    # First try without score_level filter to see if we get any results

    print("Trying with score_level=2...")
    results = search_service.search_similar_essays_snowpark(
        query_text=text_sample,
        score_level=2,
        top_k=1
        )
    
    
    if not results:
        print("\n=== No results found with score_level filter.Testing without score_level filter ===")
        results = search_service.search_similar_essays_snowpark(
            query_text=text_sample,
            top_k=1
        )
    

    print("\nSearch Results:")
    for res in results:
        print(res)
