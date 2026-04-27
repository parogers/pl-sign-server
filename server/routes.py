
import asyncio
import time
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import WebSocket, WebSocketDisconnect

from model import Message, State


router = APIRouter()


class PostMessage(BaseModel):
    name: str
    content: str
    client_id: str


def make_message_payload(message: Message):
    return {
        "id" : message.id,
        "name" : message.client_name,
        "content" : message.content,
    }


def make_payload(include_message=True):
    payload = {
        'sign_connected' : bool(State.state.sign_clients),
    }
    if include_message:
        def _fmt_message(msg):
            if msg.client_name:
                content = f'{msg.client_name} says: {msg.content}'
            else:
                content = msg.content
            return content

        messages = [
            State.state.messages_by_client_id[client_id]
            for client_id in reversed(sorted(
                State.state.messages_by_client_id,
                key=lambda client_id: State.state.messages_by_client_id[client_id].timestamp
            ))
        ]
        payload['messages'] = [
            make_message_payload(msg)
            for msg in messages
        ]
        payload['message'] = ''.join([
            f'{_fmt_message(msg)}             '
            for msg in messages
        ])
        # # Delay, scroll up, scroll left for each message
        # payload['message'] = ''.join([
        #     f'<FP><FI><FS>{msg:13}'
        #     for msg in messages
        # ])
    return payload


@router.delete('/message/{id}')
def delete_msg(id: str):
    State.state.remove_message(id)
    return {}


@router.get("/message/")
def index():
    return [
        make_message_payload(msg)
        for msg in State.state.messages_by_client_id.values()
    ]


@router.get("/")
def index():
    return ''


@router.post('/message/')
def post_message(message: PostMessage):
    msg = State.state.set_message(
        msg=message.content,
        client_id=message.client_id,
        name=message.name,
    )
    return make_message_payload(msg)


@router.websocket("/ws/")
async def websocket_endpoint(websocket: WebSocket, sign: bool | None = None):
    if sign:
        print('Sign has connected')
        State.state.add_sign_client(websocket)
    await websocket.accept()
    last_version = -1
    last_ping = 0
    while True:
        try:
            # TODO - replace this with a queue/notification system
            if State.state.has_changed(last_version):
                await websocket.send_json(make_payload())
                last_version = State.state.version
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
        State.state.remove_sign_client(websocket)
        State.state.version += 1
