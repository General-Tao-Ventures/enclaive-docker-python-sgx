from pydantic import BaseModel
from typing import List

# The request format for both minhash endpoints
class MinHashInput(BaseModel):
    user_id: str
    minhash_data: str

# The response format for the `/minhash` endpoint
class SaveMinHashOutput(BaseModel):
    id: int

# A single candidate for the `/minhash/query` endpoint
class QueryMinHashOutputOne(BaseModel):
    id: int
    user_id: str
    minhash: str
    similarity: float

# The response format for the `/minhash/query` endpoint
class QueryMinHashOutput(BaseModel):
    candidates: List[QueryMinHashOutputOne]

