import asyncio

from websocket_client import WebSocketClient
from message import Message
from datetime import datetime, timedelta
import json
from json import JSONDecodeError


class SonicDevice:
    def __init__(self, host, port, username, password):
        self.last_reset_datetime = None
        self.last_update = '2023-12-14 00:00:00.00001'
        self.daily_volume = 0
        self.client = WebSocketClient(host, port, username, password)

        # Load the daily usage flag from the file
        is_daily_usage_reset = self.load_flag()
        self.is_daily_usage_reset = is_daily_usage_reset

    async def connect(self):
        print("Device connecting")
        await self.client.connect()

    async def disconnect(self):
        print("Device disconnecting")
        await self.client.disconnect()

    async def subscribe(self, event):
        message = Message(event, {})
        await self.client.send(message.to_json())
        response = await self.client.receive()
        return Message.from_json(response).data

    async def unsubscribe(self, event):
        message = Message(event, {})
        await self.client.send(message.to_json())

    async def request_state(self):
        message = Message('requestState', {})
        await self.client.send(message.to_json())
        response = self.client.receive()
        return Message.from_json(response).data

    async def request_telemetry(self):
        message = Message('requestTelemetry', {})
        await self.client.send(message.to_json())
        response = self.client.receive()
        return Message.from_json(response).data

    async def change_state(self, state):
        message = Message('changeState', {'valve_state': state})
        await self.client.send(message.to_json())

    def save_flag(self):
        with open('is_daily_usage_reset.txt', 'w') as f:
            f.write(str(self.is_daily_usage_reset))

    def load_flag(self):
        try:
            with open('is_daily_usage_reset.txt', 'r') as f:
                is_daily_usage_reset = json.load(f)
        except FileNotFoundError:
            is_daily_usage_reset = False
        except JSONDecodeError:
            is_daily_usage_reset = False
        return is_daily_usage_reset

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
            print(sleep_duration, "seconds until daily statistics reset")
            await asyncio.sleep(sleep_duration)

            print("Performing daily statistics reset...")
            self.daily_volume = 0
            self.last_reset_datetime = datetime.now()
            print("last_reset_datetime:", self.last_reset_datetime)
            await asyncio.sleep(5)  # ensure that the reset is not performed twice

    async def calculate_daily_volume(self):
        while True:
            response = await self.client.receive()
            message = json.loads(response)

            if message['event'] == 'telemetry':
                flow_rate = message['data']['water_flow']
                # print("70 flow_rate", flow_rate)
                try:
                    time_diff = (datetime.now() - self.last_update).total_seconds() / 60  # Calculate time in minutes
                except TypeError:
                    # If self.last_update is not in datetime format, convert it and try again
                    self.last_update = datetime.strptime(self.last_update, '%Y-%m-%d %H:%M:%S.%f')
                    time_diff = (datetime.now() - self.last_update).total_seconds() / 60  # in minutes
                # print("70 time_diff", time_diff)
                self.last_update = datetime.now()
                if time_diff < 1440:  # If the last update was less than 24 hours ago
                    latest_usage = flow_rate * time_diff
                    self.daily_volume += latest_usage  # ml/min to ml/day
                    print(self.last_update,
                          "- latest_usage (ml):", round(latest_usage, 2),
                          "daily_volume (ml):", round(self.daily_volume, 2))
                    await asyncio.sleep(0.5)
