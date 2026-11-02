from fastapi import FastAPI
from sqlalchemy import create_engine
import psycopg
from pydantic_settings import BaseSettings

from app.core.database import SessionLocal, engine, get_db

app = FastAPI()

def test_database_objects_exist():
    assert engine is not None
    assert SessionLocal is not None
    assert get_db is not None

if __name__ == "__main__":
    test_database_objects_exist()
    print("Imports OK :)")