import uRAD_USB_SDK11  # Ensure uRAD_USB_SDK11 is compatible with MicroPython
from machine import UART, Pin
from time import sleep

# True if USB, False if UART
usb_communication = False

# Input parameters
mode = 1                  # Doppler mode
f0 = 125                  # Output continuous frequency 24.125 GHz
BW = 240                  # Doesn't apply in Doppler mode (mode = 1)
Ns = 200                  # 200 samples
Ntar = 3                  # 3 targets of interest
Vmax = 75                 # Searching along the full velocity range
MTI = 0                   # MTI mode disabled for static and moving targets
Mth = 0                   # Parameter not used as "movement" isn't requested
Alpha = 20                # Signal must be 20 dB higher than surrounding
distance_true = False     # Mode 1 doesn’t provide distance information
velocity_true = True      # Request velocity information
SNR_true = True           # Signal-to-Noise-Ratio information requested
I_true = False            # In-Phase Component (RAW data) not requested
Q_true = False            # Quadrature Component (RAW data) not requested
movement_true = False     # No boolean movement detection requested

# UART configuration
if not usb_communication:
	print("uart selected")
	uart = UART(2, baudrate=115200, tx=Pin(17), rx=Pin(16))

# Sleep time (seconds) between iterations
timeSleep = 0.005

# Helper function to close uRAD correctly
def close_program():
	return_code = uRAD_USB_SDK11.turnOFF(uart)
	print("turning off uRAD")
	if return_code != 0:
		raise SystemExit("Error turning off uRAD")

# Function to check if a list or element is non-empty
def is_non_empty(item):
	# Check if item is a list and contains non-zero values
	if isinstance(item, list):
		return any(val != 0 for val in item)
	# Check if item is a single value and is non-zero
	return item != 0 and item is not False

# Switch ON uRAD
print("turning on urad")
return_code = uRAD_USB_SDK11.turnON(uart if not usb_communication else None)
if return_code != 0:
	print("couldn't turn on uRAD")
	close_program()

# Load uRAD configuration
print("configuring uRAD")
return_code = uRAD_USB_SDK11.loadConfiguration(
	uart if not usb_communication else None,
	mode, f0, BW, Ns, Ntar, Vmax, MTI, Mth, Alpha,
	distance_true, velocity_true, SNR_true, I_true, Q_true, movement_true
)
if return_code != 0:
	print("couldn't configure uRAD")
	close_program()

# Main detection loop
print("running main detection loop")
while True:
	return_code, results, raw_results = uRAD_USB_SDK11.detection(uart if not usb_communication else None)
	if return_code != 0:
		close_program()

	# Filter out empty items in results and raw_results
	filtered_results = [item for item in results if is_non_empty(item)]
	filtered_raw_results = [item for item in raw_results if is_non_empty(item)]

	# Print non-empty filtered results
	if filtered_results:
		print("Filtered results:", filtered_results)
	if filtered_raw_results:
		print("Filtered raw_results:", filtered_raw_results)

	# # Process and display results
	# NtarDetected = results[0]
	# velocity = results[2]
	# SNR = results[3]

	# for i in range(NtarDetected):
	#     if SNR[i] > 0:
	#         print("Target: %d, Velocity: %1.1f m/s, SNR: %1.1f dB" % (i+1, velocity[i], SNR[i]))

	# if NtarDetected > 0:
	#     print(" ")

	sleep(timeSleep)
