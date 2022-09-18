import sys
import websockets
import ssl
import asyncio as aio
import json

from base64 import b64encode
from typing import Literal
import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class SonicWebsocketListener(object):

    def __init__(
            self,
            host: str,
            username: str,
            password: str,
    ):
        self.host = host
        self.username = username
        self.password = password
        # self.logger = getLogger(name=f'Sonic-{self.host}')
        # self.logger.info("Incoming messages will be echoed to stdout")
        self.extra_headers: dict = self.get_auth_header()
        self.ssl_context: ssl.SSLContext = self.get_ssl_context()

    def get_auth_header(self) -> dict:
        username, password = [x.encode('latin1') for x in (self.username, self.password)]
        encoded_user_pass = b64encode(b':'.join([username, password])).strip().decode('ascii')
        return {"Authorization": f"Basic {encoded_user_pass}"}

    def get_ssl_context(self) -> ssl.SSLContext:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    def write_output(self, of, data):
        if isinstance(data, str):
            of.write(f"{data}\n")
        elif isinstance(data, dict):
            of.write(f"{json.dumps(data)}\n")
        else:
            raise TypeError(f"Expected str or dict, got {type(data)} instead.")

    def echo_output(self, data):
        if isinstance(data, str) or not isinstance(data, dict):
            print(data)
        else:
            print(f"{json.dumps(data, indent=2)}")

    async def message_handler(self, connection: websockets.WebSocketClientProtocol):
        async for message in connection:
            try:
                data = json.loads(message)
                self.logger.debug(f"Received JSON message:>> {message}")
                self.echo_output(data=data)
            except Exception as e:
                self.logger.error(f"Cannot parse message: {message}. Exception: {repr(e)}")

    async def consume(self, event: Literal["requestTelemetry", "requestState"]):
        print("Line 63 - In the consume function")
        websocket_resource_url = f"wss://{self.host}"
        print("Line 65 - websocket_resource_url:", websocket_resource_url)
        try:
            print("Line 67, Extra Headers are: ",self.extra_headers)
            print("Line 68, Event topic is: ",event)
            async with websockets.connect(uri=websocket_resource_url,
                                          ssl=self.ssl_context,
                                          extra_headers=self.extra_headers) as connection:
                transmit_msg = json.dumps({"event": {event}})
                print(transmit_msg)
                await connection.send(transmit_msg)
                while True:
                    print("77")
                if connection.open:
                    print("connection.open - line 75")
                    self.logger.info("Connection established.")
                else:
                    print("connection.closed - line 80")
                    self.logger.error("Failed to establish connection.")

                await self.message_handler(connection=connection)
        except websockets.exceptions.InvalidStatusCode as e:
            if "HTTP 401" in repr(e):
                self.logger.error("Received HTTP 401 Unauthorized. Check your credentials.")
                sys.exit(1)
        except Exception as f:
            print("Line 90 - Unknown exception thrown")
            print({repr(f)})
            sys.exit(1)

    def run(self, event: Literal["requestTelemetry", "requestState"]):
        try:
            print("Line 95 - run function - try statement launches consume loop")
            aio.get_event_loop().run_until_complete(self.consume(event=event))
            print("Line 97 - run function - try statement run loop forever")
            aio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            self.logger.info("Received KeyboardInterrupt, Closing Connection")
        finally:
            print("Line 102 - Run function - finally statement")


def main():
    client = SonicWebsocketListener(host="my_ip_address:443", username="myusername", password="mypassword")
    client.run(topic="requestState")


if __name__ == '__main__':
    main()
