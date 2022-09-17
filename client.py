import sys
import websockets
import ssl
import asyncio as aio
import pathlib
import json

from base64 import b64encode
from logging import getLogger
from typing import Literal


class SonicWebsocketListener(object):

    def __init__(
            self,
            host: str,
            username: str,
            password: str,
            output_file: pathlib.Path = pathlib.Path().cwd().joinpath("sonic_output"),
            echo: bool = False,
            verbosity=4
            ):
        self.host = host
        self.logger = getLogger(name=f'Sonic-{self.host}', verbosity=verbosity)
        self.username = username
        self.password = password
        self.output_file = pathlib.Path(output_file)
        self.logger.info(f"Incoming messages will be writen to {str(self.output_file)}")
        self.echo = echo
        if self.echo:
            self.logger.info("Incoming messages will be echoed to stdout")
        else:
            self.logger.info("Incoming messages will NOT be echoed to stdout")
        self.extra_headers: dict = self.get_auth_header()
        self.ssl_context: ssl.SSLContext = self.get_ssl_context()
        self.counters = {
            'received_total': 0,
            'received_ok': 0,
            'received_error': 0,
            'received_heartbeat': 0
        }

    def get_auth_header(self) -> dict:
        username, password = [x.encode('latin1') for x in (self.username, self.password)]
        encoded_user_pass = b64encode(b':'.join([username, password])).strip().decode('ascii')
        headers = {
            "Authorization": f"Basic {encoded_user_pass}"
        }
        return headers

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

    def update_counter_ok(self):
        self.counters['received_total'] += 1
        self.counters['received_ok'] += 1

    def update_counter_error(self):
        self.counters['received_total'] += 1
        self.counters['received_error'] += 1

    def update_counter_heartbeat(self):
        self.counters['received_total'] += 1
        self.counters['received_heartbeat'] += 1

    def echo_output(self, data):
        if isinstance(data, str):
            print(data)
        elif isinstance(data, dict):
            print(f"{json.dumps(data, indent=2)}")
        else:
            print(data)

    async def message_handler(self, connection: websockets.WebSocketClientProtocol):
        with self.output_file.open(mode="a") as of:
            async for message in connection:
                try:
                    data = json.loads(message)
                    self.logger.debug(f"Received JSON message:>> {message}")
                    self.update_counter_ok()
                    self.write_output(of=of, data=data)
                    if self.echo is True:
                        self.echo_output(data=data)
                except Exception as e:
                    if message == "X":
                        self.logger.info("Received heartbeat message ('X')")
                    else:
                        self.update_counter_error()
                        self.logger.error(f"Cannot parse message: {message}. Exception: {repr(e)}")

    async def consume(self, event: Literal['requestTelemetry', 'requestState']):
        websocket_resource_url = f"wss://{self.host}"
        try:
            async with websockets.connect(uri=websocket_resource_url,
                                          ssl=self.ssl_context,
                                          extra_headers=self.extra_headers) as connection:
                if connection.open:
                    self.logger.info("Connection established.")
                    transmit_msg = {"event": {event}}
                    connection.send(json.dumps(transmit_msg))
                else:
                    self.logger.error("Failed to establish connection.")

                await self.message_handler(connection=connection)
        except websockets.exceptions.InvalidStatusCode as e:
            if "HTTP 401" in repr(e):
                self.logger.error("Received HTTP 401 Unauthorized. Check your credentials.")
                sys.exit(1)

    def run(self, event: Literal['requestTelemetry', 'requestState']):
        try:
            aio.get_event_loop().run_until_complete(self.consume(event=event))
            aio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            self.logger.info("Received KeyboardInterrupt, Closing Connection")
        finally:
            print(f"Stats: {self.counters}")


def main():
    client = SonicWebsocketListener(host="my_ip_address:443", username="myusername", password="mypassword")
    client.run(topic="requestState")


if __name__ == '__main__':
    main()
