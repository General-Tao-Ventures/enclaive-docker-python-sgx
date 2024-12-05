from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
import hashlib
import aiohttp
import asyncio
import os
from database import SessionLocal, engine
import models
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables from the mounted config directory
env_path = os.getenv('ENV_FILE', '/app/config/.env')
# load_dotenv(env_path)
load_dotenv()

# Get API key from environment variable with a default value for safety
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY")  # Get API key from environment variable

if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set")

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

@app.get("/generate_proof")
async def generate_proof(
    link: str = Query(...),
    api_key: str = Depends(get_api_key)
):
    link_hash = hashlib.sha3_256(link.encode('utf-8')).hexdigest()
    data_hash = await download_and_hash(link)
    if data_hash is None:
        raise HTTPException(status_code=400, detail="Failed to download or hash data.")
    db = next(get_db())
    db_item = models.Proof(proof_hash=link_hash, data_hash=data_hash)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "Proof submitted successfully", "link_hash": link_hash}

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

async def download_and_hash(url):
    temp_file = "temp_download.zip"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    data_hash = hashlib.sha3_256(content).hexdigest()
                    return data_hash
    except Exception as e:
        print(f"Error downloading or hashing data: {e}")
        return None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8888,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem"
    )
