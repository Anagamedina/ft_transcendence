from fastapi import FastAPI
from sqlalchemy import create_engine
import psycopg
from pydantic_settings import BaseSettings

app = FastAPI()

if __name__ == "__main__":
    print("Imports OK :)")