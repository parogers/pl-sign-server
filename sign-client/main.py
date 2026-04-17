#!/usr/bin/env python3

import sys
import socket
import json
import time
import asyncio
from websockets.sync.client import connect
from websockets.exceptions import (
    ConnectionClosedError,
    InvalidMessage,
    InvalidStatus,
)
from serial import SerialException

import site
site.addsitedir('../py-pl-m2014r')
from plm2014r import Sign, NoResponse


async def serve(host, port=8000):
    sign = Sign('/dev/ttyUSB0', retries=20)
    sign.wakeup()
    with connect(f'ws://{host}:{port}/ws/?sign=true') as websocket:
        print('Connected')
        sign.set_message('<FC>Connected')
        time.sleep(2)
        while True:
            data = websocket.recv()
            payload = json.loads(data)
            try:
                message = payload['message']
                sign.set_message(message)
            except KeyError:
                sign.wakeup()


async def main():
    try:
        host = sys.argv[1]
    except IndexError:
        host = 'localhost'
    while True:
        try:
            await serve(host)
        except NoResponse:
            print('Sign not responding... retrying')
        except (ConnectionClosedError, InvalidMessage):
            print('Connection closed... re-connecting')
        except (ConnectionRefusedError, TimeoutError, InvalidStatus, socket.gaierror):
            print('Could not reach server... retrying')
        except (FileNotFoundError, SerialException):
            print('Could not find serial device... retrying')
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
