from datasketch import MinHash
from app.utils.minhash import serialize_minhash, deserialize_minhash

if __name__ == "__main__":
    product = "Coffee"
    
    minhash = MinHash(num_perm=128)
    minhash.update(product.encode('utf-8'))
    
    quality = "God"
    minhash.update(quality.encode('utf-8'))
    
    minhash_data = serialize_minhash(minhash)
    print(minhash_data)
