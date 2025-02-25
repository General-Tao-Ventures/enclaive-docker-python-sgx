import hashlib
import aiohttp
import time
import tempfile
import aiofiles
import zipfile
import os
import pandas as pd
import io
import asyncio
from app.core.config import settings
from urllib.parse import urlparse

GMAPS_API_KEY = settings.GMAPS_API_KEY

async def fetch_postal_code(session, location):
    if location == "Not Applicable":
        return location
    
    """Fetch postal code for a single location."""
    try:
        async with session.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": location, "key": GMAPS_API_KEY},
        ) as response:
            data = await response.json()
            if data["status"] == "OK":
                for component in data["results"][0]["address_components"]:
                    if "postal_code" in component["types"]:
                        return component["long_name"]
            else:
                raise Exception("Invalid GoogleMaps API Key")
    except Exception as e:
        print(f"Error fetching postal code for {location}: {e}")
    return "UNKNOWN"

async def get_postal_codes(locations: pd.Series) -> pd.Series:
    """Fetch postal codes for multiple locations concurrently."""
    unique_locations = locations.unique()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_postal_code(session, loc) for loc in unique_locations]
        postal_code_results = await asyncio.gather(*tasks)
    postal_code_dict = dict(zip(unique_locations, postal_code_results))
    return locations.map(postal_code_dict)

async def modify_zip(input_zip_path, output_zip_path):
    """Modify the ZIP file by removing or adding files."""
    interested_files = [
        "Retail.CartItems.1.csv",
        "Digital Items.csv",
        "Retail.OrderHistory.1.csv",
        "Retail.OrderHistory.2.csv",
        "Audible.PurchaseHistory.csv",
        "Audible.Library.csv",
        "Audible.MembershipBillings.csv",
        "PrimeVideo.ViewingHistory.csv",
    ]
    
    column_modifications = {
        "Digital Items.csv": [
            "ShipFrom",
            "ShipTo",
        ],
        "Retail.OrderHistory.1.csv": {
            "Shipping Address",
            "Billing Address",
        },
        "Retail.OrderHistory.2.csv": {
            "Shipping Address",
            "Billing Address",
        },
    }
    
    with zipfile.ZipFile(input_zip_path, 'r') as original_zip:
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            for file_name in original_zip.namelist():
                # if a file is an interested file, add it to output zip file
                for interested_file in interested_files:
                    if file_name.endswith(interested_file):
                        with original_zip.open(file_name) as file_data:
                            if not interested_file in column_modifications:
                                new_zip.writestr(interested_file, file_data.read())
                            else:
                                csv_content = file_data.read().decode("utf-8")  # Read CSV as text
                                df = pd.read_csv(io.StringIO(csv_content))  # Convert to DataFrame

                                # Modify the necessary columns
                                for col in column_modifications[interested_file]:
                                    if col in df.columns:
                                        df[col] = await get_postal_codes(df[col])

                                # Write the modified CSV back to ZIP
                                csv_buffer = io.StringIO()
                                df.to_csv(csv_buffer, index=False)
                                new_zip.writestr(interested_file, csv_buffer.getvalue())
                                
                            break  # Stop checking once a match is found

async def download_and_modify_zip(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status == 200:
                    # measure download time
                    start_time = time.time()
                    # Create temporary files to store the ZIPs
                    async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as temp_input:
                        async for chunk in resp.content.iter_chunked(4096):
                            await temp_input.write(chunk)

                    temp_output = tempfile.NamedTemporaryFile(delete=False)
                    temp_output.close()  # Close file so it can be modified

                    end_time = time.time()
                    print(f"File size: {os.path.getsize(temp_input.name) / 1024 / 1024} MB")
                    print(f"Download time: {end_time - start_time} seconds")

                    # Modify the ZIP file
                    start_time = time.time()
                    await modify_zip(temp_input.name, temp_output.name)
                    end_time = time.time()
                    print(f"Modify zip time: {end_time - start_time} seconds")

                    # measure hash time
                    start_time = time.time()
                    # Compute the hash of the modified ZIP
                    hash_obj = hashlib.sha3_256()
                    async with aiofiles.open(temp_output.name, "rb") as modified_file:
                        while chunk := await modified_file.read(4096):
                            hash_obj.update(chunk)
                    end_time = time.time()
                    print(f"Hash time: {end_time - start_time} seconds")

                    # Cleanup temp files
                    os.remove(temp_input.name)

                    return hash_obj.hexdigest(), temp_output.name
                
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
