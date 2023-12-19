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

    calculate_volume_task = asyncio.create_task(device.calculate_daily_volume())
    daily_reset_task = asyncio.create_task(device.reset_daily_usage())

    # Wait for both tasks to complete (which they won't, they will run forever)
    await asyncio.gather(calculate_volume_task, daily_reset_task)

    # await device.subscribe('requestState')
    # await device.subscribe('requestTelemetry')
    # state = await device.request_state()
    # print(f'Valve state: {state["valve_state"]}')
    # print(f'Radio state: {state["radio_state"]}')
    # telemetry = await device.request_telemetry()
    # print(f'Water flow: {telemetry["water_flow"]}')
    # print(f'Leak status: {telemetry["leak_status"]}')
    # print(f'Status: {telemetry["status"]}')
    # print(f'Water temp: {telemetry["water_temp"]}')
    # print(f'Ambient temp: {telemetry["ambient_temp"]}')
    # print(f'Abs pressure: {telemetry["abs_pressure"]}')
    # print(f'Battery level: {telemetry["battery_level"]}')
    # print(f'Probed at: {telemetry["probed_at"]}')

    # device.change_state('open')
    # device.unsubscribe('requestState')
    # device.unsubscribe('requestTelemetry')
    await device.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
