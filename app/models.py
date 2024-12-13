from sqlalchemy import Column, String, Integer
from database import Base

class Proof(Base):
    __tablename__ = "proofs"

    proof_key = Column(String, primary_key=True, index=True)
    data_hash = Column(String, index=True)

class OrderHistory(Base):
    __tablename__ = "order_history"

    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(String, index=True)
    minhash = Column(String, index=True)
