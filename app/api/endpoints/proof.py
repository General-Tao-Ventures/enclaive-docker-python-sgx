from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import hashlib
import os

from app.schemas.proof import GenerateProofInput, GenerateProofOutput, GetProofOutput
from app.db.models.proof import Proof
from app.services.proof import get_proof_by_proof_key, create_proof
from app.api.deps import get_db, get_api_key
from app.utils.misc import is_valid_amazon_link, download_and_modify_zip


router = APIRouter()

@router.get("/{proof_key}", response_model=GetProofOutput)
def get_proof(
    proof_key: str,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    proof = get_proof_by_proof_key(db, proof_key=proof_key)
    if not proof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proof not found")
    return GetProofOutput(proof_key=proof_key, data_hash=proof.data_hash)

def remove_file(path: str) -> None:
    os.unlink(path)
    print("Deleted temp file:", path)
    
@router.post("/")
async def generate_proof(
    item: GenerateProofInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    print("Amazon link to generate proof:", item.link)
    if not is_valid_amazon_link(item.link):
        raise HTTPException(status_code=400, detail="Invalid Amazon link")

    proof_key = hashlib.sha3_256(item.link.encode('utf-8')).hexdigest()
    proof = get_proof_by_proof_key(db, proof_key=proof_key)
    if proof:
        raise HTTPException(status_code=400, detail="The proof already generated")
    
    data_hash, output_filepath = await download_and_modify_zip(item.link)
    print("Data hash:", data_hash)
    if data_hash is None:
        raise HTTPException(status_code=400, detail="Failed to download or hash data.")

    print("Proof key:", proof_key)
    create_proof(db, Proof(proof_key=proof_key, data_hash=data_hash))

    headers = {
        "X-Proof-Key": proof_key,
        "X-Link": item.link,
        "Access-Control-Expose-Headers": "X-Proof-Key, X-Link",
    }

    background_tasks.add_task(remove_file, output_filepath)

    return FileResponse(output_filepath, headers=headers, media_type="application/zip")
