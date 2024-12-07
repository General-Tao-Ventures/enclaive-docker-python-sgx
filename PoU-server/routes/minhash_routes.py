import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datasketch import MinHashLSH
from dotenv import load_dotenv

from minhash_utils import deserialize_minhash, serialize_minhash
from database_manager import DatabaseManager

load_dotenv()

# Initialize components
db_path = os.getenv("DB_FILE", "database/order_history.db")
db_manager = DatabaseManager(db_path)
lsh = MinHashLSH(
    threshold=float(os.getenv("LSH_THRESHOLD", 0.7)),
    num_perm=int(os.getenv("NUM_PERM", 128))
)

router = APIRouter()

class MinHashEntry(BaseModel):
    user_id: str
    minhash_data: str

class QueryResult(BaseModel):
    entries: List[Dict[str, str]]

@router.post("/minhash/query")
async def query_similar_minhashes(entry: MinHashEntry):
    try:
        query_minhash = deserialize_minhash(entry.minhash_data)
        candidate_keys = lsh.query(query_minhash)
        
        results = []
        for key in candidate_keys:
            user_id, id_str = key.split('_')
            id = int(id_str)
            entry_data = db_manager.get_by_id(id)
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

@router.post("/minhash")
async def save_minhash(entry: MinHashEntry):
    try:
        minhash = deserialize_minhash(entry.minhash_data)
        last_id = db_manager.save_minhash(entry.user_id, minhash)
        key = f"{entry.user_id}_{last_id}"
        lsh.insert(key, minhash)
        return {"id": last_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 