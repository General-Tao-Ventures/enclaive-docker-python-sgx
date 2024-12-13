from sqlalchemy import Column, String
from database import Base

class Proof(Base):
    __tablename__ = "proofs"

    proof_key = Column(String, primary_key=True, index=True)
    data_hash = Column(String, index=True)
