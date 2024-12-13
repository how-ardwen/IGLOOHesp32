/*
 * uRAD_SDK11.h - Library for controlling uRAD SHIELD
 * Created by Victor Torres, Diego Gaston - uRAD 2020
 * Edited by Howard Wen for esp32 uart 2024
*/

#include "Arduino.h"
#include "uRAD_SDK11.h"

#define ACK 0xAA // (170)
#define NtarMax 5
#define f0Min 5
#define f0Max 195
#define f0Max_CW 245
#define BWMin 50
#define BWMax 240
#define NsMin 50
#define NsMax 200
#define RmaxMax 100
#define VmaxMax 75
#define alpha_min 3
#define alpha_max 25
#define command_loadConfiguration 14
#define command_detection 15
#define command_turnON 16
#define command_turnOFF 17
#define command_ready 18
#define command_results 19
#define command_I 20
#define command_Q 21

#define RX_PIN 16 // UART RX pin
#define TX_PIN 17 // UART TX pin

uRAD_SDK11::uRAD_SDK11() {
    Serial2.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN); // Initialize UART

	// TODO - switch off uRAD

    _get_distance = false;
    _get_velocity = false;
    _get_SNR = false;
    _get_I = false;
    _get_Q = false;
    _get_movement = false;
}

int uRAD_SDK11::loadConfiguration(uint8_t mode, uint8_t f0, uint8_t BW, uint8_t Ns, uint8_t Ntar, uint8_t Rmax, uint8_t MTI, uint8_t Mth, uint8_t alpha, bool distance_true, bool velocity_true, bool SNR_true, bool I_true, bool Q_true, bool movement_true) {
    // Variables
    uint8_t CRC;

    // Check correct values
    if ((mode == 0) || (mode > 4)) {
        mode = 3;
    }
    if ((f0 > f0Max) && (mode != 1)) {
        f0 = f0Min;
    } else if ((f0 > f0Max_CW) && (mode == 1)) {
        f0 = f0Min;
    } else if (f0 < f0Min) {
        f0 = f0Min;
    }
    uint8_t BW_available = BWMax - f0 + f0Min;
    if ((BW < BWMin) || (BW > BW_available)) {
        BW = BW_available;
    }
    if ((Ns < NsMin) || (Ns > NsMax)) {
        Ns = NsMax;
    }
    if ((Ntar == 0) || (Ntar > NtarMax)) {
        Ntar = 1;
    }
    if ((mode != 1) && ((Rmax < 1) || (Rmax > RmaxMax))) {
        Rmax = RmaxMax;
    } else if ((mode == 1) && (Rmax > VmaxMax)) {
        Rmax = VmaxMax;
    }
    if (MTI > 1) {
        MTI = 0;
    }
    if ((Mth == 0) || (Mth > 4)) {
        Mth = 4;
    }
    if (alpha < alpha_min) {
        alpha = alpha_min;
    } else if (alpha > alpha_max) {
        alpha = alpha_max;
    }
    Mth--;

    // Create _configuration register
    _configuration[0] = (mode << 5) + (f0 >> 3);
    _configuration[1] = (f0 << 5) + (BW >> 3);
    _configuration[2] = (BW << 5) + (Ns >> 3);
    _configuration[3] = (Ns << 5) + (Ntar << 2) + (Rmax >> 6);
    _configuration[4] = (Rmax << 2) + MTI;
    _configuration[5] = (Mth << 6) + (alpha << 1) + 0b00000001;
    _configuration[6] = 0;
    if (distance_true) {
        _configuration[6] = 0b10000000;
        _get_distance = true;
    }
    if (velocity_true) {
        _configuration[6] += 0b01000000;
        _get_velocity = true;
    }
    if (SNR_true) {
        _configuration[6] += 0b00100000;
        _get_SNR = true;
    }
    if (I_true) {
        _configuration[6] += 0b00010000;
        _get_I = true;
    }
    if (Q_true) {
        _configuration[6] += 0b00001000;
        _get_Q = true;
    }
    if (movement_true) {
        _configuration[6] += 0b00000100;
        _get_movement = true;
    }

    CRC = (uint8_t)(_configuration[0] + _configuration[1] + _configuration[2] + _configuration[3] + _configuration[4] + _configuration[5] + _configuration[6]);
    _configuration[7] = CRC;

    // Send configuration via UART
    Serial2.write(command_loadConfiguration);
    Serial2.write(_configuration, sizeof(_configuration));

    // Wait for acknowledgment
    unsigned long timeout = millis() + 200;
    while (millis() < timeout) {
        if (Serial2.available()) {
            uint8_t rx_ACK = Serial2.read();
            if (rx_ACK == ACK) {
                return 0; // Success
            }
        }
    }

    return -1; // Timeout or error
}

// int uRAD_SDK11::detection(uint8_t NtarDetected[], float distance[], float velocity[], float SNR[], uint16_t I[], uint16_t Q[],  bool movement[]) {

// 	// Variables
// 	uint8_t mode, Ns, Ns_3, Ns_temp, Ntar_temp, rx_ACK, results[NtarMax*3*4+2], buff_temp[4], read_timeout = 200;
// 	uint16_t i, total_bytes_int, two_blocks_1, two_blocks_2, two_blocks_3;
// 	float total_bytes;
// 	int return_code = 0;
// 	uint64_t t0, ti;

// 	NtarDetected[0] = 0;
// 	memset(distance,0,sizeof(distance));
// 	memset(velocity,0,sizeof(velocity));
// 	memset(SNR,0,sizeof(SNR));
// 	movement[0] = false;		
		
// 	if ((_get_I && I != 0) || (_get_Q && Q != 0)) {		
// 		mode = (_configuration[0] & 0b11100000) >> 5;
// 		Ns = ((_configuration[2] & 0b00011111) << 3) + ((_configuration[3] & 0b11100000) >> 5);
// 		Ns_temp = Ns;
// 		if (mode == 3) {
// 			Ns_temp = 2 * Ns_temp;
// 		} else if (mode == 4) {
// 			Ns_temp = 2 * Ns_temp + 2 * ceil(0.75 * Ns_temp);
// 		}		
// 		total_bytes = 0;
// 		if ((Ns % 2) == 0) {
// 			total_bytes += Ns*1.5;
// 			two_blocks_1 = floor(Ns*1.5/3);
// 		} else {
// 			total_bytes += (Ns+1)*1.5;
// 			two_blocks_1 = floor((Ns+1)*1.5/3);
// 		}
// 		if ((mode == 3) || (mode == 4)) {
// 			two_blocks_2 = two_blocks_1;
// 			total_bytes *= 2;
// 		}
// 		if (mode == 4) {
// 			Ns_3 = ceil(0.75*Ns);
// 			if ((Ns_3 % 2) == 0) {
// 				total_bytes += 2*Ns_3*1.5;
// 				two_blocks_3 = floor(Ns_3*1.5/3);
// 			} else {
// 				total_bytes += 2*(Ns_3+1)*1.5;
// 				two_blocks_3 = floor((Ns_3+1)*1.5/3);
// 			}
// 		}
// 		total_bytes_int = uint16_t(total_bytes);	
// 	}
	
// 	rx_ACK = 0;
// 	t0 = millis();
// 	ti = millis();
// 	while ((rx_ACK != ACK) && ((ti - t0) < read_timeout)) {
// 		Serial2.write(command_detection);
//         if (Serial2.available()) {
//             rx_ACK = Serial2.read();
//         }
//         ti = millis();
//     }
	
// 	if ((ti-t0) >= read_timeout) {
// 		return_code = -1;
// 	}
	
// 	if (return_code == 0) {
// 		// Results are ready?
// 		rx_ACK = 0;
// 		t0 = millis();
// 		ti = millis();
// 		while ((rx_ACK != ACK) && ((ti - t0) < read_timeout)) {
// 			Serial2.write(command_ready);
// 			if (Serial2.available()) {
// 				rx_ACK = Serial2.read();
// 			}
// 			ti = millis();
// 		}
// 		if ((ti-t0) >= read_timeout) {
// 			return_code = -1;
// 		}
		
// 		if (return_code == 0) {
// 			// Receive results			
// 			if (_get_distance || _get_velocity || _get_SNR || _get_movement) {
// 				digitalWrite(pin_SS, LOW);
// 				delayMicroseconds(500);
// 				SPI.transfer(command_results);
// 				delayMicroseconds(500);
// 				SPI.transfer(results, sizeof(results));
// 				digitalWrite(pin_SS, HIGH);
				
// 				Ntar_temp = (_configuration[3] & 0b00011100) >> 2;
// 				for (i = 0; i < Ntar_temp; i++) {
// 					if ((_get_distance) && (distance !=0)) {
// 						buff_temp[0] = results[i*4];
// 						buff_temp[1] = results[i*4+1];
// 						buff_temp[2] = results[i*4+2];
// 						buff_temp[3] = results[i*4+3];
// 						distance[i] = *((float*)(buff_temp));
// 					}
// 					if ((_get_velocity) && (velocity !=0)) {
// 						buff_temp[0] = results[NtarMax*4+i*4];
// 						buff_temp[1] = results[NtarMax*4+i*4+1];
// 						buff_temp[2] = results[NtarMax*4+i*4+2];
// 						buff_temp[3] = results[NtarMax*4+i*4+3];
// 						velocity[i] = *((float*)(buff_temp));
// 					}
// 					buff_temp[0] = results[NtarMax*8+i*4];
// 					buff_temp[1] = results[NtarMax*8+i*4+1];
// 					buff_temp[2] = results[NtarMax*8+i*4+2];
// 					buff_temp[3] = results[NtarMax*8+i*4+3];
// 					SNR[i] = *((float*)(buff_temp));
// 					if (SNR[i] != 0) {
// 						NtarDetected[0] += 1;
// 					}
// 				}
// 				if ((!_get_SNR) || (SNR == 0)) {
// 					memset(SNR,0,sizeof(SNR));
// 				}
// 				if (_get_movement && (movement != 0)) {
// 						if (results[NtarMax*12] == 255) {
// 							movement[0] = true;
// 						} 
// 				}			
// 			}
			
// 			if(_get_I && (I!=0)) {		
// 				// Receive RAW I signal
// 				uint8_t bufferTbytes[total_bytes_int];				
// 				memset(bufferTbytes,0,sizeof(bufferTbytes));
// 				digitalWrite(pin_SS, LOW);				
// 				delayMicroseconds(500);
// 				SPI.transfer(command_I);
// 				delayMicroseconds(500);
// 				for (i = 0; i < total_bytes_int; i++) {
// 					bufferTbytes[i] = SPI.transfer(0);
// 				}
// 				digitalWrite(pin_SS, HIGH);				
								
// 				for (i = 0; i < two_blocks_1; i++) {
// 					I[i*2+0] = (bufferTbytes[i*3+0] << 4) + (bufferTbytes[i*3+1] >> 4);
// 					if ((i*2+1) <= (Ns-1)) {
// 						I[i*2+1] = ((bufferTbytes[i*3+1] & 15) << 8) + bufferTbytes[i*3+2];
// 					}
// 				}
// 				if ((mode == 3) || (mode == 4)) {
// 					for (i = 0; i < two_blocks_2; i++) {
// 						I[Ns+i*2+0] = (bufferTbytes[(two_blocks_1+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+i)*3+1] >> 4);
// 						if ((Ns+i*2+1) <= (2*Ns-1)) {
// 							I[Ns+i*2+1] = ((bufferTbytes[(two_blocks_1+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+i)*3+2];
// 						}
// 					}
// 					if (mode == 4) {
						
// 						for (i = 0; i < two_blocks_3; i++) {
// 							I[2*Ns+i*2+0] = (bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+1] >> 4);
// 							if ((2*Ns+i*2+1) <= (2*Ns+Ns_3-1)) {
// 								I[2*Ns+i*2+1] = ((bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+2];
// 							}
// 						}
// 						for (i = 0; i < two_blocks_3; i++) {
// 							I[2*Ns+Ns_3+i*2+0] = (bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+1] >> 4);
// 							if ((2*Ns+Ns_3+i*2+1) <= (2*Ns+2*Ns_3-1)) {
// 								I[2*Ns+Ns_3+i*2+1] = ((bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+2];
// 							}
// 						}						
// 					}
// 				}
// 			}
			
// 			if(_get_Q && (Q!=0)) {		
// 				// Receive RAW Q signal
// 				uint8_t bufferTbytes[total_bytes_int];
// 				memset(bufferTbytes,0,sizeof(bufferTbytes));
// 				digitalWrite(pin_SS, LOW);
// 				delayMicroseconds(500);
// 				SPI.transfer(command_Q);
// 				delayMicroseconds(500);
// 				for (i = 0; i < total_bytes_int; i++) {
// 					bufferTbytes[i] = SPI.transfer(0);
// 				}
// 				digitalWrite(pin_SS, HIGH);	
				
// 				for (i = 0; i < two_blocks_1; i++) {
// 					Q[i*2+0] = (bufferTbytes[i*3+0] << 4) + (bufferTbytes[i*3+1] >> 4);
// 					if ((i*2+1) <= (Ns-1)) {
// 						Q[i*2+1] = ((bufferTbytes[i*3+1] & 15) << 8) + bufferTbytes[i*3+2];
// 					}
// 				}
// 				if ((mode == 3) || (mode == 4)) {
// 					for (i = 0; i < two_blocks_2; i++) {
// 						Q[Ns+i*2+0] = (bufferTbytes[(two_blocks_1+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+i)*3+1] >> 4);
// 						if ((Ns+i*2+1) <= (2*Ns-1)) {
// 							Q[Ns+i*2+1] = ((bufferTbytes[(two_blocks_1+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+i)*3+2];
// 						}
// 					}
// 					if (mode == 4) {
// 						for (i = 0; i < two_blocks_3; i++) {
// 							Q[2*Ns+i*2+0] = (bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+1] >> 4);
// 							if ((2*Ns+i*2+1) <= (2*Ns+Ns_3-1)) {
// 								Q[2*Ns+i*2+1] = ((bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+two_blocks_2+i)*3+2];
// 							}
// 						}
// 						for (i = 0; i < two_blocks_3; i++) {
// 							Q[2*Ns+Ns_3+i*2+0] = (bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+0] << 4) + (bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+1] >> 4);
// 							if ((2*Ns+Ns_3+i*2+1) <= (2*Ns+2*Ns_3-1)) {
// 								Q[2*Ns+Ns_3+i*2+1] = ((bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+1] & 15) << 8) + bufferTbytes[(two_blocks_1+two_blocks_2+two_blocks_3+i)*3+2];
// 							}
// 						}
// 					}
// 				}
// 			}
// 		}	
// 	}	
// 	SPI.endTransaction();
// 	return return_code;
// }

int uRAD_SDK11::turnON(void) {

	// variables
    uint8_t rx_ACK;
    unsigned long t0, ti, read_timeout = 200;

	// send turn on via UART
    Serial2.write(command_turnON);

	// receive uRAD acknowledgement before timeout
    rx_ACK = 0;
    t0 = millis();
    ti = millis();
    while ((rx_ACK != ACK) && ((ti - t0) < read_timeout)) {
		Serial2.write(command_turnON);
        if (Serial2.available()) {
            rx_ACK = Serial2.read();
        }
        ti = millis();
    }

    if (rx_ACK == ACK) {
        return 0;
    } else {
        return -1;
    }
}

int uRAD_SDK11::turnOFF(void) {

	// variables
    uint8_t rx_ACK;
    unsigned long t0, ti, read_timeout = 200;

	// send turn on via UART
    Serial2.write(command_turnOFF);

	// receive uRAD acknowledgement before timeout
    rx_ACK = 0;
    t0 = millis();
    ti = millis();
    while ((rx_ACK != ACK) && ((ti - t0) < read_timeout)) {
		Serial2.write(command_turnOFF);
        if (Serial2.available()) {
            rx_ACK = Serial2.read();
        }
        ti = millis();
    }

    if (rx_ACK == ACK) {
        return 0;
    } else {
        return -1;
    }
}