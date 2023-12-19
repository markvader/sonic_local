import websocket
import ssl
import base64


class WebSocketClient:
    def __init__(self, host, port, username, password):
        self.url = f'wss://{host}:{port}'
        self.username = username
        self.password = password
        self.ws = None

    def to_base64(self):
        return base64.b64encode(f'{self.username}:{self.password}'.encode()).decode()

    async def connect(self):
        headers = {'Authorization': 'Basic ' + self.to_base64()}
        self.ws = websocket.create_connection(self.url,
                                              header=headers,
                                              sslopt={"cert_reqs": ssl.CERT_NONE,
                                                      "check_hostname": False})
        print("Connected established")

    async def disconnect(self):
        self.ws.close()

    async def send(self, message):
        self.ws.send(message)

    async def receive(self):
        response = self.ws.recv()
        return response
