# zephyr-haf
Python module for communicating with [Honeywell Zephyr Digital Airflow Sensors HAF Series](https://eu.mouser.com/datasheet/2/187/honeywell-sensing-airflow-zephyr-haf-series-digita-740409.pdf). This module has simple class to get reading from the sensor in SCCM (Standard Cubic Centimeters per Minute). This module also handle some error handling if there is invalid data coming from the sensor.

# Supported Device
Supported sensor types are all sensor listed [here](https://eu.mouser.com/datasheet/2/187/honeywell-sensing-airflow-zephyr-haf-series-digita-740409.pdf).

This module tested on:
1. Raspberry pi 4
2. Raspberry pi 3B+

# How To Use
Here is how you can instantiate sensor object with default parameters (maximum flow rate of 750 SCCM, sensor address at 0x49 and using smbus channel 1). 
```Python
from zephyr import Zephyr
sensor = Zephyr()
flow_rate = sensor.read()
```

To use other supported sensor, you can specify it in constructor as follow. This module will throw an exception if you select not supported sensor.
```Python
from zephyr import Zephyr
sensor = Zephyr(flow_range=50.0, sensor_address=0x69, smbus_ch=1)
```

You can also use average sensor reading and specify the number of data to be averaged. The data will be taken every 1 ms.
```Python
from zephyr import Zephyr
sensor = Zephyr()
averaged_flow = sensor.read_average(n=100)
```
