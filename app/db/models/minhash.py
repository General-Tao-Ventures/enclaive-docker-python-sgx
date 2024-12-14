from sqlalchemy import Column, Integer, String
from app.db.base import Base

class MinHash(Base):
    __tablename__ = "minhashes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, index=True)
    minhash_data = Column(String, index=True)
