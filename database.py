from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Initialize Supabase client using URL and SERVICE ROLE key for backend operations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # This should be the service role key


# Check if the required environment variables are present
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Missing required environment variables for Supabase client")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print(f"Successfully connected to Supabase: {SUPABASE_URL}")
    except Exception as e:
        print(f"Error initializing Supabase client: {str(e)}")
        supabase = None

def get_supabase_client():
    if supabase is None:
        raise Exception("Supabase client not initialized. Check your environment variables.")
    return supabase

# Database URL is not used since we're using Supabase client directly
# The SQLAlchemy setup is kept for any potential direct DB connections if needed
DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://user:password@localhost/read_and_write_db"

print(f"Attempting to connect to database: {DATABASE_URL}")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()