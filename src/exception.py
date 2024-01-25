"""Exceptions used by sonic_websocket."""


class SonicWebsocketError(Exception):
    """Base exception for Sonic websockets."""


class SonicWSConnectionError(SonicWebsocketError):
    """Connection error encountered on a Sonic websocket."""


class Unauthorized(SonicWebsocketError):
    """Authorization rejected when connecting to a Sonic websocket."""
