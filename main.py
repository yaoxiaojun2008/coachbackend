from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="English coach API", version="1.0.0")

# Import route modules
from routes import users, essays, ai, auth_test

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware to log API requests
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    print(f"[DEBUG] API CALL START: {request.method} {request.url.path}")
    
    # Extract important headers for logging
    auth_header = request.headers.get("authorization", "Not provided")
    if auth_header != "Not provided":
        # Mask the token for security
        auth_header = f"Bearer {auth_header[7:12]}..." if len(auth_header) > 10 else "Masked"
    
    print(f"[DEBUG] Headers: method={request.method}, path={request.url.path}, auth={auth_header}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    print(f"[DEBUG] API CALL END: {request.method} {request.url.path} - Status: {response.status_code} - Process Time: {process_time:.2f}s")
    return response

# Include API routes
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(essays.router, prefix="/api/essays", tags=["essays"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/")
def read_root():
    print(f"[DEBUG] Root endpoint accessed")
    return {"message": "Backend API is healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")