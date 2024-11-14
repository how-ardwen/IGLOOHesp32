# IGLOOH ESP32 proof of concept code
# Converted to MicroPython
# Howard Wen
# October 2024

import machine
import sdcard
import uos
import time
import dht
from iglooh_bme280 import BME280_SPI
import gc

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
 
# Intialize SPI peripheral (start with 1 MHz) -> 400 kHz
spi = machine.SPI(1,
                  baudrate=SPI_BAUDRATE,
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

file_path= "/sd/runtime_logs.txt"

#define batch size
BATCH_SIZE = 10
log_batch = []
#open file only once to avoid repeated open/close delays
dataFile = open(file_path, "a")

# #Millis timing variables
last_time = time.ticks_ms() #initialize last time for timestamp intervals
interval = 1000 #1 second interval for timestamps
      
# Function to get the current date and time
def get_date_time():
    rtc = machine.RTC()
    date = rtc.datetime()
    date_str = f"{date[0]}-{date[1]:02d}-{date[2]:02d}"
    time_str = f"{date[4]:02d}:{date[5]:02d}:{date[6]:02d}"
    return date_str, time_str


record = 0
date_str, time_str = get_date_time()  # Get the initial date and time


while True:
    #get data and create log entry without timestamp unless interval has passed
    try:
        # Update timestamp only if the interval has passed
        current_time = time.ticks_ms()
        
        if time.ticks_diff(current_time, last_time) >= interval:
            _, time_str = get_date_time()
            last_time = current_time  # Reset last timestamp time
        
        temperature, pressure, humidity = bme280.read_compensated_data()
    
#     #only update timestamp if interval has passed
#         current_time = time.ticks_ms()
#         if time.ticks_diff(current_time, last_time) >= interval:
#             date_str, time_str = get_date_time()
#             last_time = current_time #reset last timestamp time

        #record log entry
        log_entry = (f"{record},{date_str},{time_str},{temperature:.2f}C,{pressure:.2f}hPa,{humidity:.2f}%\n")
        log_batch.append(log_entry)
        
        #write data to card when batch size is met   
#         if len(log_batch) >= BATCH_SIZE:
#             with open(filepath, "a") as file:
#                 print("".join(log_batch))
#                 file.write("".join(log_batch))
#             log_batch.clear()
            
        if len(log_batch) >= BATCH_SIZE:
            dataFile.write("".join(log_batch))
            print("".join(log_batch))
            dataFile.flush()
            log_batch.clear()
            
            
        record += 1


    except Exception as e:
        print("Error reading BME280 or writing to SD card:", e)
    
    
    time.sleep(0.001)
