from sonic_device import SonicDevice
import asyncio
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
device_address = config['HOST']['ip_address']
device_port = config['HOST']['port']
username = config['CREDENTIALS']['signal_username']
password = config['CREDENTIALS']['signal_password']


async def main():
    device = SonicDevice(device_address, device_port, username, password)
    await device.connect()

    telemetry_data_task = asyncio.create_task(device.telemetry_data())
    daily_reset_task = asyncio.create_task(device.reset_daily_usage())

    # Wait for both tasks to complete (which they won't, they will run forever)
    await asyncio.gather(telemetry_data_task, daily_reset_task)

    # await device.subscribe('requestState')
    # await device.subscribe('requestTelemetry')
    # state = await device.request_state()
    # print(f'Valve state: {state["valve_state"]}')
    # print(f'Radio state: {state["radio_state"]}')

    # device.change_state('open')
    # device.unsubscribe('requestState')
    # device.unsubscribe('requestTelemetry')
    await device.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
