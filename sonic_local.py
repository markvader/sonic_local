#!/usr/bin/env python3

import base64
import json
import ssl
import threading
import time
import logging
import logging.config
import websocket

SONIC__LOCAL_USERNAME = "EnterUsernameFromSignalSettingsInTheSonicApp"
SONIC__LOCAL_PASSWORD = "EnterPasswordFromSignalSettingsInTheSonicApp"
SONIC_LOCAL_LAN_IP = "192.168.1.103"  # Replace with the IP address of the Sonic you want to test, e.g. "192.168.0.112"
LOG_LEVEL = "DEBUG"


def configure_logger(name, log_path):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s - %(levelname)s - %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': log_path,
                'maxBytes': 10000,
                'backupCount': 3
            }
        },
        'loggers': {
            'default': {
                'level': LOG_LEVEL,
                'handlers': ['console', 'file']
            }
        },
        'disable_existing_loggers': False
    })
    return logging.getLogger(name)


class SonicLocal:
    def __init__(self):
        self.logger = configure_logger('default', 'sonic_local.log')

        self.logger.debug('SonicLocal class initialising line55 ')

        self._wsusername = SONIC__LOCAL_USERNAME
        self._wspassword = SONIC__LOCAL_PASSWORD

        self._wshost = SONIC_LOCAL_LAN_IP
        self._wsport = "443"

        self._ws = None

        self.init_websocket(self.logger)
        # self.thread = threading.Thread(target=self.init_websocket(self.logger))
        # self.thread.daemon = False
        # self.thread.start()

    def init_websocket(self, logger):
        self.logger = logger
        self.logger.debug('initializing websocket line72')

        self._ws = WebsocketListener(sonic=self, on_message=self.on_message, on_error=self.on_error)

        try:
            self.logger.debug('entering try line77')
            self._ws.run_forever(ping_interval=10)
        except websocket.WebSocketAddressException as e:
            self.logger.error('WebSocketAddressException line80 %e' % {e})
        except websocket.WebSocketBadStatusException(message=None, status_code=None, status_message=None) as e:
            self.logger.error('WebSocketBadStatusException line82 %e' % {e})
        except websocket.WebSocketConnectionClosedException as e:
            self.logger.error('WebSocketConnectionClosedException line84 %e' % {e})
        except websocket.WebSocketPayloadException as e:
            self.logger.error('WebSocketPayloadException line86 %e' % {e})
        except websocket.WebSocketProtocolException as e:
            self.logger.error('WebSocketProtocolException line88 %e' % {e})
        except websocket.WebSocketProxyException as e:
            self.logger.error('WebSocketProxyException line90 %e' % {e})
        except websocket.WebSocketTimeoutException as e:
            self.logger.error('WebSocketTimeoutException line92 %e' % {e})
        except websocket.WebSocketException as e:
            self.logger.error('WebSocketException line94 %e' % {e})
        finally:
            self.logger.error('unknown error occurred, shutting down line96')
            self._ws.close()

    def on_message(self, *args):
        data = args
        self.logger.debug('received websocket msg: %s', data)

        # Data parsing to happen here
        # data = json.loads(data)
        # if 'telemetry' in data:
        #     self.logger.info('received telemetry data: %s', data['telemetry'])

    def on_error(self, *args):
        error = args
        self.logger.error('websocket error: %s line110' % str(error))

    def get_ws(self):
        return self._ws

    def get_wsusername(self):
        return self._wsusername

    def get_wspassword(self):
        return self._wspassword

    def get_wshost(self):
        return self._wshost

    def get_wsport(self):
        return self._wsport


class WebsocketListener(threading.Thread, websocket.WebSocketApp):
    def __init__(self, sonic, on_message=None, on_error=None):
        self.logger = sonic.logger
        self._sonic = sonic

        headers = {}

        websocket_userpass = '{}:{}'.format(self._sonic.get_wsusername(),
                                            self._sonic.get_wspassword())

        headers["Authorization"] = "Basic " + base64.b64encode(websocket_userpass.encode()).decode()

        self.logger.info('WebsocketListener headers: %s line140' % headers)

        websocket_host = 'wss://{}:{}'.format(self._sonic.get_wshost(),
                                              self._sonic.get_wsport())

        self.logger.info('WebsocketListener initialising, connecting to host: %s line145' % websocket_host)

        threading.Thread.__init__(self)
        websocket.WebSocketApp.__init__(self, websocket_host,
                                        header=headers,
                                        on_open=self.on_open,
                                        on_error=on_error,
                                        on_message=on_message,
                                        on_close=self.on_close)

        self.connected = False
        self.last_update = time.time()

    def on_open(self, *args):
        self.connected = True
        self.last_update = time.time()

        payload = {
            'event': "ping"
        }

        self.logger.debug('sending payload message to websocket: %s line166', json.dumps(payload))

        self.send(json.dumps(payload))

    def on_close(self, *args):
        self.logger.debug('websocket closed line171')
        self.connected = False

    def run_forever(self, sockopt=None, sslopt=None,
                    ping_interval=10, ping_timeout=9,
                    ping_payload="",
                    http_proxy_host=None, http_proxy_port=None,
                    http_no_proxy=None, http_proxy_auth=None,
                    http_proxy_timeout=None,
                    skip_utf8_validation=False,
                    host=None, origin=None, dispatcher=None,
                    suppress_origin=False, proxy_type=None, reconnect=None):
        self.logger.debug(
            'attempting to call WebSocketApp run_forever with ping_interval: {} line184'.format(ping_interval))

        websocket.WebSocketApp.run_forever(self,
                                           sockopt=sockopt,
                                           sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout)


if __name__ == '__main__':
    SonicLocal()
