<!-- PROJECT LOGO -->
<br />
<div align="center">
    <table>
    <tr> 
      <td align="center">
        <a href="https://enclaive.io/products/python">
          <img alt="python-sgx" height=64px src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">
        </a>
        <br>Python-SGX</td>     
      </td>  
    </tr>
    </table>


  <h2 align="center">Python-SGX: Execute Python applications in the safest Confidential Compute runtime</h2>

  <p align="center">
    <h3>packed by <a href="https://enclaive.io">enclaive</a></h3>
    </br>
    #intelsgx #confidentialcompute #python
    <br />
    <a href="#contributing">Contribute</a>
    ·
    <a href="https://github.com/enclaive/enclaive-docker-python-sgx/issues">Report Bug</a>
    ·
    <a href="https://github.com/enclaive/enclaive-docker-python-sgx/issues">Request Feature</a>
  </p>
</div>

<!-- TL;DR --> 
## TL;DR

```sh
docker pull enclaive/python-sgx
docker-compose up -d
```

**Note**: This quick setup includes a sample Python application that runs a secure key-value database with a FastAPI server.

<!-- INTRODUCTION -->
## What is Python and SGX?

> Python is a dynamically-typed garbage-collected programming language developed by Guido van Rossum in the late 80s to replace ABC. Much like the programming language Ruby, Python was designed to be easily read by programmers. Because of its large following and many libraries, Python can be implemented and used to do anything from webpages to scientific research.

[Overview of Python](https://www.python.org/)

> Intel Security Guard Extension (SGX) delivers advanced hardware and RAM security encryption features, so-called enclaves, in order to isolate code and data that are specific to each application. When data and application code run in an enclave, additional security, privacy, and trust guarantees are given, making the container an ideal choice for (untrusted) cloud environments.

[Overview of Intel SGX](https://www.intel.com/content/www/us/en/developer/tools/software-guard-extensions/overview.html)

<!-- APPLICATION OVERVIEW -->
## Application Overview

This Python application demonstrates a secure key-value database running inside an SGX enclave. It includes a FastAPI server exposed over HTTPS with two endpoints:

- `/generate_proof?link={link}`: Downloads a ZIP file from the provided link, hashes the public link and data using SHA3, stores the hashes in the database, and deletes the data from memory/disk.
- `/get_proof?proof_hash={proof_hash}`: Retrieves the proof corresponding to the provided proof hash from the database.

The application ensures that all operations occur within the secure environment provided by SGX, protecting both the data and the processing logic.

<!-- WHY -->
## Why use Python-SGX (instead of "vanilla" Python) images?

The benefits of running this application within Python-SGX include:

- **Enhanced Security**: Protects the integrity and confidentiality of the Python code, the database, and the data being processed.
- **Data Privacy**: Ensures that sensitive data, such as the downloaded files and computed hashes, remain confidential even in untrusted environments.
- **Regulatory Compliance**: Helps meet technical and organizational measures (TOMs) required by privacy regulations like GDPR and CCPA.

<!-- DEPLOY IN THE CLOUD -->
## How to deploy Python-SGX in a zero-trust cloud?

The application can be deployed on SGX-ready cloud infrastructures like:

- [Microsoft Azure Confidential Cloud](https://azure.microsoft.com/en-us/solutions/confidential-compute/)
- [OVH Cloud](https://docs.ovh.com/ie/en/dedicated/enable-and-use-intel-sgx/)
- [Alibaba Cloud](https://www.alibabacloud.com/blog/alibaba-cloud-released-industrys-first-trusted-and-virtualized-instance-with-support-for-sgx-2-0-and-tpm_596821)
- [Kraud Cloud](https://kraud.cloud/)

<!-- GETTING STARTED -->
## Getting started

### Platform requirements

Ensure your hardware supports Intel SGX:

```sh
grep sgx /proc/cpuinfo
```

### Software requirements

Install the Docker engine:

```sh
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker $USER
```

<!-- GET THIS IMAGE -->
## Get this image

Pull the prebuilt image from the Docker Hub Registry:

```console
docker pull enclaive/python-sgx:latest
```

<!-- BUILD THE IMAGE -->
## Build the image

To build the image yourself, clone the repository and build:

```console
git clone https://github.com/enclaive/enclaive-docker-python-sgx.git
cd enclaive-docker-python-sgx
docker build -t enclaive/python-sgx:latest .
```

## Application Details

The application code is located in the `/app/` directory. It consists of:

- **main.py**: The main FastAPI application.
- **database.py**: The database setup using SQLite.
- **models.py**: The data models for the database.
- **schemas.py**: The Pydantic models for request and response validation.
- **requirements.txt**: The Python dependencies.

### main.py

```python
from fastapi import FastAPI, HTTPException, Query
import hashlib
import aiohttp
import asyncio
import os
from database import SessionLocal, engine
import models
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/submit_proof")
async def submit_proof(link: str = Query(...)):
    link_hash = hashlib.sha3_256(link.encode('utf-8')).hexdigest()
    data_hash = await download_and_hash(link)
    if data_hash is None:
        raise HTTPException(status_code=400, detail="Failed to download or hash data.")
    db = next(get_db())
    db_item = models.Proof(proof_hash=link_hash, data_hash=data_hash)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message": "Proof submitted successfully", "link_hash": link_hash}

@app.get("/query_proof")
def query_proof(link_hash: str = Query(...)):
    db = next(get_db())
    data = db.query(models.Proof).filter(models.Proof.proof_hash == link_hash).first()
    if data:
        return {"data_hash": data.data_hash}
    else:
        raise HTTPException(status_code=404, detail="Proof not found.")

async def download_and_hash(url):
    temp_file = "temp_download.zip"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    data_hash = hashlib.sha3_256(content).hexdigest()
                    return data_hash
    except Exception as e:
        print(f"Error downloading or hashing data: {e}")
        return None
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
```

### database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./proofs.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

### models.py

```python
from sqlalchemy import Column, String
from database import Base

class Proof(Base):
    __tablename__ = "proofs"

    proof_hash = Column(String, primary_key=True, index=True)
    data_hash = Column(String, index=True)
```

### requirements.txt

```
fastapi
uvicorn
aiohttp
sqlalchemy
```

<!-- RUN THE IMAGE -->
## Run the image

Start the enclaved Python application:

```sh
docker-compose up -d
```

The application will be accessible over HTTPS at `https://<your-server-address>:8000`.

<!-- USAGE EXAMPLES -->
## Usage

### Submit a Proof

To submit a proof, send a GET request to `/submit_proof` with the `link` parameter:

```sh
curl -X GET "https://<your-server-address>:8000/submit_proof?link=https://example.com/data.zip" -k
```

### Query a Proof

To query a proof, send a GET request to `/query_proof` with the `link_hash` parameter:

```sh
curl -X GET "https://<your-server-address>:8000/query_proof?link_hash=<link_hash>" -k
```

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<!-- SUPPORT -->
## Support

Don't forget to give the project a star! Spread the word on social media! Thanks again!

<!-- LICENSE -->
## License

Distributed under the Apache 2.0 License. See `LICENSE` for further information.

<!-- CONTACT -->
## Contact

enclaive.io - [@enclaive_io](https://twitter.com/enclaive_io) - contact@enclaive.io - [https://enclaive.io](https://enclaive.io)

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

This project greatly celebrates all contributions from the Gramine team. Special shout out to [Dmitrii Kuvaiskii](https://github.com/dimakuv) from Intel for his support.

- [Gramine Project](https://github.com/gramineproject)
- [Intel SGX](https://github.com/intel/linux-sgx-driver)
- [Python](https://www.python.org/)

## Trademarks

This software listing is packaged by enclaive.io. The respective trademarks mentioned in the offering are owned by the respective companies, and use of them does not imply any affiliation or endorsement.

---

*Note: This application securely processes and stores proofs within an SGX enclave, ensuring that sensitive data remains confidential and tamper-proof.*