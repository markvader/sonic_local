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
username = "ENTERusernameFROMsignalSETTINGSinTHEsonicAPP"
password = "ENTERpasswordFROMsignalSETTINGSinTHEsonicAPP"
ip_address = "find your ip address on your local network" # e.g "192.168.1.12"


port = 443
uri = f"wss://{ip_address}:{port}"


async def sonic_connect():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    # ssl_context.create_default_https_context = ssl._create_unverified_context

    user_pass = f"{username}:{password}"
    headers = {'Authorization': f"Basic {base64.b64encode(user_pass.encode()).decode()}"}
    # Following headers already included in websockets.connect(), therefore not needed
    # headers['Connection'] = 'Upgrade'
    # headers['Upgrade'] = 'websocket'

    print(f"{uri}")
    print(f"{headers}")
    print(f"{ssl_context}")

    async with websockets.connect(uri, extra_headers=headers, ssl=ssl_context) as websocket:
        await websocket.send(json.dumps({"event": "requestTelemetry"}))
        response = await websocket.recv()
        print(f"{response}")

if __name__ == "__main__":
    asyncio.run(sonic_connect())
