
import time
from dataclasses import dataclass


@dataclass
class Message:
    id: int
    client_id: int
    client_name: str
    content: str
    timestamp: int


class State:
    _state: 'State' = None
    version: int = 0
    sign_clients: set
    messages_by_client_id: dict
    timestamp_by_client_id: dict
    names_by_client_id: dict

    def __init__(self):
        self.sign_clients = set()
        self.messages_by_client_id = {}

    def set_message(self, msg, name, client_id):
        msg = Message(
            id=client_id,
            client_id=client_id,
            client_name=name,
            content=msg,
            timestamp=time.time(),
        )
        self.messages_by_client_id[client_id] = msg
        self.version += 1
        return msg

    def remove_message(self, client_id):
        try:
            del self.messages_by_client_id[client_id]
            self.version += 1
        except KeyError:
            pass

    def has_changed(self, old_version):
        return self.version != old_version

    def add_sign_client(self, websocket):
        self.sign_clients.add(id(websocket))

    def remove_sign_client(self, websocket):
        self.sign_clients.remove(id(websocket))

    @classmethod
    @property
    def state(cls):
        if not cls._state:
            cls._state = State()
        return cls._state
