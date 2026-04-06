#!/usr/bin/env python3

import json
import time
import asyncio
from websockets.asyncio.client import connect
from websockets.exceptions import (
    ConnectionClosedError,
    InvalidMessage,
)

import site
site.addsitedir('../py-pl-m2014r')
from plm2014r import Sign, NoResponse


async def serve():
    async with connect("ws://localhost:8000/ws/?sign=true") as websocket:
        sign = Sign('/dev/ttyUSB0', retries=20)
        sign.wakeup()
        sign.set_message('<FC>Connected')
        time.sleep(2)
        while True:
            data = await websocket.recv()
            if not data:
                # Ping event
                continue
            payload = json.loads(data)
            print('message update:', payload)
            sign.set_message(payload['message'])


async def main():
    while True:
        try:
            await serve()
        except NoResponse:
            print('Sign not responding... retrying')
            time.sleep(1)
        except (ConnectionClosedError, InvalidMessage):
            print('Connection closed... re-connecting')
            time.sleep(1)
        except ConnectionRefusedError:
            print('Could not reach server... retrying')
            time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
