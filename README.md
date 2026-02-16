# Read & Write Backend

This is the backend API for the Read & Write application, built with FastAPI.

## Features

- User authentication and management
- Essay storage and management
- AI-powered writing analysis and feedback
- Reading lesson generation

## Requirements

- Python 3.11


## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables by creating a `.env` file:
   ```env
   DATABASE_URL=postgresql://username:password@localhost/database_name
   GEMINI_API_KEY=your-gemini-api-key
   DEEPSEEK_API_KEY=your-deepseek-api-key
   SECRET_KEY=your-super-secret-key-for-jwt-tokens
   ```

3. Initialize the database:
   ```bash
   python initial_db.py
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`.

## API Endpoints

### Users
- `POST /api/users/register` - Register a new user
- `POST /api/users/login` - Log in a user
- `GET /api/users/profile` - Get current user's profile
- `PUT /api/users/profile` - Update current user's profile

### Essays
- `GET /api/essays` - Get all essays for current user
- `POST /api/essays` - Create a new essay
- `GET /api/essays/{id}` - Get a specific essay
- `PUT /api/essays/{id}` - Update a specific essay
- `DELETE /api/essays/{id}` - Delete a specific essay

### AI Services
- `POST /api/ai/generate-reading-lesson` - Generate a reading lesson
- `POST /api/ai/analyze-writing` - Analyze writing and provide feedback
- `POST /api/ai/full-analyze-writing` - Full writing analysis with multiple aspects

### Deployment in Railway.app
uvicorn main:app  --reload --host 0.0.0.0 --port $PORT --log-level warning
create runtime.txt and add a line for python
python-3.11.9
