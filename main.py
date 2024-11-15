
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
import aiofiles
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form, Response, status, Depends
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from config import ADMIN_PASSWORD, MAX_FILE_SIZE, STORAGE_CHANNEL
from utils.clients import initialize_clients
from utils.directoryHandler import getRandomID
from utils.extra import auto_ping_website, convert_class_to_dict, reset_cache_dir
from utils.streamer import media_streamer
from utils.logger import Logger
import urllib.parse
import logging
import re
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from base64 import standard_b64encode, standard_b64decode
import jwt
import time
import secrets
import httpx

from bson import ObjectId
import os

import math
from urllib.parse import urlparse
# Startup Event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reset the cache directory, delete cache files
    reset_cache_dir()

    # Initialize the clients
    await initialize_clients()

    # Start the website auto ping task
    asyncio.create_task(auto_ping_website())

    yield


app = FastAPI(docs_url=None, redoc_url=None, lifespan=lifespan)
logger = Logger(__name__)
SECRET_KEY = "JHNCA8ER3NbjfCHSA89KJASCAxnjks"

@app.get("/file")
async def dl_file(request: Request):
    from utils.directoryHandler import DRIVE_DATA

    user_agent = request.headers.get("User-Agent", "")
    if "bot" in user_agent.lower() or "crawler" in user_agent.lower():
        raise HTTPException(status_code=403, detail="Bot activity detected. Download blocked.")

    #path = request.query_params.get("download")
    hash = request.query_params.get("hash")

    if not hash:
        raise HTTPException(status_code=400, detail="Missing parameters")

    try:
        payload = jwt.decode(hash, SECRET_KEY, algorithms=["HS256"])
        path = payload.get("path")
        # if payload.get("path") != path:
           # raise HTTPException(status_code=403, detail="Invalid path in token")

        file = DRIVE_DATA.get_file(path)
        if file:
            return await media_streamer(STORAGE_CHANNEL,file.file_id, file.name, request)
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")
