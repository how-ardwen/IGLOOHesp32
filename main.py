# IGLOOH ESP32 proof of concept code
# Converted to MicroPython
# Adam Dunn
# November 2024

from machine import Pin, I2C
import machine
import sdcard
import uos
import time
import dht
from iglooh_bme280 import BME280_SPI
from iglooh_rtc import RTC_I2C

# CONSTANTS
# SPI pins
SPI_BAUDRATE = 4000000
SPI_MOSI = 23
SPI_MISO = 19
SPI_SCK = 18
SD_CS = 5
BME_CS= 15


DEBUG = 0

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(SD_CS, machine.Pin.OUT)
 
 #initialize i2c
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
#initialize i2c instance from iglooh_rtc class
rtc = RTC_I2C(i2c)    
 
# Intialize SPI peripheral (start with 1 MHz) -> 400 kHz
spi = machine.SPI(1,
                  baudrate=4000000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(SPI_SCK),
                  mosi=machine.Pin(SPI_MOSI),
                  miso=machine.Pin(SPI_MISO))
 
# Initialize SD card and BME
sd = sdcard.SDCard(spi, cs, SPI_BAUDRATE)
bme280 = BME280_SPI(bme_cs=BME_CS, spi=spi)
 
# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")

file_path= "/sd/runtime_logs.csv"

WIFI_SSID = "---------"
WIFI_PW = "----------"

# WiFi Setup
# def connect_wifi():
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     wlan.connect(WIFI_SSID, WIFI_PW)
#     
#     while not wlan.isconnected():
#         print(f"Connecting to WiFi network {WIFI_SSID} ...")
#         time.sleep(5)
#     print("Connected to WiFi!")
    
#initialize rtc date and time
#rtc._set_rtc_time(2024, 11, 26, 4, 12, 49, 0)

#open file only once to avoid repeated open/close delays
dataFile = open(file_path, "a")

record = 0
try:
    while True:
        try:        
            #get time and environment data
            raw_temperature, raw_pressure, raw_humidity = bme280.read_raw_data()
            current_time = rtc._read_epoch_time_with_millis()
            
            #record log entry
            log_entry = f"{record},{current_time},{raw_temperature},{raw_pressure},{raw_humidity}\n"
            
            print(log_entry)
            dataFile.write(log_entry)
            record += 1

        except Exception as e:
            print("Error reading BME280 or writing to SD card:", e)
    
    
    time.sleep(0.001)

finally:
    # Ensure the file is closed on exit
    dataFile.close()    