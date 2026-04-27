#!/usr/bin/env python3

import time
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from model import State
from routes import router


app = FastAPI()
app.include_router(router)

CORS_ORIGINS = [
    'http://localhost:5173',
    'http://studio.local:5173',
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
