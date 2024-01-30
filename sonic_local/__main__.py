import argparse
import asyncio
import logging

from .websocket_client import WebSocketClient

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)


async def device(options):
    async def create_client():
        sonic_device = WebSocketClient(options.ip_address, options.username, options.password)
        return sonic_device
    return await create_client()


async def main(options):
    # loop = asyncio.get_event_loop()
    sonic_device = await device(options)
    try:
        await sonic_device.connect()
        if options.command == 'requestTelemetry' or options.command == 'requestState':
            await sonic_device.request_command(command=options.command)
        if options.command == 'open' or options.command == 'closed':
            await sonic_device.change_command(command=options.command)
        if options.command == 'subscribe':
            await sonic_device.subscribe()
        await sonic_device.close()
    except KeyboardInterrupt:
        _LOGGER.info("Keyboard interrupt")
        try:
            _LOGGER.info("Closing connection to device")
            await sonic_device.close()
        except Exception as e:
            _LOGGER.error("Error closing connection to device: %s", e)
        finally:
            _LOGGER.info("Cancelling pending tasks")
            pending = asyncio.all_tasks()
            for task in pending:
                task.cancel()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Sonic Local', description='Sonic Local CLI (all 4 options are required)')
    parser.add_argument("-i", "--ip_address", required=True, help="IP address of the device e.g 192.168.1.10")
    parser.add_argument("-u", "--username", required=True, help="Username for the device")
    parser.add_argument("-p", "--password", required=True, help="Password for the device")
    parser.add_argument("-c", "--command",  required=True, default="requestTelemetry",
                        help="Command to send, (options available: requestState, requestTelemetry, open, closed")
    args = parser.parse_args()
    asyncio.run(main(args))
