import json
import os
import sys
import base64
import asyncio
import aiohttp
from aiohttp import WSMsgType
from datetime import datetime
from icecream import ic
import logging

from exception import (
    SonicWebsocketError,
    SonicWSConnectionError,
    Unauthorized
)

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout
else:
    from asyncio import timeout as asyncio_timeout

_LOGGER = logging.getLogger(__name__)

data_folder = "data_folder"
os.makedirs(data_folder, exist_ok=True)


class WebSocketClient:
    """Sonic websocket handler."""

    def __init__(self,
                 host: str,
                 username: str,
                 password: str,
                 session: aiohttp.ClientSession | None = None
                 ) -> None:
        self.uri = f'wss://{host}:443'
        self.username = username
        self.password = password
        self._own_session = not session
        self.session = session or aiohttp.ClientSession()
        self.ws: aiohttp.ClientWebSocketResponse | None = None
        self._connect_lock = asyncio.Lock()
        self.daily_volume = 0
        self.last_reset_datetime = None
        self.last_update = '2023-12-14 00:00:00.000001'
        self.telemetry_json_data = dict()
        self.telemetry_data_file = os.path.join(data_folder, "telemetry_data.json")
        self.daily_volume_data_file = os.path.join(data_folder, "daily_volume.txt")

    def to_base64(self):
        return base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()

    async def connect(self) -> None:
        """Opening a persistent websocket connection."""
        async with self._connect_lock:
            if self.ws and not self.ws.closed:
                _LOGGER.warning("Websocket is already connected")
                return

        _LOGGER.debug("Opening websocket to %s", self.uri)
        headers = {'Authorization': 'Basic ' + self.to_base64()}
        try:
            async with asyncio_timeout(15):
                self.ws = await self.session.ws_connect(
                    self.uri, headers=headers, verify_ssl=False
                )
        except aiohttp.ClientResponseError as exc:
            if exc.status == 401:
                _LOGGER.error("Credentials rejected: %s", exc)
                raise Unauthorized("Credentials rejected") from exc
            raise SonicWSConnectionError(
                f"Unexpected response received: {exc}"
            ) from exc
        except aiohttp.ClientConnectionError as exc:
            raise SonicWSConnectionError(f"Connection error: {exc}") from exc
        except asyncio.TimeoutError as exc:
            raise SonicWSConnectionError("Connection timed out") from exc
        except Exception as exc:  # pylint: disable=broad-except
            raise SonicWSConnectionError(f"Unknown error: {exc}") from exc
        _LOGGER.debug("Successfully connected to %s", self.uri)

    async def close(self):
        """Close the websocket connection."""
        if self.ws and not self.ws.closed:
            await self.ws.close()
        """Close the session."""
        if self._own_session and self.session and not self.session.closed:
            await self.session.close()

    # async def send(self, message):
    #     self.ws.send(message)

    async def receive_data(self):
        """Receive responses/data from the websocket."""
        while True:
            if not self.ws or self.ws.closed:
                await self.connect()
                assert self.ws
            try:
                await self.load_previous_volume_data()
                raw_msg = await self.ws.receive()
                # ic(raw_msg)
                if raw_msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.CLOSING):
                    _LOGGER.debug("Websocket closed, will try again")
                elif raw_msg.type != WSMsgType.TEXT:
                    _LOGGER.error("Received non-text message: %s", raw_msg.type.name)
                else:
                    message = raw_msg.json()
                    if message['event'] == 'telemetry':
                        abs_pressure, ambient_temp, battery_level, flow_rate, leak_status, probed_at, status_str, \
                            telemetry_datetime, time_diff, water_temp = await self.extract_telemetry_data(message)
                        if time_diff < 1440:  # If the last update was less than 24 hours ago
                            await self.calculate_volume(flow_rate, time_diff)
                        await self.save_volume_to_file()
                        daily_volume_ml = round(float(self.daily_volume), 2)
                        self.save_telemetry_data(probed_at, water_temp, abs_pressure, flow_rate, leak_status,
                                                 battery_level, ambient_temp, daily_volume_ml, status_str)
                        await asyncio.sleep(0.5)
                    if message['event'] == 'state':
                        valve_state = message['data']['valve_state']
                        radio_state = message['data']['radio_state']
                        print("data_timestamp:", datetime.now(),
                              "- valve_state:", valve_state,
                              "- radio_state:", radio_state)
            except asyncio.TimeoutError:
                _LOGGER.error("Command timed out")
            except ConnectionResetError:
                # Websocket closing
                self.ws = None
                _LOGGER.debug("Websocket connection reset, will try again")

    async def extract_telemetry_data(self, message):
        probed_at = message['data']['probed_at']  # 1703073823925
        telemetry_datetime = datetime.fromtimestamp(probed_at / 1000.0)  # 2023-12-20 17:16:24.430000
        time_diff = await self.time_since_last_update(telemetry_datetime)
        self.last_update = telemetry_datetime
        flow_rate = message['data']['water_flow']  # 3088.8671875
        leak_status = message['data']['leak_status']  # No Leaks
        status = message['data']['status']  # ['OKAY']
        status_str = ', '.join(status)
        water_temp = message['data']['water_temp']  # 10.4375
        ambient_temp = message['data']['ambient_temp']  # 11.9375
        abs_pressure = message['data']['abs_pressure']  # 4831
        battery_level = message['data']['battery_level']  # okay
        return abs_pressure, ambient_temp, battery_level, flow_rate, leak_status, \
            probed_at, status_str, telemetry_datetime, time_diff, water_temp

    async def load_previous_volume_data(self):
        if self.daily_volume == 0 and os.path.exists(self.daily_volume_data_file):
            with open(self.daily_volume_data_file, "r") as f:
                self.daily_volume = float(f.read())
            print(f"Loaded last volume usage from file: {self.daily_volume}")

    async def save_volume_to_file(self):
        with open(self.daily_volume_data_file, "w") as f:
            f.write(str(self.daily_volume))

    def save_telemetry_data(self, probed_at, water_temp, abs_pressure, flow_rate, leak_status,
                            battery_level, ambient_temp, daily_volume_ml, status_str):
        self.telemetry_json_data = {
            'probed_at': probed_at,
            'water_temp': water_temp,
            'abs_pressure': abs_pressure,
            'flow_rate': flow_rate,
            'leak_status': leak_status,
            'battery_level': battery_level,
            'ambient_temp': ambient_temp,
            'daily_volume_ml': daily_volume_ml,
            'status': status_str
        }
        print(self.telemetry_json_data)
        with open(self.telemetry_data_file, "a") as f:
            json.dump(self.telemetry_json_data, f)
            f.write("\n")

    def seconds_until_midnight(self):
        current_time = datetime.now()

        # Calculate time until the next midnight
        midnight = datetime(current_time.year, current_time.month, current_time.day, 23, 59, 59, 999999)
        time_until_midnight = midnight - current_time

        # Convert the time difference to seconds
        seconds_until_midnight = time_until_midnight.total_seconds()
        result = int(seconds_until_midnight)
        return result

    async def reset_daily_usage(self):
        while True:
            sleep_duration = self.seconds_until_midnight()
            print(round(sleep_duration / 3600, 1), "hours until daily statistics are reset")
            await asyncio.sleep(sleep_duration)

            print("Performing daily statistics reset...")
            self.daily_volume = 0
            self.last_reset_datetime = datetime.now()
            print("last_reset_datetime:", self.last_reset_datetime)
            await asyncio.sleep(5)  # ensure that the reset is not performed twice

    async def calculate_volume(self, flow_rate, time_diff):
        latest_usage = flow_rate * time_diff
        self.daily_volume += latest_usage  # ml/min to ml/day
        return

    async def time_since_last_update(self, telemetry_datetime):
        try:
            time_diff = (telemetry_datetime - self.last_update).total_seconds() / 60  # Calculate time in minutes
        except TypeError:
            self.last_update = datetime.strptime(self.last_update, '%Y-%m-%d %H:%M:%S.%f')
            time_diff = (telemetry_datetime - self.last_update).total_seconds() / 60  # in minutes
        return time_diff
