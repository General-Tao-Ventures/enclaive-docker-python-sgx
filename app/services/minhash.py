from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.db.models.minhash import MinHash
from utils.minhash import serialize_minhash, deserialize_minhash
from app.core.config import settings
from app.db.models.minhash import MinHash as MinHashDb
from datasketch import MinHash


# Insert a minhash entry into the database
def save_minhash(db: Session, user_id, minhash) -> int:
    # Serialize the minhash
    minhash_data = serialize_minhash(minhash)

    # Create the minhash entry to insert
    db_item = MinHashDb(user_id=user_id, minhash_data=minhash_data)

    # Add the minhash entry to the session and commit
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Return the ID of the inserted entry
    return db_item.id

# Query a minhash entry by its ID
def get_minhash_by_id(db: Session, entry_id: int) -> MinHash:
    # Query the minhash entry by its ID
    entry = db.query(MinHashDb).filter(MinHashDb.id == entry_id).first()

    # Deserialize the minhash
    return deserialize_minhash(entry.minhash_data)
