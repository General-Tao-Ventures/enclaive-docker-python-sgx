from datasketch import MinHash
import base64
import json
import numpy as np
import os

def serialize_minhash(minhash: MinHash) -> str:
    """Serialize a MinHash object to a JSON string."""
    minhash_dict = {
        'seed': minhash.seed,
        'hashvalues': base64.b64encode(minhash.hashvalues.tobytes()).decode('ascii')
    }
    return json.dumps(minhash_dict)

def deserialize_minhash(json_str: str) -> MinHash:
    """Deserialize a JSON string to a MinHash object."""
    minhash_dict = json.loads(json_str)
    minhash = MinHash(num_perm=int(os.getenv('NUM_PERM', 128)), seed=minhash_dict['seed'])
    minhash.hashvalues = np.frombuffer(base64.b64decode(minhash_dict['hashvalues']), dtype=np.uint64)
    return minhash