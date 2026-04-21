#!/usr/bin/env python3

import time
import json
import asyncio
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware


class State:
    version: int = 0
    message: str = 'Server ready'
    sign_clients: set
    messages_by_client_id: dict

    def __init__(self):
        self.sign_clients = set()
        self.messages_by_client_id = {}
        self.timestamp_by_client_id = {}

    def set_message(self, msg, client_id):
        self.message = msg
        self.messages_by_client_id[client_id] = msg
        self.timestamp_by_client_id[client_id] = time.time()
        self.version += 1

    def has_changed(self, old_version):
        return self.version != old_version

    def add_sign_client(self, websocket):
        self.sign_clients.add(id(websocket))

    def remove_sign_client(self, websocket):
        self.sign_clients.remove(id(websocket))


state = State()


class PostMessage(BaseModel):
    content: str
    client_id: str


app = FastAPI()

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


@app.get("/")
def index():
    return ''


@app.post('/message/')
def post_message(message: PostMessage):
    state.set_message(message.content, client_id=message.client_id)
    return message


@app.get('/message/')
def get_message():
    return state.message


def make_payload(include_message=True):
    payload = {
        'sign_connected' : bool(state.sign_clients),
    }
    if include_message:
        # payload['message'] = state.message + '       '
        messages = [
            msg
            for client_id, msg in reversed(sorted(
                state.messages_by_client_id.items(),
                key=lambda args: state.timestamp_by_client_id[args[0]]
            ))
        ]
        payload['messages'] = messages
        payload['message'] = ''.join([
            f'{msg:13}' + '<FP><FI><FS>'
            for msg in messages
        ])
        print(messages)
    return payload


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
                    await websocket.send_json(make_payload(include_message=False))
                    last_ping = time.time()
            await asyncio.sleep(0.25)
        except WebSocketDisconnect:
            break
    if sign:
        print('Sign has disconnected')
        state.remove_sign_client(websocket)
        state.version += 1
