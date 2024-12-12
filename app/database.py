from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String
from model import Base, Proof, MinHashEntry
from helpers import serialize_minhash, deserialize_minhash
import uuid

# The uninitialized DB session
Session = None

def get_or_init_db(url: str):
    # If not yet initialized,
    global Session
    if not Session:
        # Create the database engine and a session
        engine = create_engine(
            url, connect_args={"check_same_thread": False}
        )
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create the proofs table if it does not exist
        Base.metadata.create_all(bind=engine)

    # Get the session
    db = Session()

    # Return the session
    try:
        yield db
    finally:
        db.close()


# Insert a proof into the database
def insert_proof(db_url, link_hash, data_hash):
    # Create the proof to insert
    db_item = Proof(proof_hash=link_hash, data_hash=data_hash)

    # Get the DB session
    db = next(get_or_init_db(db_url))

    # Add the proof to the session and commit
    db.add(db_item)
    db.commit()


# Get a proof by its hash from the database
def get_proof_by_hash(db_url, proof_hash):
    # Get the DB session
    db = next(get_or_init_db(db_url))

    # Query the proof by its hash
    proof = db.query(Proof).filter(Proof.proof_hash == proof_hash).first()

    # Return the proof
    return proof

# Insert a minhash entry into the database
def insert_minhash_entry(db_url, user_id, minhash):
    # Serialize the minhash
    minhash_data = serialize_minhash(minhash)

    # Create the minhash entry to insert
    db_item = MinHashEntry(user_id=user_id, minhash_data=minhash_data)

    # Get the DB session
    db = next(get_or_init_db(db_url))

    # Add the minhash entry to the session and commit
    db.add(db_item)
    db.commit()

    # Return the ID of the inserted entry
    return db_item.id

# Get a minhash entry by its ID
def get_minhash_entry_by_id(db_url, entry_id):
    # Get the DB session
    db = next(get_or_init_db(db_url))

    # Query the minhash entry by its ID
    entry = db.query(MinHashEntry).filter(MinHashEntry.id == entry_id).first()

    # Deserialize the minhash
    return deserialize_minhash(entry.minhash_data)
