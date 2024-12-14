from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from schemas.minhash import MinHashInput, SaveMinHashOutput, QueryMinHashOutputOne, QueryMinHashOutput
from app.db.models.proof import Proof
from app.services.proof import get_proof_by_proof_key, create_proof
from app.api.deps import get_db, get_api_key
from app.utils.misc import is_valid_amazon_link, download_and_hash
from app.utils.minhash import deserialize_minhash, serialize_minhash
from app.core.config import settings
from datasketch import MinHashLSH
from app.services.minhash import save_minhash as save_minhash_db
from app.services.minhash import get_minhash_by_id

router = APIRouter()

# Create the MinHashLSH object
lsh = MinHashLSH(
    threshold=settings.MINHASH_LSH_THRESHOLD,
    num_perm=settings.MINHASH_NUM_PERM    
)

# Save a minhash entry
@router.post("/", response_model=SaveMinHashOutput)
def save_minhash(
    item: MinHashInput,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    try:
        # Deserialize the minhash
        minhash = deserialize_minhash(item.minhash_data)
        if not minhash:
            raise HTTPException(status_code=400, detail="Invalid minhash data")
        
        # Insert the minhash entry into the database
        minhash_id = save_minhash_db(db, item.user_id, minhash)
        if not minhash_id:
            raise HTTPException(status_code=500, detail="Failed to save minhash")
        
        # The key is the user ID and the minhash ID
        key = f"{item.user_id}_{minhash_id}"
        
        # Insert it into the LSH
        lsh.insert(key, minhash)

        return SaveMinHashOutput(id=minhash_id)
    except Exception as e:
        print(f"Failed to save minhash: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save minhash")


# Query for similar minhash entries
@router.post("/query", response_model=QueryMinHashOutput)
async def query_similar_minhashes(
    item: MinHashInput,
    api_key: str = Depends(get_api_key),
    db: Session = Depends(get_db)
):
    try:
        # Deserialize the minhash
        minhash = deserialize_minhash(item.minhash_data)
        if not minhash:
            raise HTTPException(status_code=400, detail="Invalid minhash data")
        
        # Get candidates
        candidate_keys = lsh.query(minhash)

        # For every candidate,
        results = list()
        for key in candidate_keys:
            try:
                # Split the key into user ID and minhash ID
                user_id_str, id_str = key.split("_")

                # Make sure the id is an integer
                id = int(id_str)

                # Get the minhash entry by its ID
                db_minhash = get_minhash_by_id(db, id)

                # See if we got something
                if db_minhash:
                    # Calculate the Jaccard similarity
                    similarity = db_minhash.jaccard(minhash)

                    # Add it to the list of candidates
                    results.append(QueryMinHashOutputOne(
                        id=id,
                        user_id=user_id_str,
                        minhash=serialize_minhash(db_minhash),
                        similarity=similarity,
                    ))
            except Exception as e:
                print(f"Failed to query minhash: {e}")
                continue
        
        return QueryMinHashOutput(candidates=results)
    except Exception as e:
        print(f"Failed to query minhash: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to query minhash")