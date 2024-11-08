from machine import I2C, Pin
import time

class DBM_I2C:
    # CONSTANTS
    DBM_I2C_ADDR = 0x48
    VERSION_REG = 0x00
    REG_ID3 = 0x01
    REG_ID2 = 0x02
    REG_ID1 = 0x03
    REG_ID0 = 0x04
    
    SCRATCH_REG = 0X05
    CONTROL_REG = 0X06
    TAVG_HIGH_REG = 0X07
    TAVG_LOW_REG = 0X08
    
    AVG_DECIBEL_REG = 0x0A
    MIN_DECIBEL_REG = 0x0B
    MAX_DECIBEL_REG = 0x0C

    FREQ_64BIN0 = 0x78
    FREQ_64BIN63 = 0xB7

    def __init__(self, i2c) -> None:

        # initialization
        self.i2c = i2c

        # DM device info
        self._version = None
        self._reg_id = None
        self._scratch = None

    # Function to read a register from decibel meter
    def _read_reg(self, regaddr):
        data = self.i2c.readfrom_mem(self.DBM_I2C_ADDR, regaddr, 1)
        return data[0]

    def _write_reg(self, regaddr, value) -> bool:
        try:
            self.i2c.writeto_mem(self.DBM_I2C_ADDR, regaddr, bytes([value]))
            return True
        except Exception as e:
            print(f"error writing {value} to register {regaddr}: \n {e}")
            return False
    
    @property
    def version(self):
        if self._version is None:
            try:
                self._version = self._read_reg(self.VERSION_REG)
            except Exception as e:
                print(f"Error reading version register: {e}")
                self._version = "unknown"
        return self._version

    @property
    def reg_id(self):
        if self._reg_id is None:
            try:
                id0 = self._read_reg(self.REG_ID0)
                id1 = self._read_reg(self.REG_ID1)
                id2 = self._read_reg(self.REG_ID2)
                id3 = self._read_reg(self.REG_ID3)
                id_array = [id0, id1, id2, id3]
                self._reg_id = id_array
            except Exception as e:
                print(f"Error reading id register: {e}")
                self._reg_id = "unknown"
        return self._reg_id
    
    @property
    def scratch(self):
        if self._scratch is None:
            try:
                self._scratch = self._read_reg(self.SCRATCH_REG)
            except Exception as e:
                print(f"Error reading scratch register: {e}")
                self._scratch = "unknown"
        return self._scratch
    
    def set_configuration(self, update_speed = 1000, scratch_value = 1):
        try:
            self._write_reg(self.SCRATCH_REG, scratch_value)
            self._write_reg(self.TAVG_HIGH_REG, update_speed)
            self._write_reg(self.TAVG_LOW_REG, update_speed)
            return True
        except Exception as e:
            print(f"Error setting configuration: \n {e}")
            return False
    
    def get_db(self):
        try:
            db_data = []

            avg_db = self._read_reg(self.AVG_DECIBEL_REG)
            min_db = self._read_reg(self.MIN_DECIBEL_REG)
            max_db = self._read_reg(self.MAX_DECIBEL_REG)

            db_data.extend([avg_db, min_db, max_db])

            # for i in range(64):
            #     db_data.append(self._read_reg(self.FREQ_64BIN0 + i))
            
            return db_data

        except Exception as e:
            print(f"Error getting sound decibel data: \n {e}")
            return False