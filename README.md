This is an early version of a local control and data extraction for the Sonic water shut of valve.
I have previously written a python library for the web API and a Home Assistant integration for the same device.

This library will exclusively act as a websocket client that connects directly to the device and thus will be local only

It will have less control of device and account settings (than the web api library) and will focus on the ability to calculate and view the volume of water used in a period of time, thus will be ideally setup to supply information to the Home Assistant energy dashboard.

The water consumption information is not currently available in the web API.

It will also have device status information (battery levels, signal strength etc.), further it will have the ability to open and close the valve.

The device publishes a telemetry message approximately every 1 minute when there is no flow, and approx every second when there is water flowing.

This message contains the flow rate, water temperature, ambient_temp, the absolute water pressure, the battery level, the leak_status, device status and the probe time.

I have initially structured the library with the following classes.
 
1. `SonicDevice`: This class represents the Sonic device and contains methods to interact with it.
It has methods like `request_state`, `request_telemetry`, `change_state`, and `calculate_daily_volume`.

2. `WebSocketClient`: This class handle the WebSocket connection to the Sonic device.
It has methods like `connect`, `disconnect`, `send`, and `receive`.

3. `Message`: This class handles json messages to be sent or received over the WebSocket connection.
It has the methods `to_json` and `from_json`.

4. `main`: An instance of `SonicDevice` is created, we connect to it, receive a stream of volume usage, 
Also able to perform operations like open and close the valve.

TO USE

1. ~~To test. copy the config_demo.ini file and rename to config.ini and update the values with your device details.~~
2. You need to enable the `Local mode status` in the `Signal Settings` within the `Settings` in the `Sonic` App to get the device's local server username/password.
3. If the `Local mode status` is disabled and re-enabled, the username/password will change.
4. Then from the terminal run `python main.py --ip YOURIPADDRESS -u YOURUSERNAME -p YOURPASSWORD --c XXXXXX` where XXXXXX is either `open`, `closed`, `requestState` or `requestTelemetry`.
5. for help with the command line arguments run `python main.py --help`

TODO

1. ~~add method for storing/caching daily volume in case program crashes~~
2. ~~handle the concurrency of receiving/returning volumes and also daily tasks~~ using asyncio.gather task to run concurrently 
3. Handle functions like opening, closing valve alongside the telemetry data stream
4. Can I automatically identify the devices ip on my local network? or is this something that will be better suited to the Home Assistant integration?
5. ~~remove port number from config.ini and set default as 443 in code.~~ Done
6. ~~Handle crashes and reconnection to websocket better, device can become unreachable if clean disconnect is not performed.~~ Working quite well now
7. ~~Add~~ improve logging (print statements to logger)
8. Add tests
9. average pressure? or max pressure? 
10. handle different timezones
11. remove old code in sonic_device.py
12. handle delay for valve to open and close then read state to confirm success
13. rewrite readme to reflect current state of project (moving volume calculation to HA integration)
14. ~~remove configparser from main.py as it has been replaced with argparse~~
15. 
15. ...