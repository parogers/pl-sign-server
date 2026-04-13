#!/usr/bin/env python3

import time
import json
import asyncio
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


class State:
    version: int = 0
    message: str = ''
    sign_clients: set

    def __init__(self):
        self.sign_clients = set()

state = State()


class PostMessage(BaseModel):
    content: str


app = FastAPI()
app.mount('/static/', StaticFiles(directory='static'), name='static')

CORS_ORIGINS = [
    'http://localhost:5173',
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get("/")
def index():
    return RedirectResponse('/static/index.html')


@app.post('/message/')
def post_message(message: PostMessage):
    state.message = message.content
    state.version += 1
    return message


@app.get('/message/')
def get_message():
    return state.message


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, sign: bool | None = None):
    if sign:
        print('Sign has connected')
        state.sign_clients.add(id(websocket))
        state.version += 1
    await websocket.accept()
    last_version = -1
    last_ping = 0
    while True:
        try:
            # TODO - replace this with a queue/notification system
            if state.version != last_version:
                payload = {
                    'message' : state.message + '       ',
                    'sign_connected' : bool(state.sign_clients),
                }
                await websocket.send_json(payload)
                last_version = state.version
            # TODO - hack
            await asyncio.sleep(0.25)
            if time.time() - last_ping >= 5:
                await websocket.send_text('')
                last_ping = time.time()
        except WebSocketDisconnect:
            break
    if sign:
        print('Sign has disconnected')
        state.sign_clients.remove(id(websocket))
        state.version += 1
