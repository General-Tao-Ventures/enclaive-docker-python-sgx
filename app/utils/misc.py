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
    valid_domains = [
        "s3.amazonaws.com.au",
        "s3.amazonaws.com.be",
        "s3.amazonaws.com.br",
        "s3.amazonaws.ca",
        "s3.amazonaws.cn",
        "s3.amazonaws.eg",
        "s3.amazonaws.fr",
        "s3.amazonaws.de",
        "s3.amazonaws.in",
        "s3.amazonaws.it",
        "s3.amazonaws.co.jp",
        "s3.amazonaws.com.mx",
        "s3.amazonaws.nl",
        "s3.amazonaws.pl",
        "s3.amazonaws.sa",
        "s3.amazonaws.sg",
        "s3.amazonaws.es",
        "s3.amazonaws.se",
        "s3.amazonaws.com.tr",
        "s3.amazonaws.ae",
        "s3.amazonaws.co.uk",
        "s3.amazonaws.com",
        "s3.amazonaws.co",
        "s3.amazonaws.com.cn",
        "s3.amazonaws.com.sg"
    ]
    
    parsed_url = urlparse(link)
    if not parsed_url.scheme == "https":
        return False
    if not any(parsed_url.netloc.endswith(domain) for domain in valid_domains):
        return False
    if not (parsed_url.path.endswith("All%20Data%20Categories.zip")
            or parsed_url.path.endswith("All%20Data%20Categories.7.zip")
            or parsed_url.path.endswith("Your%20Orders.zip")
            or parsed_url.path.endswith("Your%20Orders.7.zip")):
        return False
    return True
