#!/usr/bin/env python3

from urllib.parse import urlparse
import argparse
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


def make_ws_url(server_url):
    parsed = urlparse(server_url)
    ws_scheme = ''
    if parsed.scheme == 'http':
        ws_scheme = 'ws'
    elif parsed.scheme == 'https':
        ws_scheme = 'wss'
    else:
        raise Exception(f'unknown scheme: {server_url}')

    url = f'{ws_scheme}://{parsed.netloc}/{parsed.path}'
    if not url.endswith('/'):
        url += '/'
    url += 'ws/?sign=true'
    return url


async def serve(server_url):

    with connect(make_ws_url(server_url)) as websocket:
        sign = Sign('/dev/ttyUSB0', retries=20)
        sign.wakeup()
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
    parser = argparse.ArgumentParser(description='Pulls messages from a sign server and drives a PL sign via USB')
    parser.add_argument(
        '--url',
        type=str,
        nargs=1,
        required=False,
        default=['http://localhost:8000'],
    )
    args = parser.parse_args(sys.argv[1:])
    url = args.url[0]
    while True:
        try:
            await serve(url)
        except NoResponse:
            print('Sign not responding... retrying')
        except (ConnectionClosedError, InvalidMessage, ConnectionError):
            print('Connection closed... re-connecting')
        except (ConnectionRefusedError, TimeoutError, InvalidStatus, socket.gaierror):
            print('Could not reach server... retrying')
        except (FileNotFoundError, SerialException):
            print('Could not find serial device... retrying')
        time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
