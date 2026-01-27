from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# Use the same DATABASE_URL from database.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/read_and_write_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()