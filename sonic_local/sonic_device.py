import asyncio
import aiohttp
from aiohttp import WSMsgType
from websocket_client import WebSocketClient
from message import Message
from datetime import datetime
import json


class SonicDevice:
    def __init__(self, host, username, password):
        self.telemetry_json_data = dict()
        self.client = WebSocketClient(host, username, password)
        self.daily_volume = 0
        self.last_reset_datetime = None
        self.last_update = '2023-12-14 00:00:00.000001'

        # Load the daily usage flag from the file
        is_daily_usage_reset = self.load_flag()
        self.is_daily_usage_reset = is_daily_usage_reset

    async def connect(self):
        print("Connecting to device")
        await self.client.connect()

    async def disconnect(self):
        print("Disconnecting from device")
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

    def load_flag(self):
        try:
            with open('is_daily_usage_reset.txt', 'r') as f:
                is_daily_usage_reset = json.load(f)
        except FileNotFoundError:
            is_daily_usage_reset = False
        except json.JSONDecodeError:
            is_daily_usage_reset = False
        return is_daily_usage_reset

