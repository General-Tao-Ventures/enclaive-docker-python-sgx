import requests
import hashlib
import asyncio
import aiohttp

# Replace with your server address
SERVER_ADDRESS = 'https://localhost:8888'

# Disable warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add this at the top with other constants
API_KEY = "primeinsights-priv-api-key"
HEADERS = {"X-API-Key": API_KEY}

async def submit_proof(link):
    params = {'link': link}
    response = requests.get(
        f"{SERVER_ADDRESS}/generate_proof", 
        params=params, 
        headers=HEADERS,  # Add headers here
        verify=False
    )
    if response.status_code == 200:
        data = response.json()
        print(f"Submitted proof for link: {link}")
        print(f"Link Hash: {data['link_hash']}")
        return data['link_hash']
    else:
        print(f"Failed to submit proof for link: {link}")
        print(f"Error: {response.text}")
        return None

async def query_proof(link_hash):
    params = {'proof_hash': link_hash}
    response = requests.get(
        f"{SERVER_ADDRESS}/get_proof", 
        params=params, 
        headers=HEADERS,  # Add headers here
        verify=False
    )
    if response.status_code == 200:
        data = response.json()
        print(f"Queried proof for link hash: {link_hash}")
        print(f"Data Hash: {data['data_hash']}")
        return data['data_hash']
    else:
        print(f"Proof not found for link hash: {link_hash}")
        print(f"Error: {response.text}")
        return None

def compute_link_hash(link):
    return hashlib.sha3_256(link.encode('utf-8')).hexdigest()

async def main():
    test_links = [
        'https://github.com/enclaive/enclaive-docker-python-sgx/archive/refs/heads/master.zip',
        'https://github.com/gramineproject/gramine/archive/refs/heads/master.zip',
        'https://github.com/python/cpython/archive/refs/heads/main.zip'
    ]

    link_hashes = {}

    # Submit proofs for multiple files
    for link in test_links:
        link_hash = await submit_proof(link)
        if link_hash:
            link_hashes[link] = link_hash

    print("\n--- Querying Proofs ---\n")

    # Query proofs and verify data hashes
    for link, link_hash in link_hashes.items():
        data_hash = await query_proof(link_hash)
        if data_hash:
            # For verification purposes, compute the expected data hash
            expected_data_hash = await download_and_hash(link)
            if data_hash == expected_data_hash:
                print(f"Data hash matches for link: {link}")
            else:
                print(f"Data hash does NOT match for link: {link}")
        print()

async def download_and_hash(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                content = await resp.read()
                data_hash = hashlib.sha3_256(content).hexdigest()
                return data_hash
    return None

if __name__ == "__main__":
    asyncio.run(main())
