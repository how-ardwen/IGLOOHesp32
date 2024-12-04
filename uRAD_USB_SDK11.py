import math
import struct
import time
from machine import UART

# Initialize configuration parameters
configuration = [0] * 8
NtarMax = 5
get_distance = False
get_velocity = False
get_SNR = False
get_I = False
get_Q = False
get_movement = False
results_packetLen = NtarMax * 3 * 4 + 2

def loadConfiguration(ser, mode, f0, BW, Ns, Ntar, Rmax, MTI, Mth, Alpha, distance_true, velocity_true, SNR_true, I_true, Q_true, movement_true):
	global configuration, get_distance, get_velocity, get_SNR, get_I, get_Q, get_movement
	
	# Setup and validate configuration values
	f0Min, f0Max, f0Max_CW, BWMin, BWMax = 5, 195, 245, 50, 240
	NsMin, NsMax, RmaxMax, VmaxMax, AlphaMin, AlphaMax = 50, 200, 100, 75, 3, 25

	# Ensuring parameters stay within their allowable ranges
	mode = 3 if mode == 0 or mode > 4 else mode
	f0 = min(max(f0, f0Min), f0Max_CW if mode == 1 else f0Max)
	BW = min(max(BW, BWMin), BWMax - f0 + f0Min)
	Ns = min(max(Ns, NsMin), NsMax)
	Ntar = max(1, min(Ntar, NtarMax))
	Rmax = min(max(Rmax, 1), VmaxMax if mode == 1 else RmaxMax)
	MTI, Mth = min(max(MTI, 0), 1), min(max(Mth, 1), 4) - 1
	Alpha = min(max(Alpha, AlphaMin), AlphaMax)
	
	# Construct the configuration byte array
	configuration[0] = ((mode << 5) + (f0 >> 3)) & 0xFF
	configuration[1] = ((f0 << 5) + (BW >> 3)) & 0xFF
	configuration[2] = ((BW << 5) + (Ns >> 3)) & 0xFF
	configuration[3] = ((Ns << 5) + (Ntar << 2) + (Rmax >> 6)) & 0xFF
	configuration[4] = ((Rmax << 2) + MTI) & 0xFF
	configuration[5] = ((Mth << 6) + (Alpha << 1) + 1) & 0xFF
	configuration[6] = 0
	if distance_true: configuration[6] += 0x80; get_distance = True
	if velocity_true: configuration[6] += 0x40; get_velocity = True
	if SNR_true:      configuration[6] += 0x20; get_SNR = True
	if I_true:        configuration[6] += 0x10; get_I = True
	if Q_true:        configuration[6] += 0x08; get_Q = True
	if movement_true: configuration[6] += 0x04; get_movement = True

	# Calculate CRC for the configuration
	configuration[7] = sum(configuration[:7]) & 0xFF

	# Send configuration to uRAD
	if ser.any() or True:  # Replace ser.is_open check
		a = ser.write(bytearray([14]))
		print(a)
		a = ser.write(bytearray(configuration[0:8]))
		print(a)
		configuration[5] &= 0xFE

		time.sleep(0.005)
		ACK = ser.read(1)
		print(ACK)
		if ACK and ACK[0] == 0xAA:
			return 0
	return -1

def detection(uart):
	global get_distance, get_velocity, get_SNR, get_I, get_Q, get_movement, NtarMax, configuration

	if get_distance or get_velocity or get_SNR:
		NtarDetected = 0
		distance = [0] * NtarMax
		velocity = [0] * NtarMax
		SNR = [0] * NtarMax
		movement = False
	else:
		NtarDetected = 0
		distance, velocity, SNR, movement = [], [], [], False

	if get_I or get_Q:
		mode = (configuration[0] & 0b11100000) >> 5
		Ns = ((configuration[2] & 0b00011111) << 3) + ((configuration[3] & 0b11100000) >> 5)
		Ns_temp = Ns
		if mode == 3:
			Ns_temp *= 2
		elif mode == 4:
			Ns_temp += Ns_temp + 2 * math.ceil(0.75 * Ns_temp)
		
		I = [0] * Ns_temp if get_I else []
		Q = [0] * Ns_temp if get_Q else []
	else:
		I, Q = [], []

	try:
		# Sending detection request
		uart.write(bytearray([15]))  # Send the detection command
		time.sleep(0.005)

		# Process results if required
		if get_distance or get_velocity or get_SNR or get_movement and results != None:
			# Read the result packet
			results = uart.read(results_packetLen)
			if results and len(results) == results_packetLen:
				Ntar_temp = (configuration[3] & 0b00011100) >> 2
				if get_distance:
					distance[0:Ntar_temp] = struct.unpack('<%df' % Ntar_temp, results[0:4 * Ntar_temp])
				if get_velocity:
					velocity[0:Ntar_temp] = struct.unpack('<%df' % Ntar_temp, results[NtarMax * 4:NtarMax * 4 + 4 * Ntar_temp])
				SNR[0:Ntar_temp] = struct.unpack('<%df' % Ntar_temp, results[2 * NtarMax * 4:2 * NtarMax * 4 + 4 * Ntar_temp])
				NtarDetected = sum(1 for snr in SNR if snr > 0)
				if not get_SNR:
					SNR = [0] * NtarMax

				if get_movement:
					movement = results[NtarMax * 12] == 255
			# else:
			# 	return -2, [], []

		# Receive I, Q data if requested
		if get_I or get_Q:
			total_bytes = int(Ns * 1.5) if Ns % 2 == 0 else int((Ns + 1) * 1.5)
			two_blocks_1 = math.floor(total_bytes / 3)
			if mode in (3, 4):
				total_bytes *= 2
			if mode == 4:
				Ns_3 = math.ceil(0.75 * Ns)
				total_bytes += int(2 * Ns_3 * 1.5) if Ns_3 % 2 == 0 else int(2 * (Ns_3 + 1) * 1.5)
				two_blocks_3 = math.floor((Ns_3 + 1) * 1.5 / 3)

			# Convert to integer to use with read
			total_bytes = int(total_bytes)

			# Read I component
			if get_I:
				bufferIbytes = uart.read(total_bytes)
				if bufferIbytes and len(bufferIbytes) == total_bytes:
					for i in range(two_blocks_1):
						I[i * 2] = (bufferIbytes[i * 3] << 4) + (bufferIbytes[i * 3 + 1] >> 4)
						if i * 2 + 1 <= Ns - 1:
							I[i * 2 + 1] = ((bufferIbytes[i * 3 + 1] & 15) << 8) + bufferIbytes[i * 3 + 2]
					# Additional handling for mode 3 and 4 if necessary

			# Read Q component
			if get_Q:
				bufferQbytes = uart.read(total_bytes)
				if bufferQbytes and len(bufferQbytes) == total_bytes:
					for i in range(two_blocks_1):
						Q[i * 2] = (bufferQbytes[i * 3] << 4) + (bufferQbytes[i * 3 + 1] >> 4)
						if i * 2 + 1 <= Ns - 1:
							Q[i * 2 + 1] = ((bufferQbytes[i * 3 + 1] & 15) << 8) + bufferQbytes[i * 3 + 2]
					# Additional handling for mode 3 and 4 if necessary
			else:
				return -2, [], []

		return 0, [NtarDetected, distance, velocity, SNR, movement], [I, Q]
	except Exception as e:
		print("Detection error:", e)
		return -2, [], []

def turnON(ser):
	try:
		if ser.any() or True:  # Replace ser.is_open check
			bytes_written = ser.write(bytearray([16]))
			print(bytes_written)

			time.sleep(0.005)
			ACK = ser.read(1)
			print(ACK)
			
			if ACK and ACK[0] == 0xAA:
				return 0
			else:
				return -1
	except Exception as e:
		print("Turn ON error:", e)
	return -1

def turnOFF(ser):
	try:
		if ser.any() or True:  # Replace ser.is_open check
			ser.write(bytearray([17]))
			ACK = ser.read(1)
			return 0 if ACK and ACK[0] == 0xAA else -1
	except Exception as e:
		print("Turn OFF error:", e)
	return -1