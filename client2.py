import base64
import json
import logging
import websockets
logger = logging.getLogger("sonic_local")
"""Local API for Hero Labs Sonic Water Device

    Usage example:
    from webrtc_signalling import SonicLocal
    soniclocal = SonicLocal(server, id, peer_id)
    soniclocal.on_connect = lambda: soniclocal.setup_call()
    soniclocal.connect()
    soniclocal.start()

"""


class SonicLocalError(Exception):
    pass


class SonicLocalErrorNoPeer(Exception):
    pass


class SonicLocal:
    def __init__(self, server, id, peer_id, enable_basic_auth=False, username=None, password=None):
        """Initialize the soniclocal instance

        Arguments:
            server {string} -- websocket URI to connect to, example: ws://127.0.0.1:8080
            id {integer} -- ID of this client when registering.
            peer_id {integer} -- ID of peer to connect to.
        """

        self.server = server
        self.id = id
        self.peer_id = peer_id
        self.enable_basic_auth = enable_basic_auth
        self.username = username
        self.password = password
        self.conn = None

        self.on_ice = lambda mlineindex, candidate: logger.warning('unhandled ice event')
        self.on_sdp = lambda sdp_type, sdp: logger.warning('unhandled sdp event')
        self.on_connect = lambda: logger.warning('unhandled on_connect callback')
        self.on_disconnect = lambda: logger.warning('unhandled on_disconnect callback')
        self.on_session = lambda: logger.warning('unhandled on_session callback')
        self.on_error = lambda v: logger.warning('unhandled on_error callback: %s', v)

    async def setup_call(self):
        """Creates session with peer

        Should be called after HELLO is received.

        """
        logger.debug("setting up call")
        await self.conn.send('SESSION %d' % self.peer_id)

    async def connect(self):
        """Connects to and registers id with soniclocal server

        Sends the HELLO command to the soniclocal server.

        """
        try:
            headers = None
            if self.enable_basic_auth:
                auth64 = base64.b64encode(
                    bytes("{}:{}".format(self.username, self.password), "ascii")).decode("ascii")
                headers = [
                    ("Authorization", "Basic {}".format(auth64))
                ]
            self.conn = await websockets.connect(self.server, extra_headers=headers)
            await self.conn.send('HELLO %d' % self.id)
        except websockets.ConnectionClosed:
            self.on_disconnect()

    async def send_ice(self, mlineindex, candidate):
        """Sends te ice candidate to peer

        Arguments:
            mlineindex {integer} -- the mlineindex
            candidate {string} -- the candidate
        """

        msg = json.dumps(
            {'ice': {'candidate': candidate, 'sdpMLineIndex': mlineindex}})
        await self.conn.send(msg)

    async def send_sdp(self, sdp_type, sdp):
        """Sends the SDP to peer

        Arguments:
            sdp_type {string} -- SDP type, answer or offer.
            sdp {string} -- the SDP
        """

        logger.info("sending sdp type: %s" % sdp_type)
        logger.debug("SDP:\n%s" % sdp)

        msg = json.dumps({'sdp': {'type': sdp_type, 'sdp': sdp}})
        await self.conn.send(msg)

    async def stop(self):
        logger.warning("stopping")
        await self.conn.close()

    async def start(self):
        """Handles messages from the soniclocal server websocket.

        Message types:
          HELLO: response from server indicating peer is registered.
          ERROR*: error messages from server.
          {"sdp": ...}: JSON SDP message
          {"ice": ...}: JSON ICE message

        Callbacks:

        on_connect: fired when HELLO is received.
        on_session: fired after setup_call() succeeds and SESSION_OK is received.
        on_error(SonicLocalErrorNoPeer): fired when setup_call() failes and peer not found message is received.
        on_error(SonicLocalError): fired when message parsing failes or unexpected message is received.

        """
        async for message in self.conn:
            if message == 'HELLO':
                logger.info("connected")
                await self.on_connect()
            elif message == 'SESSION_OK':
                logger.info("started session with peer: %s", self.peer_id)
                self.on_session()
            elif message.startswith('ERROR'):
                if message == "ERROR peer '%s' not found" % self.peer_id:
                    await self.on_error(SonicLocalErrorNoPeer("'%s' not found" % self.peer_id))
                else:
                    await self.on_error(SonicLocalError("unhandled soniclocal message: %s" % message))
            else:
                # Attempt to parse JSON SDP or ICE message
                data = None
                try:
                    data = json.loads(message)
                except Exception as e:
                    if isinstance(e, json.decoder.JSONDecodeError):
                        await self.on_error(SonicLocalError("error parsing message as JSON: %s" % message))
                    else:
                        await self.on_error(SonicLocalError("failed to prase message: %s" % message))
                    continue
                if data.get("sdp", None):
                    logger.info("received SDP")
                    logger.debug("SDP:\n%s" % data["sdp"])
                    self.on_sdp(data['sdp'].get('type'),
                                data['sdp'].get('sdp'))
                elif data.get("ice", None):
                    logger.info("received ICE")
                    logger.debug("ICE:\n%s" % data.get("ice"))
                    self.on_ice(data['ice'].get('sdpMLineIndex'),
                                data['ice'].get('candidate'))
                else:
                    await self.on_error(SonicLocalError("unhandled JSON message: %s", json.dumps(data)))


def main():
    soniclocal = SonicLocal("192.168.1.11:443", id, "peer_id", username="magic", password="82jVb26KlwQ=")
    soniclocal.on_connect = lambda: soniclocal.setup_call()
    soniclocal.connect()
    soniclocal.start()


if __name__ == '__main__':
    main()
