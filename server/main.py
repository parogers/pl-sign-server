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

    def set_message(self, msg):
        self.message = msg
        self.version += 1

    def has_changed(self, old_version):
        return self.version != old_version

    def add_sign_client(self, websocket):
        self.sign_clients.add(id(websocket))
        self.version += 1

    def remove_sign_client(self, websocket):
        self.sign_clients.remove(id(websocket))
        self.version += 1


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
    state.set_message(message.content)
    return message


@app.get('/message/')
def get_message():
    return state.message



def make_payload():
    return {
        'message' : state.message + '       ',
        'sign_connected' : bool(state.sign_clients),
    }


@app.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, sign: bool | None = None):
    if sign:
        print('Sign has connected')
        state.add_sign_client(websocket)
    await websocket.accept()
    last_version = -1
    last_ping = 0
    while True:
        try:
            # TODO - replace this with a queue/notification system
            if state.has_changed(last_version):
                await websocket.send_json(make_payload())
                last_version = state.version
            else:
                # TODO - hack
                if time.time() - last_ping >= 5:
                    await websocket.send_json(make_payload())
                    last_ping = time.time()
            await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            break
    if sign:
        print('Sign has disconnected')
        state.remove_sign_client(websocket)
        state.version += 1
