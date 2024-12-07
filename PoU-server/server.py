import os
import uvicorn
import logging
import argparse
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes import minhash_routes
from routes.minhash_routes import lsh, db_manager

load_dotenv()

app = FastAPI(
    title="PrimeInsights Proof of Uniqueness DatabaseAPI",
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_debug_middleware():
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.debug(f"Request: {request.method} {request.url}")
        logger.debug(f"Headers: {request.headers}")
        
        try:
            body = await request.body()
            if body:
                logger.debug(f"Body: {body.decode()}")
        except Exception:
            pass

        response = await call_next(request)
        logger.debug(f"Response status: {response.status_code}")
        return response

@app.middleware("http")
async def check_authentication(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    api_key = request.headers.get('x-api-key')
    if not api_key or api_key != os.getenv("API_KEY"):
        logger.warning(f"Failed authentication attempt from {request.client.host}")
        return Response("403 Forbidden", status_code=403)
    return await call_next(request)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        for id, user_id, minhash in db_manager.get_all_entries():
            key = f"{user_id}_{id}"
            lsh.insert(key, minhash)
        logger.info("Successfully loaded LSH index")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize LSH index: {e}")
        raise
    finally:
        logger.info("Shutting down application")

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(minhash_routes.router, tags=["minhash"])

@app.get("/")
async def root():
    return f"Welcome to the Proof of Uniqueness API. Connection time: {datetime.now()}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proof of Uniqueness API")
    parser.add_argument('--port', type=int, default=int(os.getenv("PORT", "8123")), 
                       help='Port to run the API on')
    parser.add_argument('--host', type=str, default='0.0.0.0', 
                       help='Host to run the API on')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug logging')
    parser.add_argument('--use-https', action='store_true',
                       help='Enable HTTPS (requires SSL certificates)')
    parser.add_argument('--ssl-keyfile', type=str, 
                       help='Path to SSL key file')
    parser.add_argument('--ssl-certfile', type=str, 
                       help='Path to SSL certificate file')
    args = parser.parse_args()
    
    log_level = "DEBUG" if args.debug else "INFO"
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    if args.debug:
        create_debug_middleware()
        logger.debug("Debug logging enabled")
    
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    ssl_config = {}
    if args.use_https:
        if not (args.ssl_keyfile and args.ssl_certfile):
            logger.error("SSL certificates required when --use-https is enabled")
            exit(1)
        ssl_config.update({
            'ssl_keyfile': args.ssl_keyfile,
            'ssl_certfile': args.ssl_certfile
        })
        logger.info(f"HTTPS enabled with cert: {args.ssl_certfile}")
    else:
        logger.info("Running in HTTP mode")
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port, 
        log_level=log_level.lower(),
        log_config=log_config,
        **ssl_config
    )