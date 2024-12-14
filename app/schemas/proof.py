from pydantic import BaseModel

class GenerateProofInput(BaseModel):
    link: str

class GenerateProofOutput(BaseModel):
    link: str
    proof_key: str

class GetProofOutput(BaseModel):
    proof_key: str
    data_hash: str
