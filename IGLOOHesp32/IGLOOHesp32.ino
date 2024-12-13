#include "C:\Users\wenho\OneDrive - The University of Western Ontario\aNHP\Radar\IGLOOHesp32\uRAD_SDK11.cpp" 	// include the library

uRAD_SDK11 uRAD;       		// create the object uRAD

// input parameters
uint8_t mode, f0, BW, Ns, Ntar, Rmax, MTI, Mth, alpha;
bool distance_true, velocity_true, SNR_true, I_true, Q_true, movement_true;
int return_code;

// results output array
uint8_t NtarDetected[1];
float velocity[5], SNR[5];

void setup() {
	Serial.begin(115200);   	// serial port baud rate

	// mode = 1;					// doppler mode
	// f0 = 125;					// output continuous frequency 24.125 GHz
	// BW = 240;					// don't apply in doppler mode (mode = 1)
	// Ns = 200;					// 200 samples
	// Ntar = 3;					// 3 target of interest
	// Vmax = 75;					// searching along the full velocity range
	// MTI = 0;					// MTI mode disable because we want information of static and moving targets
	// Mth = 0;					// parameter not used because "movement" is not requested
	// alpha = 20;					// signal has to be 20 dB higher than its surrounding
	// distance_true = false; 		// request distance information
	// velocity_true = true;		// mode 2 does not provide velocity information
	// SNR_true = true; 			// Signal-to-Noise-Ratio information requested
	// I_true = false; 			// In-Phase Component (RAW data) not requested
	// Q_true = false; 			// Quadrature Component (RAW data) not requested
	// movement_true = false; 		// Not interested in boolean movement detection

	// switch ON uRAD
  return_code = uRAD.turnON();
	while (return_code != 0) {
		Serial.printf("Error turning on uRAD, return code: %d\n", return_code);
    return_code = uRAD.turnON();
    delay(1000);
  }
	
	// // load the configuration
	// return_code = uRAD.loadConfiguration(mode, f0, BW, Ns, Ntar, Vmax, MTI, Mth, alpha, distance_true, velocity_true, SNR_true, I_true, Q_true, movement_true);
	// if (return_code != 0) {
	// 	Serial.println("Error configuring uRAD");
	// }	

}

void loop() {
  Serial.println("Got to main loop. Yay!");
  int return_code = uRAD.turnOFF();
  if (return_code == 0) {
    Serial.println("turned off radar!");
  } else {
    Serial.printf("error turning off radar, code: %d\n", return_code);
  }
  delay(5000);
// 	// target detection request
// 	return_code = uRAD.detection(NtarDetected, 0, velocity, SNR, 0, 0, 0);

// 	// iterate through desired targets
// 	if (return_code == 0) {
// 		for (uint8_t i = 0; i < NtarDetected[0]; i++) {
// 			// if target is reflective enough, print its distance
// 			if (SNR[i] > 0){   
// 				Serial.print("Target: ");
// 				Serial.print(i+1);
// 				Serial.print(", Velocity: ");
// 				Serial.print(velocity[i]);
// 				Serial.print(" m/s, SNR: ");
// 				Serial.print(SNR[i]);
// 				Serial.println(" dB");
// 			}
// 		}
// 		// If number of detected targets is greater than 0 prints an empty line for a smarter output
// 		if (NtarDetected[0] > 0) {
// 			Serial.println(" ");	
// 		}
// 	} else {
// 		Serial.println("Error in detection");
// 	}
}