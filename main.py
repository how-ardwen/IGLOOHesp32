# IGLOOH ESP32 proof of concept code
# Converted to MicroPython
# Howard Wen
# October 2024

import machine
import sdcard
import uos

# CONSTANTS
# SPI pins
SPI_BAUDRATE = 1320000
SPI_MOSI = 23
SPI_MISO = 19
SPI_SCK = 18
SD_CS = 5

DEBUG = 0

# Assign chip select (CS) pin (and start it high)
cs = machine.Pin(SD_CS, machine.Pin.OUT)
 
# Intialize SPI peripheral (start with 1 MHz) -> 400 kHz
spi = machine.SPI(1,
                  baudrate=400000,
                  polarity=0,
                  phase=0,
                  bits=8,
                  firstbit=machine.SPI.MSB,
                  sck=machine.Pin(SPI_SCK),
                  mosi=machine.Pin(SPI_MOSI),
                  miso=machine.Pin(SPI_MISO))
 
# Initialize SD card
sd = sdcard.SDCard(spi, cs, 400000)
 
# Mount filesystem
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")
 
# Create a file and write something to it
with open("/sd/test01.txt", "w") as file:
    file.write("Hello, SD World!\r\n")
    file.write("This is a test\r\n")
 
# Open the file we just created and read from it
with open("/sd/test01.txt", "r") as file:
    data = file.read()
    print(data)
