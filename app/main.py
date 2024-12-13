from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import hashlib
import os

from database import SessionLocal, engine
from sqlalchemy.orm import Session

import models
import schemas
from utils import download_and_hash, is_valid_amazon_link
    
load_dotenv()

models.Base.metadata.create_all(bind=engine)


API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key_header


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/generate_proof")
async def generate_proof(
    item: schemas.GenerateProof,
    api_key: str = Depends(get_api_key)
):
    print("Amazon link to generate proof:", item.link)
    if not is_valid_amazon_link(item.link):
        raise HTTPException(status_code=400, detail="Invalid Amazon link")

    link_hash = hashlib.sha3_256(item.link.encode('utf-8')).hexdigest()
    data_hash = await download_and_hash(item.link)
    if data_hash is None:
        raise HTTPException(status_code=400, detail="Failed to download or hash data.")

    db = next(get_db())
    db_item = models.Proof(proof_hash=link_hash, data_hash=data_hash)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return {"message": "Proof submitted successfully", "link_hash": link_hash, "data_hash": data_hash}


@app.get("/get_proof")
def get_proof(
    proof_hash: str = Query(...),
    api_key: str = Depends(get_api_key)
):
    db = next(get_db())
    data = db.query(models.Proof).filter(models.Proof.proof_hash == proof_hash).first()
    if data:
        return {"data_hash": data.data_hash}
    else:
        raise HTTPException(status_code=404, detail="Proof not found.")

# TODO: Add a route/function for the Proof of Uniqueness database queries
# See: PoU-Server/ on how to query the database, ideally just port in here so it all runs on the same app/server


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8888,
    )
