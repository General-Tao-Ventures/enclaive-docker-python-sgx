from fastapi import FastAPI, HTTPException, Security, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from database import insert_proof, get_proof_by_hash, get_minhash_entry_by_id, insert_minhash_entry
from model import Proof, MinHashEntry, MinHashRequest
import hashlib
import aiohttp
from helpers import serialize_minhash, deserialize_minhash, download_and_hash
import asyncio
import uvicorn
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import argparse
from pydantic import BaseModel
from datasketch import MinHashLSH, MinHash

API_KEY_HEADER_NAME = "X-API-KEY"

# Create an argument parser
parser = argparse.ArgumentParser(description="Proof of Uniqueness Server")

# Add arguments for env file, host, port, key, cert file
parser.add_argument("--env-file", type=str, default=".env.example", help="The path to the env variable file to load")
parser.add_argument("--db-url", type=str, default="sqlite:////tmp/database.db", help="The database URL to connect to (with schema)")
parser.add_argument("--host", type=str, default="0.0.0.0", help="The host to run the server on")
parser.add_argument("--port", type=int, default="8888", help="The port to run the server on")
parser.add_argument("--ssl-keyfile", type=str, default="./certs/key.pem", help="Path to the SSL key file")
parser.add_argument("--ssl-certfile", type=str, default="./certs/cert.pem", help="Path to the SSL cert file")

# Create a FastAPI app. We need to do this here because it needs to be global
app = FastAPI()

# Parse the arguments
ARGS = parser.parse_args()

# Load the environment variables from the configured file
load_dotenv(ARGS.env_file)

# Try to get the API key, panicking if it's not set
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable not set")

# Configure the app to effectively skip CORS checks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is the header that FastAPI will use to check for the API key
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)

# Used to check the API key
async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key_header

# Generate a proof by visiting a URL and hashing the contents
@app.get("/generate_proof")
async def generate_proof(
    link: str = Query(...),
    api_key: str = Depends(get_api_key)
):
    # Hash the link and the data at that link
    link_hash = hashlib.sha3_256(link.encode('utf-8')).hexdigest()
    data_hash = await download_and_hash(link)

    # Return early if we failed to download or hash the data
    if data_hash is None:
        raise HTTPException(status_code=400, detail="Failed to download or hash data.")

    # Insert the proof into the database
    insert_proof(ARGS.db_url, link_hash, data_hash)
    
    return {"message": "Proof submitted successfully", "link_hash": link_hash}

# Get a proof by its hash from the DB
@app.get("/get_proof")
async def get_proof(
    proof_hash: str = Query(...),
    api_key: str = Depends(get_api_key)
):
    # Get the proof from the database
    data = get_proof_by_hash(ARGS.db_url, proof_hash)

    # Return the proof if it exists
    if data:
        return {"data_hash": data.data_hash}
    else:
        raise HTTPException(status_code=404, detail="Proof not found.")

# Initialize the LSH object
lsh = MinHashLSH(
    threshold=float(os.getenv("LSH_THRESHOLD", 0.7)),
    num_perm=int(os.getenv("NUM_PERM", 128))
)

# Query similar minhashes
@app.post("/minhash/query")
async def query_similar_minhashes(entry: MinHashRequest, api_key: str = Depends(get_api_key)):
    try:
        query_minhash = deserialize_minhash(entry.minhash_data, os.getenv("NUM_PERM", 128))
        candidate_keys = lsh.query(query_minhash)
        
        results = []
        for key in candidate_keys:
            user_id, id_str = key.split('_')
            id = int(id_str)
            entry_data = get_minhash_entry_by_id(ARGS.db_url, id)
            if entry_data:
                _, _, minhash = entry_data
                similarity = query_minhash.jaccard(minhash)
                results.append({
                    "id": id,
                    "user_id": user_id,
                    "minhash": serialize_minhash(minhash),
                    "similarity": similarity
                })
        
        return {"candidates": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Save a minhash entry
@app.post("/minhash")
async def save_minhash(entry: MinHashRequest, api_key: str = Depends(get_api_key)):
    try:
        minhash = deserialize_minhash(entry.minhash_data)
        id = insert_minhash_entry(ARGS.db_url, entry.user_id, minhash)
        key = f"{entry.user_id}_{id}"
        lsh.insert(key, minhash)
        return {"id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

if __name__ == "__main__":
    # Run the FastAPI app
    uvicorn.run(
        app, 
        host=ARGS.host,
        port=ARGS.port,
        ssl_keyfile=ARGS.ssl_keyfile,
        ssl_certfile=ARGS.ssl_certfile,
    )