from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from db.models.proof import Proof

def get_proof_by_proof_key(db: Session, proof_key: str):
    return db.query(Proof).filter(Proof.proof_key == proof_key).first()

def create_proof(db: Session, proof: Proof):
    db.add(proof)
    db.commit()
    db.refresh(proof)
    return proof
