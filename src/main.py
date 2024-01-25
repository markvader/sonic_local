import argparse
from websocket_client import WebSocketClient
import asyncio
import configparser
import logging

config = configparser.ConfigParser()
config.read('config.ini')
device_address = config['HOST']['ip_address']
username = config['CREDENTIALS']['signal_username']
password = config['CREDENTIALS']['signal_password']

logging.basicConfig(level=logging.DEBUG)


async def main(options):
    sonic_device = WebSocketClient(options.ip_address, options.username, options.password)
    await sonic_device.connect()
    if options.command == 'requestTelemetry' or options.command == 'requestState':
        await sonic_device.request_command(command=options.command)
    if options.command == 'open' or options.command == 'closed':
        await sonic_device.change_command(command=options.command)
    await sonic_device.close()

# async def main():
#     max_retries = 5  # Maximum number of retries
#     backoff_factor = 3  # Multiplier for exponential backoff
#     delay = 5  # Initial delay in seconds
#
#     for _ in range(max_retries):
#         try:
#             sonic_device = WebSocketClient(device_address, username, password)
#             await sonic_device.connect()
#
#             # telemetry_data_task = asyncio.create_task(sonic_device.receive_data())
#             send_json_task = asyncio.create_task(sonic_device.request_command('requestTelemetry'))
#             daily_reset_task = asyncio.create_task(sonic_device.reset_daily_usage())
#
#             # Wait for both tasks to complete (which they won't, they will run forever)
#             # await asyncio.gather(telemetry_data_task, daily_reset_task)
#             await asyncio.gather(send_json_task, daily_reset_task)
#         except Exception as e:
#             print(f"An error occurred: {e}")
#             print(f"Retrying in {delay} seconds...")
#             await asyncio.sleep(delay)
#             delay *= backoff_factor  # Increase delay for next retry
#     else:
#         print("Maximum retries reached. Giving up.")
#         await sonic_device.close()
#
#     # await device.subscribe('requestState')
#     # await device.subscribe('requestTelemetry')
#     # state = await device.request_state()
#     # device.change_state('open')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip_address",
        "-i",
        required=True,
        help="IP address of the device e.g 192.168.1.10"
    )
    parser.add_argument(
        "--username",
        "-u",
        required=True,
        help="Username for the device"
    )
    parser.add_argument(
        "--password",
        "-p",
        required=True,
        help="Password for the device"
    )
    parser.add_argument(
        "--command",
        "-c",
        required=True,
        help="Command to send to the device, e.g. requestState, requestTelemetry, open, closed"
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args))
