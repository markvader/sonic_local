This is an early version of a local control and data extraction for the Sonic water shut of valve.
I have previously written a python library for the web API and a Home Assistant integration for the same device.

This library will exclusively act as a websocket client that connects directly to the device and thus will be local only

It will have less control of device and account settings (than the web api library) and will focus on the ability to calculate and view the volume of water used in a period of time, thus will be ideally setup to supply information to the Home Assistant energy dashboard.

The water consumption information is not available in the web API.

It will also have device status information (battery levels, signal strength etc), further it will have the ability to open and close the valve.

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

To test. copy the config_demo.ini file and rename to config.ini and update the values with your device details.
You need to enable the `Local mode status` in the `Signal Settings` within the `Settings` in the `Sonic` App to get the device's local server username/password.
If the `Local mode status` is disabled and re-enabled, the username/password will change.
Then run `python main.py`

TODO

add method for storing/caching daily volume in case program crashes
need to handle the concurrency of receiving/returning volumes, and also state, and performing functions like opening, closing valve
Can I automatically identify the devices ip on my local network? or is this something that will be better suited to the Home Assistant integration?
remove port number from config.ini and set default as 443 in code.
