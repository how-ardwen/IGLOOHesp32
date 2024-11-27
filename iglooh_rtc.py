# IGLOOH ESP32 DS3231 RTC code

from machine import Pin, I2C
import urequests
import utime

class RTC_I2C:
    ADDR = 0x68  # I2C address for DS3231 (also one on 0x57?)
    EPOCH_OFFSET = 946684800  # Offset for epoch starting from 2000-01-01 to 1970-01-01

    def __init__(self, i2c):
        self.i2c = i2c

    # Function to set time on DS3231 RTC
    def _set_rtc_time(self, year, month, day, weekday, hour, minute, second):
        # Convert time to BCD format
        def to_bcd(value):
            return ((value // 10) << 4) | (value % 10)

        time_data = bytearray([to_bcd(second), to_bcd(minute), to_bcd(hour), to_bcd(weekday), to_bcd(day), to_bcd(month), to_bcd(year % 100)])
        self.i2c.writeto_mem(self.ADDR, 0x00, time_data)
        print("RTC time set successfully")

    # Function to get current time from an online API and set RTC
    def _sync_rtc_with_ntp(self):
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
                self._set_rtc_time(year, month, day, weekday, hour, minute, second)
                print(f"RTC synchronized with NTP server. Milliseconds: {millisecond}")
            else:
                print("Failed to get time from server, status code:", response.status_code)
            response.close()
        except Exception as e:
            print("Error syncing time with NTP server:", e)

    def _read_epoch_time_with_millis(self):
            data = self.i2c.readfrom_mem(self.ADDR, 0x00, 7)
            def from_bcd(value):
                return ((value >> 4) * 10) + (value & 0x0F)

            second = from_bcd(data[0])
            minute = from_bcd(data[1])
            hour = from_bcd(data[2])
            day = from_bcd(data[4])
            month = from_bcd(data[5])
            year = from_bcd(data[6]) + 2000

            #1. Use this if you want to return time in epoch format
            # Manually convert the date and time to epoch time (taking into account the 2000 epoch offset)
#             try:
#                 tm = (year, month, day, hour, minute, second, 0, 0, 0)
#                 epoch_time = utime.mktime(tm) + self.EPOCH_OFFSET  # Adjust for epoch starting from 2000-01-01
#             except OverflowError:
#                 # If the date is out of bounds for `mktime`, fallback to a default
#                 epoch_time = 0
#                 print("Error: Date is out of range for epoch conversion")
# 
#             # Get current microseconds from the system timer
#             microseconds = utime.ticks_us() % 1000000
#             # Format the output as epoch_time.microseconds
#             epoch_time_with_microseconds = f"{epoch_time}.{microseconds:06d}"
#             return epoch_time_with_microseconds
            
            #2, Use this if you want to return time in human readable format (slower)
#             # Get current system microseconds
            microseconds = utime.ticks_us() % 1000000

            # Format as human-readable date and time with milliseconds
            datetime_str = (f"{year:04d},{month:02d},{day:02d},{hour:02d}:{minute:02d}:{second:02d}:{microseconds // 1000:03d}")
            return datetime_str

   
    def setup(self, wifi_connected):
        if wifi_connected:
            self._sync_time_with_ntp()
            curr_time = self._read_epoch_time_with_millis()
        else:
            curr_time = self._read_epoch_time_with_millis()

        return curr_time
    
    
    def get_time(self):
        return self._read_epoch_time_with_millis() 
   
   # WiFi Setup
    def connect_wifi(self, WIFI_SSID, WIFI_PW):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PW)

        while not wlan.isconnected():
            print(f"Connecting to WiFi network {WIFI_SSID} ...")
            time.sleep(5)
            print("Connected to WiFi!")
