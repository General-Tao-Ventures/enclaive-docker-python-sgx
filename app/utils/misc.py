import hashlib
import aiohttp
from urllib.parse import urlparse

async def download_and_hash(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status == 200:
                    # hash_obj = hashlib.sha3_256()
                    hash_obj = hashlib.new("sha3_256")
                    while True:
                        chunk = await resp.content.read(4096)
                        if not chunk:
                            break
                        hash_obj.update(chunk)
                    return hash_obj.hexdigest()

                    # content = await resp.read()
                    # data_hash = hashlib.sha3_256(content).hexdigest()
                    # return data_hash
                
    except Exception as e:
        print(f"Error downloading or hashing data: {e}")
        return None
    finally:
        pass

def is_valid_amazon_link(link):
    valid_domains = [
        "amazonaws.com.au",
        "amazonaws.com.be",
        "amazonaws.com.br",
        "amazonaws.ca",
        "amazonaws.cn",
        "amazonaws.eg",
        "amazonaws.fr",
        "amazonaws.de",
        "amazonaws.in",
        "amazonaws.it",
        "amazonaws.co.jp",
        "amazonaws.com.mx",
        "amazonaws.nl",
        "amazonaws.pl",
        "amazonaws.sa",
        "amazonaws.sg",
        "amazonaws.es",
        "amazonaws.se",
        "amazonaws.com.tr",
        "amazonaws.ae",
        "amazonaws.co.uk",
        "amazonaws.com",
        "amazonaws.co",
        "amazonaws.com.cn",
        "amazonaws.com.sg"
    ]
    
    parsed_url = urlparse(link)
    if not parsed_url.scheme == "https":
        return False
    if not any(parsed_url.netloc.endswith(domain) for domain in valid_domains):
        return False
    if not ".s3." in parsed_url.netloc:
        return False
    if not parsed_url.path.endswith(".zip"):
        return False
    if not ("All%20Data%20Categories" in parsed_url.path
            or "Your%20Orders" in parsed_url.path):
        return False
    return True
