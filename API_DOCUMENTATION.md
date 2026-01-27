# Essay Search API Documentation

## Overview

The new `/api/ai/sample` endpoint allows frontend applications to search for similar essays in the Snowflake database using Cortex Search Service.

## API Endpoint

```
POST /api/ai/sample
```

## Request Format

```json
{
  "query_text": "Your essay text here...",
  "score_level": 2,  // Optional: Filter by minimum score level (1-6)
  "top_k": 3         // Optional: Number of results to return (default: 2)
}
```

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_text` | string | Yes | The essay text to search for similar essays |
| `score_level` | integer | No | Minimum score level filter (1-6). Only essays with score_level >= this value will be returned |
| `top_k` | integer | No | Maximum number of results to return (default: 2) |

## Response Format

```json
{
  "results": [
    {
      "id": "101",
      "grade": "7",
      "writing_type": "Argumentative",
      "score_level": "3",
      "essay_text": "Splash! A 16 year old girl named Abby Sunderland...",
      "score_rationale": "This essay received a 3 on the district rubric...",
      "similarity": 0.85
    }
  ]
}
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier of the essay |
| `grade` | string | Grade level of the essay |
| `writing_type` | string | Type of writing (e.g., "Argumentative", "Narrative") |
| `score_level` | string | Score level/rating of the essay |
| `essay_text` | string | The complete essay content (full text) |
| `score_rationale` | string | Explanation of the score (may be null) |
| `similarity` | number | Similarity score (may be null) |

## Example Usage

### Frontend JavaScript Example

```javascript
async function searchSimilarEssays(queryText, scoreLevel = null, topK = 3) {
  const response = await fetch('/api/ai/sample', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + yourAuthToken
    },
    body: JSON.stringify({
      query_text: queryText,
      score_level: scoreLevel,
      top_k: topK
    })
  });

  if (!response.ok) {
    throw new Error('Search failed: ' + response.statusText);
  }

  const data = await response.json();
  return data.results;
}

// Usage
const query = "Your essay text here...";
const results = await searchSimilarEssays(query, 3, 5);
console.log('Found', results.length, 'similar essays');
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/ai/sample" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token_here" \
  -d '{
    "query_text": "Your essay text here...",
    "score_level": 3,
    "top_k": 5
  }'
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400 Bad Request`: Missing or invalid query_text
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Server error during search

## Authentication

This endpoint requires user authentication. The frontend must include a valid JWT token in the Authorization header.

## Integration Notes

1. **Snowflake Dependencies**: The API requires Snowflake credentials in environment variables:
   - `SNOWFLAKE_USER`
   - `SNOWFLAKE_PASSWORD`
   - `SNOWFLAKE_ACCOUNT`
   - `SNOWFLAKE_WAREHOUSE`
   - `SNOWFLAKE_ROLE`
   - `SNOWFLAKE_DATABASE`
   - `SNOWFLAKE_SCHEMA`

2. **Snowpark Library**: The API uses the Snowpark library for modern Snowflake connectivity. Install with:
   ```bash
   pip install snowflake-snowpark-python
   ```

3. **Cortex Search Service**: The API connects to the `ESSAY_SEARCH_SERVICE` in the `EDUCATION.PUBLIC` schema.

## Testing

Use the provided test script to verify the API is working:

```bash
python test_api_endpoint.py
```

This will test the endpoint with sample data and display the results.