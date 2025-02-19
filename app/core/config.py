# app/core/config.py
from dotenv import load_dotenv
from pydantic import BaseModel

import os

class Settings(BaseModel):
    API_KEY: str
    GMAPS_API_KEY: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    MINHASH_LSH_THRESHOLD: float
    MINHASH_NUM_PERM: int


load_dotenv()

settings = Settings(
    API_KEY=os.getenv("API_KEY"),
    GMAPS_API_KEY=os.getenv("GMAPS_API_KEY"),
    POSTGRES_USER=os.getenv("POSTGRES_USER"),
    POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD"),
    POSTGRES_DB=os.getenv("POSTGRES_DB"),
    MINHASH_LSH_THRESHOLD=float(os.getenv("MINHASH_LSH_THRESHOLD", "0.7")),
    MINHASH_NUM_PERM=int(os.getenv("MINHASH_NUM_PERM", "128")),
)
