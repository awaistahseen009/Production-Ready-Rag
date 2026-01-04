from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
load_dotenv(override=True)

SQLALCHEMY_DATABASE_URL=os.getenv("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
import app.model 

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()