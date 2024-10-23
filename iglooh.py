# IGLOOH ESP32 proof of concept code
# Converted to MicroPython
# Howard Wen
# October 2024

from machine import Pin, I2C
import network
import urequests
import time
import utime
import sys

# CONSTANTS
# SDA and SCL pins for the RTC
I2C_SDA = 21
I2C_SCL = 22
RTC_I2C_ADDR = 0x68  # Typical I2C address for DS3231
# WIFI ssid and password
WIFI_SSID = "BELL882"
WIFI_PW = "37E26FF916A6"
EPOCH_OFFSET = 946684800  # Offset for epoch starting from 2000-01-01 to 1970-01-01

# setup I2C
i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=100000)

# Function to set up DS3231 RTC
def rtc_setup():
    # Check if RTC is connected
    devices = i2c.scan()
    if devices:
        print(f"I2C devices found at addresses: {[hex(addr) for addr in devices]}")
        if RTC_I2C_ADDR in devices:
            print("RTC DS3231 found at address 0x68")
        else:
            print("RTC DS3231 not found at the expected address")
    else:
        print("No I2C devices found")

# Function to set time on DS3231 RTC
def set_rtc_time(year, month, day, weekday, hour, minute, second):
    # Convert time to BCD format
    def to_bcd(value):
        return ((value // 10) << 4) | (value % 10)

    time_data = bytearray([to_bcd(second), to_bcd(minute), to_bcd(hour), to_bcd(weekday), to_bcd(day), to_bcd(month), to_bcd(year % 100)])
    i2c.writeto_mem(RTC_I2C_ADDR, 0x00, time_data)
    print("RTC time set successfully")

# WiFi Setup
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PW)

    while not wlan.isconnected():
        print(f"Connecting to WiFi network {WIFI_SSID} ...")
        time.sleep(5)
    print("Connected to WiFi!")

# Function to get current time from an online API and set RTC
def sync_time_with_ntp():
    try:
        response = urequests.get("http://worldtimeapi.org/api/timezone/Etc/UTC")
        if response.status_code == 200:
            json_data = response.json()
            datetime_str = json_data["datetime"]
            year = int(datetime_str[0:4])
            month = int(datetime_str[5:7])
            day = int(datetime_str[8:10])
            hour = int(datetime_str[11:13])
            minute = int(datetime_str[14:16])
            second = int(datetime_str[17:19])
            millisecond = int(datetime_str[20:23])  # Extract milliseconds
            weekday = (utime.localtime(utime.mktime((year, month, day, hour, minute, second, 0, 0))))[6] + 1  # Calculate weekday (1=Monday, ..., 7=Sunday)
            set_rtc_time(year, month, day, weekday, hour, minute, second)
            print(f"RTC synchronized with NTP server. Milliseconds: {millisecond}")
        else:
            print("Failed to get time from server, status code:", response.status_code)
        response.close()
    except Exception as e:
        print("Error syncing time with NTP server:", e)

# Function to read current epoch time from RTC with milliseconds precision
def read_epoch_time_with_millis():
    data = i2c.readfrom_mem(RTC_I2C_ADDR, 0x00, 7)
    def from_bcd(value):
        return ((value >> 4) * 10) + (value & 0x0F)

    second = from_bcd(data[0])
    minute = from_bcd(data[1])
    hour = from_bcd(data[2])
    day = from_bcd(data[4])
    month = from_bcd(data[5])
    year = from_bcd(data[6]) + 2000

    # Manually convert the date and time to epoch time (taking into account the 2000 epoch offset)
    try:
        tm = (year, month, day, hour, minute, second, 0, 0, 0)
        epoch_time = utime.mktime(tm) + EPOCH_OFFSET  # Adjust for epoch starting from 2000-01-01
    except OverflowError:
        # If the date is out of bounds for `mktime`, fallback to a default
        epoch_time = 0
        print("Error: Date is out of range for epoch conversion")

    # Get current microseconds from the system timer
    microseconds = utime.ticks_us() % 1000000
    # Format the output as epoch_time.microseconds
    epoch_time_with_microseconds = f"{epoch_time}.{microseconds:06d}"
    return epoch_time_with_microseconds

# Run RTC setup, connect to WiFi, sync with NTP and print time in epoch with microseconds every 30 seconds
if __name__ == "__main__":
    rtc_setup()
    user_input = False
    if user_input:
        connect_wifi()
        sync_time_with_ntp()
    else:
        print("Skipping time update. Proceeding to print epoch time.")
    
    while True:
        epoch_time_with_microseconds = read_epoch_time_with_millis()
        print(f"Current epoch time: {epoch_time_with_microseconds}")
        time.sleep(30)

