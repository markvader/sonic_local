"""Exceptions used by sonic_websocket."""


class SonicWebsocketError(Exception):
    """Base exception for Sonos websockets."""


class SonicWSConnectionError(SonicWebsocketError):
    """Connection error encountered on a Sonos websocket."""


class Unauthorized(SonicWebsocketError):
    """Authorization rejected when connecting to a Sonos websocket."""
