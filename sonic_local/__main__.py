import argparse
import asyncio
import logging

from .websocket_client import WebSocketClient

logging.basicConfig(level=logging.DEBUG)


async def main(options):
    sonic_device = WebSocketClient(options.ip_address, options.username, options.password)
    await sonic_device.connect()
    if options.command == 'requestTelemetry' or options.command == 'requestState':
        await sonic_device.request_command(command=options.command)
    if options.command == 'open' or options.command == 'closed':
        await sonic_device.change_command(command=options.command)
    await sonic_device.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Sonic Local', description='Sonic Local CLI (all 4 options are required)')
    parser.add_argument("-i", "--ip_address", required=True, help="IP address of the device e.g 192.168.1.10")
    parser.add_argument("-u", "--username", required=True, help="Username for the device")
    parser.add_argument("-p", "--password", required=True, help="Password for the device")
    parser.add_argument("-c", "--command",  required=True, default="requestTelemetry",
                        help="Command to send, (options available: requestState, requestTelemetry, open, closed")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
