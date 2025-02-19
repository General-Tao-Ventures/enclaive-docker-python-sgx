from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import hashlib

from app.schemas.log import LogInput
from app.db.models.proof import Proof
from app.services.proof import get_proof_by_proof_key, create_proof
from app.api.deps import get_db, get_api_key


router = APIRouter()

@router.post("/")
def log(
    item: LogInput,
    api_key: str = Depends(get_api_key),
):
    print(f"===> PoC Logging for the proof key: {item.proof_key}")
    print(item.log_content)
