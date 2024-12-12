from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

# The request format for the minhash endpoints
class MinHashRequest(BaseModel):
    user_id: str
    minhash_data: str

class Proof(Base):
    __tablename__ = "proofs"

    proof_hash = Column(String, primary_key=True, index=True)
    data_hash = Column(String, index=True)

class MinHashEntry(Base):
    __tablename__ = "minhashes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    minhash_data = Column(String, index=True)
