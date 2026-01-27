#!/usr/bin/env python3
"""
Test script for the new /api/ai/sample endpoint
"""

import requests
import json

def test_essay_search_api():
    """Test the essay search API endpoint"""
    
    # Test data
    test_query = {
        "query_text": "In the book The Rogue Wave by Theodore Taylor, Scoot and her older brother go on a sailboat named the Old Sea Dog on the Pacific Ocean. Sully, her older brother, was teaching her how to sail. On their adventure, they hit a huge rogue wave and the boat flipped upside down. They both got stuck in different places and Scoot blacked out. Sully wasn't able to hear her so he was absolutely terrified and worried. Eventually, Scoot woke up and was banging on the wall. Some nearby fishermen saved them.",
        "score_level": 2,
        "top_k": 3
    }
    
    # API endpoint (adjust URL as needed for your setup)
    url = "http://localhost:8000/api/ai/sample"
    
    print("Testing Essay Search API...")
    print(f"Query: {test_query['query_text'][:100]}...")
    print(f"Score level: {test_query['score_level']}")
    print(f"Top K: {test_query['top_k']}")
    print()
    
    try:
        # Make the API request
        response = requests.post(url, json=test_query)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"Found {len(result.get('results', []))} results")
            
            # Display results
            for i, essay in enumerate(result.get('results', []), 1):
                print(f"\n--- Result {i} ---")
                print(f"ID: {essay.get('id')}")
                print(f"Grade: {essay.get('grade')}")
                print(f"Writing Type: {essay.get('writing_type')}")
                print(f"Score Level: {essay.get('score_level')}")
                print(f"Similarity: {essay.get('similarity')}")
                print(f"Essay Text: {essay.get('essay_text')[:200]}...")
                if essay.get('score_rationale'):
                    print(f"Score Rationale: {essay.get('score_rationale')[:100]}...")
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_essay_search_api()