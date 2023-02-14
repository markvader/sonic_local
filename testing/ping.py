import asyncio
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
delay = 1


async def ping():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # ssl_context.create_default_https_context = ssl._create_unverified_context

    user_pass = f"{username}:{password}"
    headers = {'Authorization': f"Basic {base64.b64encode(user_pass.encode()).decode()}"}
    # Note: Connection & Upgrade headers already included in websockets.connect(), therefore likely not needed

    # prints for debugging
    print(f"{uri}")
    print(f"{headers}")
    print(f"{ssl_context}")

    try:
        async with websockets.connect(uri, extra_headers=headers, ssl=ssl_context) as websocket:
            await websocket.send(json.dumps({"event": "ping"}))
            pong = await websocket.recv()
            print(f"Successfully connected to {uri}, response to ping: {pong}")

            await asyncio.sleep(delay)
            await websocket.send('ping')
            pong = await websocket.recv()
            print(f"Maintained connection to {uri}, response to ping: {pong}")
            print("Success!")

    except (RuntimeError, websockets.exceptions.ConnectionClosed) as e:
        print(e.args)
    except (websockets.exceptions.InvalidStatusCode, ConnectionResetError, websockets.exceptions.InvalidMessage) as e:
        print('Connection to Signal device was unsuccessful:', e)
        print(e.args)


if __name__ == "__main__":
    asyncio.run(ping())
