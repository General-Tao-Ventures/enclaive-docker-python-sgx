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
    if not parsed_url.scheme == "https":
        return False
    if not parsed_url.netloc.endswith("s3.amazonaws.com"):
        return False
    if not parsed_url.path.endswith("Your%20Orders.zip"):
        return False
    return True
