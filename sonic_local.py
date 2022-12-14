import asyncio
from asyncio.exceptions import TimeoutError as ConnectionTimeoutError
import base64
import websockets
import json
import ssl
import logging

logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# USER TO PROVIDE FOLLOWING VARIABLES
username = "EnterUsernameFromSignalSettingsInTheSonicApp"
password = "EnterPasswordFromSignalSettingsInTheSonicApp"
ip_address = "Find your ip address on your local network"  # e.g "192.168.1.12"

port = 443
uri = f"wss://{ip_address}:{port}"
TIMEOUT = 20


async def sonic_connect():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # ssl_context.create_default_https_context = ssl._create_unverified_context

    user_pass = f"{username}:{password}"
    headers = {'Authorization': f"Basic {base64.b64encode(user_pass.encode()).decode()}"}

    # prints for debugging
    print(f"{uri}")
    print(f"{headers}")
    print(f"{ssl_context}")

    try:
        # Try connection attempt
        connection = await asyncio.wait_for(websockets.connect(uri,
                                                               extra_headers=headers,
                                                               ssl=ssl_context), TIMEOUT)
        # If success
        async with websockets.connect(uri, extra_headers=headers, ssl=ssl_context) as websocket:
            await websocket.send(json.dumps({"event": "requestTelemetry"}))
            response = await websocket.recv()
            print(f"{response}")
    except ConnectionTimeoutError as e:
        print({repr(e)})
        print("Connection Timeout Error")
    except ConnectionResetError as f:
        print({repr(f)})
        print("Connection Reset Error")
    except Exception as g:
        print("unknown error")
        print({repr(g)})


if __name__ == "__main__":
    asyncio.run(sonic_connect())
