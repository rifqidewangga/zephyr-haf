import sys
from zephyr import Zephyr
import zephyr


def main():
    env_temperature: float = zephyr.c_to_kelvin(20.0)
    env_pressure: float = 1024.0  # hPa

    if len(sys.argv) == 3:
        env_pressure = float(sys.argv[1])
        env_temperature = zephyr.c_to_kelvin(float(sys.argv[2]))

    sensor = None

    try:
        sensor = Zephyr()
    except zephyr.SensorNotSupported as e:
        print(e.message)

    if sensor is not None:
        while True:
            try:
                qs = sensor.read_average()
                qx = zephyr.compensated_reading(qs, env_temperature, env_pressure)
                print(f"{qx:2f}")
            except zephyr.InvalidSensorData as e:
                print(e.message)
            except KeyboardInterrupt:
                print("Program terminated")
                break


if __name__ == '__main__':
    main()
