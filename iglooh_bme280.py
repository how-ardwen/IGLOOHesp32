from machine import SPI, Pin
import time
from ustruct import unpack
from array import array

# BME280 Registers
BME280_REGISTER_CONTROL_HUM = 0xF2
BME280_REGISTER_CONTROL = 0xF4
BME280_REGISTER_CONFIG = 0xF5
BME280_REGISTER_PRESSURE_DATA = 0xF7
BME280_REGISTER_TEMP_DATA = 0xFA
BME280_REGISTER_HUMIDITY_DATA = 0xFD

class BME280_SPI:
    def __init__(self, bme_cs, spi):
        self.cs = Pin(bme_cs, Pin.OUT)
        self.spi = spi
        self.__sealevel = 101325

        # Perform sensor initialization
        self._load_calibration_data()
        self._set_sensor_mode()

    def _spi_write(self, register, value):
        self.cs.value(0)  # Select the sensor
        self.spi.write(bytes([register & 0x7F]))  # Write register (clear MSB)
        self.spi.write(bytes([value]))  # Write value
        self.cs.value(1)  # Deselect the sensor

    def _spi_read(self, register, length):
        self.cs.value(0)  # Select the sensor
        self.spi.write(bytes([register | 0x80]))  # Read register (set MSB)
        data = self.spi.read(length)
        self.cs.value(1)  # Deselect the sensor
        return data

    def _load_calibration_data(self):
        # Load trimming parameters into memory by reading them via SPI
        dig_88_a1 = self._spi_read(0x88, 26)
        dig_e1_e7 = self._spi_read(0xE1, 7)

        self.dig_T1, self.dig_T2, self.dig_T3, self.dig_P1, \
            self.dig_P2, self.dig_P3, self.dig_P4, self.dig_P5, \
            self.dig_P6, self.dig_P7, self.dig_P8, self.dig_P9, \
            _, self.dig_H1 = unpack("<HhhHhhhhhhhhBB", dig_88_a1)

        self.dig_H2, self.dig_H3, self.dig_H4, \
            self.dig_H5, self.dig_H6 = unpack("<hBbhb", dig_e1_e7)
        self.dig_H4 = (self.dig_H4 * 16) + (self.dig_H5 & 0xF)
        self.dig_H5 //= 16

    def _set_sensor_mode(self):
        # Set the sensor mode to Normal with default oversampling settings
        self._spi_write(BME280_REGISTER_CONTROL_HUM, 0x01)  # Humidity oversampling x1
        self._spi_write(BME280_REGISTER_CONTROL, 0x27)  # Temperature and Pressure oversampling x1, Normal mode
        self._spi_write(BME280_REGISTER_CONFIG, 0xA0)  # Standby time and filter settings

    def read_raw_data(self):
        # Read raw data from the sensor registers via SPI
        data = self._spi_read(BME280_REGISTER_PRESSURE_DATA, 8)  # Read from pressure, temp, and humidity registers
        raw_press = ((data[0] << 16) | (data[1] << 8) | data[2]) >> 4
        raw_temp = ((data[3] << 16) | (data[4] << 8) | data[5]) >> 4
        raw_hum = (data[6] << 8) | data[7]
        return raw_temp, raw_press, raw_hum

    def read_compensated_data(self):
        # Read raw data and compensate it using the calibration data
        raw_temp, raw_press, raw_hum = self.read_raw_data()

        # Temperature compensation
        var1 = (raw_temp / 16384.0 - self.dig_T1 / 1024.0) * self.dig_T2
        var2 = (raw_temp / 131072.0 - self.dig_T1 / 8192.0) ** 2 * self.dig_T3
        t_fine = int(var1 + var2)
        temperature = (var1 + var2) / 5120.0

        # Pressure compensation
        var1 = (t_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self.dig_P6 / 32768.0
        var2 += var1 * self.dig_P5 * 2.0
        var2 = (var2 / 4.0) + (self.dig_P4 * 65536.0)
        var1 = ((self.dig_P3 * var1 * var1 / 524288.0) + (self.dig_P2 * var1)) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.dig_P1

        if var1 == 0.0:
            pressure = 30000  # Avoid division by zero
        else:
            p = ((1048576.0 - raw_press) - (var2 / 4096.0)) * 6250.0 / var1
            var1 = self.dig_P9 * p * p / 2147483648.0
            var2 = p * self.dig_P8 / 32768.0
            pressure = p + (var1 + var2 + self.dig_P7) / 16.0

        # Humidity compensation
        h = t_fine - 76800.0
        h = (raw_hum - (self.dig_H4 * 64.0 + self.dig_H5 / 16384.0 * h)) * \
            (self.dig_H2 / 65536.0 * (1.0 + self.dig_H6 / 67108864.0 * h *
                                      (1.0 + self.dig_H3 / 67108864.0 * h)))
        humidity = h * (1.0 - self.dig_H1 * h / 524288.0)

        if humidity < 0:
            humidity = 0
        if humidity > 100:
            humidity = 100

        return temperature, pressure / 100.0, humidity
    
    def read_reg(self, register, length):
        self._spi_read(register=register, length=length)

    def write_reg(self, register, value):
        self._spi_write(register=register, value=value)