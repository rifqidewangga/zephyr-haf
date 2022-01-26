from smbus2 import SMBus
from time import sleep

SUPPORTED_FLOW_RANGE = [50.0, 100.0, 200.0, 400.0, 750.0]

SUPPORTED_SENSOR_ADDRESS = [0x49, 0x59, 0x69, 0x79]


class SensorNotSupported(Exception):
    """
    Exception class for not supported device.
    """

    def __init__(self, flow_range, sensor_address):
        self.message = f"Device with flow range {flow_range} and address {hex(sensor_address)} supported\n"
        self.message += f"Supported flow range: {SUPPORTED_FLOW_RANGE}\n"
        self.message += f"Supported address: {SUPPORTED_SENSOR_ADDRESS}"
        super().__init__(self.message)


class InvalidSensorData(Exception):
    """
    Exception class for invalid sensor data.
    """

    def __init__(self, data, max_retry=1):
        self.message = f"Invalid data received after {max_retry} retries, last data received {hex(data)}."
        super().__init__(self.message)


STANDARD_TEMPERATURE = 273.15  # K
STANDARD_PRESSURE = 1023.38  # hPa


def c_to_kelvin(temp_c: float) -> float:
    """
    converter from celsius to kelvin
    :param temp_c: temperature in celsius
    :return: temperature in kelvin
    """
    return 273.15 + temp_c


def compensated_reading(flow_at_stp: float, temperature: float, pressure: float) -> float:
    """
    calculate compensated reading
    :param flow_at_stp: flow rate in SCCM
    :param temperature: kelvin
    :param pressure: hPa
    :return: compensated flow rate in CCM
    """
    qx = flow_at_stp * (STANDARD_PRESSURE * temperature) / (pressure * STANDARD_TEMPERATURE)
    return qx


class Zephyr:
    """
    Interface to read from Zephyr flow sensor
    https://eu.mouser.com/datasheet/2/187/honeywell-sensing-airflow-zephyr-haf-series-digita-740409.pdf
    """
    def __init__(self, flow_range: float = 750.0, sensor_address: int = 0x49, smbus_ch: int = 1):
        if flow_range not in SUPPORTED_FLOW_RANGE or sensor_address not in SUPPORTED_SENSOR_ADDRESS:
            raise SensorNotSupported(flow_range, sensor_address)

        self._smbus_ch = smbus_ch
        self._FS_flow_rate = flow_range
        self._sensor_address = sensor_address
        self._last_flow_rate = 0.0
        self._sensor_update_period = 0.001  # s

        self._initialize_sensor()

    def _initialize_sensor(self) -> None:
        """
        Make sure valid reading after first device power up.
        First two reading after initial power up will return SN of device, not used in this library.
        :return: None
        """
        start_up_time = 0.017  # seconds
        warm_up_time = 0.030  # seconds

        with SMBus(self._smbus_ch) as bus:
            sleep(start_up_time)
            bus.read_byte(self._sensor_address)
            sleep(warm_up_time)
            bus.read_byte(self._sensor_address)

    def _convert_to_digital_output(self, flow_rate: float) -> int:
        """
        Convert flow rate reading from sensor to digital output code.
        Digital Output Code = 16384 * [0.5 + 0.4 * (Flow Applied/Full Scale Flow)]
        :return: int
        """
        digital_output_code = int(16384 * (0.5 + 0.4 * (flow_rate / self._FS_flow_rate)))
        return digital_output_code

    def _convert_to_flow_rate(self, digital_output) -> float:
        """
        Convert digital output code from sensor reading to SCCM.
        Flow Applied = Full Scale Flow * [(Digital Output Code/16384) - 0.5]/0.4
        :return: float
        """
        flow_rate = self._FS_flow_rate * ((digital_output/16384) - 0.5) / 0.4
        return flow_rate

    @staticmethod
    def _validate_data(data: int) -> bool:
        """
        Validate sensor reading.
        Reading invalid if the two of MSB is not 0b00 (usually during start up or after power loss).
        Sensor should be reinitialized.
        :param: digital_output: int
        :return: bool
        """
        if data & 0xc000 != 0:
            return False

        return True

    def _read_digital_output(self) -> int:
        """
        Read digital output from sensor 12-bit length data.
        It will return None if the data is invalid
        :return: int
        """
        with SMBus(self._smbus_ch) as bus:
            raw_data_block = bus.read_i2c_block_data(self._sensor_address, 0, 2)
            digital_output = raw_data_block[0] << 8 | raw_data_block[1]

            if self._validate_data(digital_output):
                return digital_output

        raise InvalidSensorData(digital_output)

    def read(self) -> float:
        """
        Read flow rate, output in SCCM.
        This method can throw InvalidSensorData exception and should be handled by user.
        :return: float
        """
        flow_rate = self._convert_to_flow_rate(self._read_digital_output())
        self._last_flow_rate = flow_rate

        return flow_rate

    def read_average(self, n: int = 500) -> float:
        """
        read average flow rate from n number data
        :param n: number of data to be averaged
        :return: average flow rate in SCCM
        """
        data = []
        for i in range(n):
            data.append(self.read())
            sleep(self._sensor_update_period)

        return sum(data) / n
