# IGLOOH ESP32 proof of concept code
# Converted to MicroPython
# Howard Wen
# October 2024

from machine import Pin, I2C, SPI
import network
import urequests
import time
import iglooh_bme280
import iglooh_dbm
import iglooh_rtc

# CONSTANTS
# SPI pins
MOSI = 23
MISO = 19
SCK = 18
BME_CS = 5
# SDA and SCL pins for the decibel meter module + RTC
I2C_SDA = 21
I2C_SCL = 22
# WIFI ssid and password
WIFI_SSID = "BELL882"
WIFI_PW = "37E26FF916A6"

DEBUG = 0

# VARIABLES
wifi_connected = False

# setup I2C and SPI
spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))
i2c = I2C(1, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=10000)

# initialize bme and dbm objects
bme = iglooh_bme280.BME280_SPI(bme_cs=BME_CS, spi=spi)
dbm = iglooh_dbm.DBM_I2C(i2c=i2c)
rtc = iglooh_rtc.RTC_I2C(i2c=i2c)

# WiFi Setup
def connect_wifi():
    global wifi_connected

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PW)

    while not wlan.isconnected():
        print(f"Connecting to WiFi network {WIFI_SSID} ...")
        time.sleep(5)
    
    print("Connected!")
    wifi_connected = True

def bme280_setup():
    # Setup the BME280 with default settings
    print(f"id: {bme.read_reg(0xD0,1)} \nversion: {bme.read_reg(0xD1,1)}")

def dbm_setup():
    # Setup the decibel meter
    if dbm.set_configuration(125, 123):
        # unique_id_str = ' '.join(f'{x:02X}' for x in dbm.reg_id)
        print(f"Version: {dbm.version}, Unique ID: {dbm.reg_id}, Scratch: {dbm.scratch}")
    else:
        print("error setting up dbm")

def rtc_setup():
    global wifi_connected
    # Setup RTC
    return rtc.setup(wifi_connected=wifi_connected)


# Setup sensors
def setup():
    # connect wifi
    connect_wifi() if not DEBUG else print("debug mode")

    # SPI PERIPHERALS SETUP
    # set up BME280
    print("BME280 test (Using SPI connection)")
    bme280_setup()
    print("BME280 setup complete")
    
    # I2C PERIPHERALS SETUP
    i2c_sensors = i2c.scan()
    print(f"Connected I2C sensors: {i2c_sensors}")

    # dbm sensor setup
    if dbm.DBM_I2C_ADDR in i2c_sensors:
        print("Setting up Sound Decibel Meter")
        dbm_setup()
        print("Sound Decibel Meter setup complete")
    # RTC setup
    if rtc.ADDR in i2c_sensors:
        print("setting up RTC")
        time = rtc_setup()
        if time:
            print(f"set up RTC. Current time: {time}")
        else:
            print("Failed to setup RTC")

# Main loop
def main_loop():
    delay_time = 2.5  # seconds

    while True:
        # Read decibel values
        db_array = dbm.get_db()
        if db_array:
            curr_time = rtc.get_time()
            print(f"Current time: {curr_time}")
            
            avg_db = db_array[0]
            min_db = db_array[1]
            max_db = db_array[2]
            print(f"dB reading = {avg_db:03d} \t [MIN: {min_db:03d} \tMAX: {max_db:03d}]")

            temperature, pressure, humidity = bme.read_compensated_data()
            print(f"Temperature: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f}%")

            # Assemble JSON with dB SPL reading
            DBMjson = f'{{"time": {curr_time}, "db": {avg_db}, "temperature": {temperature}}}'
            print("JSON: \n" + DBMjson)

            # Make a POST request with the data
            if not DEBUG:
                if network.WLAN(network.STA_IF).isconnected():
                    try:
                        response = urequests.post("https://demo.thingsboard.io/api/v1/MpvD4JYOpDvbKIJLvFif/telemetry", 
                                                data=DBMjson, 
                                                headers={'Content-Type': 'application/json'})
                        print(response.status_code)
                        print(response.text)
                        response.close()
                    except Exception as e:
                        print(f"Error on sending POST: {e}")
                else:
                    print("Something wrong with WiFi?")
            
        time.sleep(delay_time)

# Run setup and main loop
if __name__ == "__main__":
    setup()
    main_loop()
