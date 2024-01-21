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


async def main():
    while True:  # Outer loop to handle restarts
        try:
            sonic_device = WebSocketClient(device_address, username, password)
            await sonic_device.connect()

            telemetry_data_task = asyncio.create_task(sonic_device.receive_data())
            daily_reset_task = asyncio.create_task(sonic_device.reset_daily_usage())

            # Wait for both tasks to complete (which they won't, they will run forever)
            await asyncio.gather(telemetry_data_task, daily_reset_task)

        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(5)  # Wait for a short time before retrying

    # await device.subscribe('requestState')
    # await device.subscribe('requestTelemetry')
    # state = await device.request_state()

    # device.change_state('open')
    # device.unsubscribe('requestState')
    # device.unsubscribe('requestTelemetry')
    # await sonic_device.close()

if __name__ == '__main__':
    asyncio.run(main())
