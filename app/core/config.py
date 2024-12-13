# app/core/config.py
from dotenv import load_dotenv
from pydantic import BaseModel

import os

class Settings(BaseModel):
    API_KEY: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str


load_dotenv()

settings = Settings(
    API_KEY=os.getenv("API_KEY"),
    POSTGRES_USER=os.getenv("POSTGRES_USER"),
    POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD"),
    POSTGRES_DB=os.getenv("POSTGRES_DB"),
)
