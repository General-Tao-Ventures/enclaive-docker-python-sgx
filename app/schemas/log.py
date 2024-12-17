from pydantic import BaseModel
from typing import List

# The request format for both minhash endpoints
class LogInput(BaseModel):
    proof_key: str
    log_content: str
