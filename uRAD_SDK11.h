/*
 * uRAD_SDK11.h - Library for controlling uRAD SHIELD
 * Created by Victor Torres, Diego Gaston - uRAD 2020
*/

#ifndef uRAD_SDK11_h
#define uRAD_SDK11_h
#include "Arduino.h"

class uRAD_SDK11
{
	public:
		uRAD_SDK11();
		int loadConfiguration(uint8_t mode, uint8_t f0, uint8_t BW, uint8_t Ns, uint8_t Ntar, uint8_t Rmax, uint8_t MTI, uint8_t Mth, uint8_t alpha, bool distance_true, bool velocity_true, bool SNR_true, bool I_true, bool Q_true, bool movement_true);
		int detection(uint8_t NtarDetected[], float distance[], float velocity[], float SNR[], uint16_t I[], uint16_t Q[],  bool movement[]);
		int turnON(void);
		int turnOFF(void);
	private:
		uint8_t _configuration[8];
		bool _get_distance;
		bool _get_velocity;
		bool _get_SNR;
		bool _get_I;
		bool _get_Q;
		bool _get_movement;
};

#endif
