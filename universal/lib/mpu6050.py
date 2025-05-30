import time
from math import atan, sqrt, pi

# Translated from https://github.com/rfetick/MPU6050_light
# and from https://github.com/adamjezek98/MPU6050-ESP8266-MicroPython
class mpu6050:
  def __init__(self, i2c):
    # ADDRESSES
    self.MPU6050_ADDR                  = 0x68
    self.MPU6050_SMPLRT_DIV_REGISTER   = 0x19
    self.MPU6050_CONFIG_REGISTER       = 0x1a
    self.MPU6050_GYRO_CONFIG_REGISTER  = 0x1b
    self.MPU6050_ACCEL_CONFIG_REGISTER = 0x1c
    self.MPU6050_PWR_MGMT_1_REGISTER   = 0x6b

    self.MPU6050_GYRO_OUT_REGISTER     = 0x43
    self.MPU6050_ACCEL_OUT_REGISTER    = 0x3B

    self.RAD_2_DEG                     = 57.29578 # [deg/rad], unused
    self.CALIB_OFFSET_NB_MES           = 250
    self.TEMP_LSB_2_DEGREE             = 340.0    # [bit/celsius]
    self.TEMP_LSB_OFFSET               = 12412.0

    self.DEFAULT_GYRO_COEFF            = 0.75

    # I2C
    self.i2c = i2c
    self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_PWR_MGMT_1_REGISTER, bytes([0]))

    # Pre Calcs
    self.setFilterGyroCoef(self.DEFAULT_GYRO_COEFF)
    self.setGyroOffsets(0,0,0)
    self.setAccOffsets(0,0,0)

    self.begin(1, 0)

  def begin(self, gyro_config_num, acc_config_num):
    self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_PWR_MGMT_1_REGISTER, bytes([0x01]))
    self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_SMPLRT_DIV_REGISTER, bytes([0x00]))
    self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_CONFIG_REGISTER, bytes([0x00]))
    
    # Timer
    self.preInterval = time.ticks_ms()
    
    self.setGyroConfig(gyro_config_num)
    self.setAccConfig(acc_config_num)
    self.calcOffsets(True, False)
    self.calcOffsets(False, True)

    self.angleX = 0
    self.angleY = 0
    self.angleZ = 0 
    
    self.accelX = 0
    self.accelY = 0
    self.accelZ = 0 
    
    self.gyroX = 0
    self.gyroY = 0
    self.gyroZ = 0 
    
    self.update()

  def bytes_toint(self, firstbyte, secondbyte):
    if not firstbyte & 0x80:
      return firstbyte << 8 | secondbyte
    return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

  def setGyroConfig(self, config_num):
    if config_num == 0: # range = +- 250 deg/s
      self.gyro_lsb_to_degsec  = 131.0
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_GYRO_CONFIG_REGISTER, bytes([0x00]))
    elif config_num == 1: # range = +- 500 deg/s
      self.gyro_lsb_to_degsec  = 65.5
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_GYRO_CONFIG_REGISTER, bytes([0x08]))
    elif config_num == 2: # range = +- 1000 deg/s
      self.gyro_lsb_to_degsec  = 32.8
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_GYRO_CONFIG_REGISTER, bytes([0x10]))
    elif config_num == 3: # range = +- 2000 deg/s
      self.gyro_lsb_to_degsec  = 16.4
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_GYRO_CONFIG_REGISTER, bytes([0x18]))

  def setAccConfig(self, config_num):
    if config_num == 0: # range = +- 2 g
      self.acc_lsb_to_g = 16384.0
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_CONFIG_REGISTER, bytes([0x00]))
    elif config_num == 1: # range = +- 4 g
      self.acc_lsb_to_g = 8192.0
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_CONFIG_REGISTER, bytes([0x08]))
    elif config_num == 2: # range = +- 8 g
      self.acc_lsb_to_g = 4096.0
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_CONFIG_REGISTER, bytes([0x10]))
    elif config_num == 3: # range = +- 16 g
      self.acc_lsb_to_g = 2048.0
      self.i2c.writeto_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_CONFIG_REGISTER, bytes([0x18]))

  def setGyroOffsets(self, x, y, z):
    self.gyroXoffset = x
    self.gyroYoffset = y
    self.gyroZoffset = z

  def setAccOffsets(self, x, y, z):
    self.accXoffset = x
    self.accYoffset = y
    self.accZoffset = z

  def setFilterGyroCoef(self, gyro_coeff):
    if (gyro_coeff < 0) or (gyro_coeff > 1): 
      gyro_coeff = self.DEFAULT_GYRO_COEFF # prevent bad gyro coeff, should throw an error...
    self.filterGyroCoef = gyro_coeff
  
  def setFilterAccCoef(self, acc_coeff):
    self.setFilterGyroCoef(1.0-acc_coeff)

  def calcOffsets(self, is_calc_gyro, is_calc_acc):
    print("Kalibrace GYRO senzoru ! Nehybat se snimacem !")
    if is_calc_gyro:
      self.setGyroOffsets(0, 0, 0)
    if is_calc_acc:
      self.setAccOffsets(0, 0, 0)
    ag = [0., 0., 0., 0., 0., 0.]

    for i in range(self.CALIB_OFFSET_NB_MES):
      data = self.fetchData()
      ag[0] += data["AcX"]
      ag[1] += data["AcY"]
      ag[2] += data["AcZ"] - 1
      ag[3] += data["GyX"]
      ag[4] += data["GyY"]
      ag[5] += data["GyZ"]
      time.sleep(1e-3)
    
    
    
    if is_calc_acc:
      print("Akcelerometr zkalibrovan.")
      self.accXoffset = ag[0] / self.CALIB_OFFSET_NB_MES
      self.accYoffset = ag[1] / self.CALIB_OFFSET_NB_MES
      self.accZoffset = ag[2] / self.CALIB_OFFSET_NB_MES
  
    if is_calc_gyro:
      print("Gyroskop zkalibrovan.")
      self.gyroXoffset = ag[3] / self.CALIB_OFFSET_NB_MES
      self.gyroYoffset = ag[4] / self.CALIB_OFFSET_NB_MES
      self.gyroZoffset = ag[5] / self.CALIB_OFFSET_NB_MES

  def fetchData(self):
    #I2C
    rawData = self.i2c.readfrom_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_OUT_REGISTER, 14)

    raw_ints = rawData
    vals = {}
    vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1]) / self.acc_lsb_to_g - self.accXoffset
    vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3]) / self.acc_lsb_to_g - self.accYoffset
    vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5]) / self.acc_lsb_to_g - self.accZoffset
    
    vals["Tmp"] = (self.bytes_toint(raw_ints[6], raw_ints[7]) + self.TEMP_LSB_OFFSET) / self.TEMP_LSB_2_DEGREE
   
    vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9]) / self.gyro_lsb_to_degsec - self.gyroXoffset
    vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11]) / self.gyro_lsb_to_degsec - self.gyroYoffset
    vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13]) / self.gyro_lsb_to_degsec - self.gyroZoffset

    return vals

  def update(self):
    data = self.fetchData()
    accX = data["AcX"]
    accY = data["AcY"]
    accZ = data["AcZ"]
    gyroX = data["GyX"]
    gyroY = data["GyY"]
    gyroZ = data["GyZ"]

    sgZ = (accZ>=0)-(accZ<0) # allow one angle to go from -180 to +180 degrees
    angleAccX = atan(accY / sqrt(accZ**2 + accX**2)) *  self.RAD_2_DEG # [-180,+180] deg
    angleAccY = atan(accX / sqrt(accZ**2 + accY**2)) * -self.RAD_2_DEG # [- 90,+ 90] deg

    dt = time.ticks_diff(time.ticks_ms(), self.preInterval) * 1e-3

    self.angleX = self.filterGyroCoef*(self.angleX + gyroX*dt) + (1 - self.filterGyroCoef)*angleAccX
    self.angleY = self.filterGyroCoef*(self.angleY + gyroY*dt) + (1 - self.filterGyroCoef)*angleAccY
    self.angleZ += gyroZ*dt
    
    self.accelX = accX
    self.accelY = accY
    self.accelZ = accZ
    
    self.gyroX = gyroX
    self.gyroY = gyroY
    self.gyroZ = gyroZ
    
    self.preInterval = time.ticks_ms()
  
  # GETTERS
  def getAngles(self):
    if (time.ticks_ms() > (self.preInterval + 10)):
        self.update()
    return self.angleX, self.angleY, self.angleZ
  
  def getAccel(self):
    if (time.ticks_ms() > (self.preInterval + 10)):
        self.update()
    return self.accelX, self.accelY, self.accelZ
  
  def getGyro(self):
    if (time.ticks_ms() > (self.preInterval + 10)):
        self.update()
    return self.gyroX, self.gyroY, self.gyroZ
    
  def getTemp(self):
    rawData = self.i2c.readfrom_mem(self.MPU6050_ADDR, self.MPU6050_ACCEL_OUT_REGISTER, 14)
    raw_ints = rawData
    return ((self.bytes_toint(raw_ints[6], raw_ints[7]) + self.TEMP_LSB_OFFSET) / self.TEMP_LSB_2_DEGREE)

  def getRawData(self):
    return self.fetchData()
