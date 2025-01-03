import re
import hashlib
import aiohttp
from urllib.parse import urlparse

async def download_and_hash(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    data_hash = hashlib.sha3_256(content).hexdigest()
                    return data_hash
    except Exception as e:
        print(f"Error downloading or hashing data: {e}")
        return None
    finally:
        pass

def is_valid_amazon_link(link):
    parsed_url = urlparse(link)
    pattern = r'^.*\.s3\.amazonaws\.[a-z]{2,3}$'
    if not parsed_url.scheme == "https":
        return False
    if not re.match(pattern, parsed_url.netloc):
        return False
    if not parsed_url.path.endswith("All%20Data%20Categories.zip"):
        return False
    return True
