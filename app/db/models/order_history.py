from sqlalchemy import Column, String, Integer
from db.base import Base

class OrderHistory(Base):
    __tablename__ = "order_history"

    id=Column(Integer, autoincrement=True, primary_key=True, index=True)
    user_id = Column(String, index=True)
    minhash = Column(String, index=True)
