import zipfile
import os
import asyncio
from pathlib import Path
import time
import hashlib
from app.utils.misc import modify_zip


async def test_modify_zip():
    # measure modify_zip execution time
    start_time = time.time()
    temp_dir = Path("./tests/demo")
    input_zip = temp_dir / "input.zip"
    output_zip = temp_dir / "output.zip"

    await modify_zip(input_zip, output_zip)
    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")
    
    # calculate hash
    start_time = time.time()
    hash_obj = hashlib.sha3_256()
    with open(output_zip, "rb") as f:
        while chunk := f.read(4096):
            hash_obj.update(chunk)
    print(f"Hash: {hash_obj.hexdigest()}")
    end_time = time.time()
    print(f"Hash time: {end_time - start_time} seconds")
    

asyncio.run(test_modify_zip())