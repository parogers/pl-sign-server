#!/usr/bin/env python3

import json
import time
import asyncio
from websockets.asyncio.client import connect
from websockets.exceptions import (
    ConnectionClosedError,
    InvalidMessage,
)
from serial import SerialException

import site
site.addsitedir('../py-pl-m2014r')
from plm2014r import Sign, NoResponse


async def serve():
    sign = Sign('/dev/ttyUSB0', retries=20)
    sign.wakeup()
    async with connect("ws://localhost:8000/ws/?sign=true") as websocket:
        sign.set_message('<FC>Connected')
        time.sleep(2)
        while True:
            data = await websocket.recv()
            payload = json.loads(data)
            try:
                message = payload['message']
                sign.set_message(message)
            except KeyError:
                sign.wakeup()


async def main():
    while True:
        try:
            await serve()
        except NoResponse:
            print('Sign not responding... retrying')
        except (ConnectionClosedError, InvalidMessage):
            print('Connection closed... re-connecting')
        except (ConnectionRefusedError, TimeoutError):
            print('Could not reach server... retrying')
        except (FileNotFoundError, SerialException):
            print('Could not find serial device... retrying')
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
