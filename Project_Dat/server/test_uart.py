import serial
import RPi.GPIO as GPIO
import time
import threading
from queue import Queue
from soft_timer import Soft_Timer
import struct
DE_PIN=18    #12
RE_PIN=23    #16



class MobusInputRegister:
    def __init__(self):
        self.reg_temp=0
        self.reg_humidity=0
        self.reg_sound=0
        self.reg_viberation=0
        
    def save_value_in_input_register(self,value, addr_reg_offset):
        try:
            addr_reg = addr_reg_offset + 30001  # Base address ADDR_INPUT_REG is 30001
            shift = 0
            ptr=None
            # Identify which register the address corresponds to and store the value
            if 30001 <= addr_reg < 30005:  # ADDR_REG_TEMPERATE (30001 to 30004)
                ptr = 'reg_temp'
                shift = addr_reg - 30001
            elif 30005 <= addr_reg < 30009:  # ADDR_REG_HUMIDITY (30005 to 30008)
                ptr = 'reg_humidity'
                shift = addr_reg - 30005
            elif 30009 <= addr_reg < 30013:  # ADDR_REG_SOUND (30009 to 30012)
                ptr = 'reg_sound'
                shift = addr_reg - 30009
            elif 30013 <= addr_reg < 30017:  # ADDR_REG_VIBRATION (30013 to 30016)
                ptr = 'reg_viberation'
                shift = addr_reg - 30013
            
            if ptr:
                reg_value = getattr(self, ptr)  # Get the current register value
                reg_value = bytearray(struct.pack('>I', reg_value))  # Convert to bytearra
                reg_value[shift] = value  # Set the byte at the correct position
                setattr(self, ptr, struct.unpack('>I', bytes(reg_value))[0])  # Update the register value
                
        except Exception as error:
            print(error)

    def save_multi_value_in_input_register(self, data, addr_reg_offset, num):
    # Save multiple values from data into registers based on addr_reg_offset
        try:
            for i in range(num):
                reg_tmp = addr_reg_offset + i
                self.save_value_in_input_register(data[i], reg_tmp) 
        except Exception as err:
            print(err)
            
       
class ModbusManager:
    def __init__(self):
        self.READ_COILS = 1
        self.READ_INPUT_DISCRETES = 2
        self.READ_HOLDING_REGISTERS = 3
        self.READ_INPUT_REGISTERS = 4
        self.WRITE_SINGLE_COIL = 5
        self.WRITE_SINGLE_REGISTER = 6
        self.WRITE_MULTIPLE_COILS = 15
        self.WRITE_MULTIPLE_REGISTERS = 16
        
        self.ADDR_INPUT_REG = 30001
        self.ADDR_HOLDING_REG = 40001
        self.ADDR_COIL = 1
        self.ADDR_DISCRETE_INPUT = 10001
        # Define specific register addresses based on the base address
        self.ADDR_REG_TEMPERATURE = self.ADDR_INPUT_REG + 0
        self.ADDR_REG_HUMIDITY = self.ADDR_INPUT_REG + 4
        self.ADDR_REG_SOUND = self.ADDR_INPUT_REG + 8
        self.ADDR_REG_VIBRATION = self.ADDR_INPUT_REG + 12 
        self.InputRegister=MobusInputRegister()
                
    
    def init_rtu_frame_request(self,addr_slave, fc, addr_reg, num):
        frame = bytearray(8)  # Initialize bytearray with 8 bytes
        frame[0] = addr_slave
        frame[1] = fc
        frame[2] = (addr_reg >> 8) & 0x00FF
        frame[3] = addr_reg & 0x00FF
        frame[4] = (num >> 8) & 0x00FF
        frame[5] = num & 0x00FF
        crc = self.calculate_crc16_modbus(frame[:6])  # Calculate CRC for first 6 bytes
        frame[6] = crc & 0x00FF
        frame[7] = (crc >> 8) & 0x00FF
        return frame
    
    def check_function_code(self,fc):
        list_fc = [1, 2, 3, 4, 5, 6, 15, 16]
        return fc in list_fc
    
    def check_crc(self,crc_l, crc_h, data, length):
        if length > 2:
            crc_l_ = data[length - 2]
            crc_h_ = data[length - 1]
            crc = self.calculate_crc16_modbus(data[:length - 2])
            crc_l = crc & 0x00FF
            crc_h = (crc >> 8) & 0x00FF
            return crc_l == crc_l_ and crc_h == crc_h_
        return False
    
    def check_rtu_frame(self,addr_slave, data, length):
        if length >= 8:
            addr_slave_ = data[0]
            fc_ = data[1]
            if addr_slave != addr_slave_:
                return False
            if not self.check_function_code(fc_):
                return False
            crc_l_ = data[length - 2]
            crc_h_ = data[length - 1]
            if not self.check_crc(crc_l_, crc_h_, data, length):
                return False
            return True
        return False
    
    def calculate_crc16_modbus(self,data):
    # Bảng CRC16 Modbus
        crc_table = [
            0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
            0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
            0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
            0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
            0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
            0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
            0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
            0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
            0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
            0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
            0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
            0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
            0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
            0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
            0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
            0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
            0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
            0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
            0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
            0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
            0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
            0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
            0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
            0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
            0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
            0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
            0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
            0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
            0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
            0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
            0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
            0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
        ]

        crc_word = 0xFFFF

        for byte in data:
            n_temp = (byte ^ crc_word) &0x00FF
            crc_word >>= 8
            crc_word ^= crc_table[n_temp]

        return crc_word
    
    def ieee754_to_float(self,val):
        return struct.unpack('!f', struct.pack('!I', val))[0]
    
    def process_response(self,addr_slave,data,len, addr_reg_offset):
        if self.check_rtu_frame(addr_slave,data,len):
            print('check frame ok') 
            fc= data[1]
            if fc==self.READ_INPUT_REGISTERS:
                print('process_frame_input_registrer_response')
                self.process_frame_input_registrer_response(data,len,addr_reg_offset)
                
                print(f'{self.InputRegister.reg_temp} | {self.ieee754_to_float(self.InputRegister.reg_temp)}')
                print(f'{self.InputRegister.reg_humidity} | {self.ieee754_to_float(self.InputRegister.reg_humidity)}')
                print(f'{self.InputRegister.reg_sound} | {self.ieee754_to_float(self.InputRegister.reg_sound)}')
                print(f'{self.InputRegister.reg_viberation} | {self.ieee754_to_float(self.InputRegister.reg_viberation)}')
                return True
            else:
                print('fc not support')
                return False
                
    def process_frame_input_registrer_response(self,data,len,addr_reg_offset):
        addr_slave=data[0]
        fc=data[1]
        num= data[2]
        self.InputRegister.save_multi_value_in_input_register(data[3:],addr_reg_offset,num)

 
class MessageFormat:
    
    def __init__(self,bytes_data=None):
        
        if isinstance(bytes_data, str):
            self.data = bytes_data.encode('ascii')  # Chuyển chuỗi thành byte theo mã ASCII
        else:
            self.data = bytes_data  # Giả sử nếu là mảng byte, lưu trữ trực tiếp
    
    def to_default_format(self):
        ret=bytearray([0x02])
        ret.extend(self.data)
        ret.append(0x03)
        return ret
            
class UartManager:
    
    def __init__(self,ser:serial.Serial,DE_pin=None,RE_pin=None,timeout_s=10,timeout_callback=None,finish_callback=None):
        self.ser=ser
        self.status_mutex=threading.Lock()
        self.status_uart='free'
        self.buff_rx=bytearray()
        self.buff_tx=bytearray()
        self.queue=Queue()
        self.timeout_callback=timeout_callback
        self.finish_callback=finish_callback
        self.timer=None
        # self.process_thread=threading.Thread(target=self._process_data,deamon=True)
        # self.process_thread.start()
        self.pre_bytes_in_buffer=0
        self.DE_PIN=DE_pin
        self.RE_PIN=RE_pin
        self.timeout_s=timeout_s
       
        if DE_pin is not None  and  RE_PIN is not None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(DE_pin,GPIO.OUT)
            GPIO.setup(RE_pin,GPIO.OUT)
        
        self.time_s=self._get_wait_time_ms_from_baud(ser.baudrate)/1000
        self.time_3_5_char_s=self._get_time_3_5_char_ms(ser.baudrate)/1000
        self.timer_tick=0
        self.timeout_tick= timeout_s/self.time_s
        
        self.enable_mode_receive()
        self.start_timer()  
    
        
    def enable_mode_transmit(self):
        GPIO.output(self.DE_PIN,GPIO.HIGH)
        GPIO.output(self.RE_PIN,GPIO.HIGH)
        time.sleep(self.time_3_5_char_s)
        
    def enable_mode_receive(self):        
        GPIO.output(self.DE_PIN,GPIO.LOW)
        GPIO.output(self.RE_PIN,GPIO.LOW)
        time.sleep(self.time_3_5_char_s)
        
    def _get_time_3_5_char_ms(self,baud):
        return  (8/baud)*3.5*1000
        
    def start_timer(self):
    # Tạo một đối tượng timer mới để gọi hàm timer_callback sau interval giây
        self.timer = threading.Timer(self.time_s, self.timer_callback)
        self.timer.start()  # Bắt đầu timer

    def stop_timer(self):
    # Hủy bỏ timer nếu nó chưa thực thi
        if self.timer is not None:
            self.timer.cancel()
            print("Timer đã bị hủy.")
        else:
            print("Không có timer nào để hủy.")
    
    def register_timeout_callback(self,callback):
        self.timeout_callback=callback

    def register_finish_callback(self,callback):
        self.finish_callback=callback

    def get_buffer(self):
        return self.buffer[:self.buffer_size]
    
    def send_uart(self,data):
        with self.status_mutex:
            if self.status_uart=='free':
                self.buff_tx.clear()
                self.buff_tx.extend(data)
                
                self.enable_mode_transmit()
                self.ser.write(self.buff_tx)
                self.ser.flush()
                time.sleep(self.time_3_5_char_s) 
                
                self.enable_mode_receive()
                self.buff_rx.clear()
                self.status_uart='busy'
    
    def timer_callback(self):
        with self.status_mutex:
            if self.status_uart=='busy':
                bytes_in_buffer=self.ser.in_waiting
                if(bytes_in_buffer>0):  
                    if self.pre_bytes_in_buffer <bytes_in_buffer:
                        self.pre_bytes_in_buffer=bytes_in_buffer
                    elif self.pre_bytes_in_buffer==bytes_in_buffer:
                        self.pre_bytes_in_buffer=0
                        self.status_uart='finish'
                        data=self.ser.read(bytes_in_buffer)  #doc buffer 
                        self.buff_rx.extend(data)
                        if self.finish_callback:
                            ret=self.finish_callback(self.buff_rx,self.buff_tx)
                            if ret==True:
                                self.timer_tick=0                               
                                self.buff_rx.clear()
                                self.buff_tx.clear()
                                self.status_uart='free'
                            else:
                                self.buff_rx.clear()
                                self.status_uart='busy'
                else:
                    self.timer_tick=self.timer_tick+1
                    if self.timer_tick>self.timeout_tick:
                        print(self.timer_tick)
                        self.timer_tick=0
                        self.status_uart='timeout'
                        if self.timeout_callback:
                            self.timeout_callback()
                            self.buff_tx.clear()
                            self.buff_rx.clear()
                        self.status_uart='free'
        self.start_timer()     
    def free(self):

        if self.timer is not None:
            self.timer.cancel()
            print("Timer đã bị hủy.")
            
        if self.ser is not None:
            self.ser.close()
            print("Kết nối UART đã được đóng.")
        
        if self.DE_PIN is not None and self.RE_PIN is not None:
            GPIO.cleanup()
            print("GPIO đã được giải phóng.")

        del self.status_mutex
        print("Tài nguyên đã được giải phóng.")
        
    def _get_wait_time_ms_from_baud(self,baud):
        time_ms= (int) ((8/baud)*10*1000)
        return time_ms
                                                     
##################################################################################################

def finish_callback(buff_rx,buff_tx):
    print(buff_rx)
    try:
        addr_slave=buff_tx[0]
        addr_reg_h=buff_tx[2]
        addr_reg_l=buff_tx[3]
        addr_reg_offset=addr_reg_h*256+addr_reg_l
        modbus=ModbusManager()
        return modbus.process_response(addr_slave,buff_rx,len(buff_rx),addr_reg_offset)
    except:
        return False

def timout_callback():
    print('timout...')

def read_slaves(uart:UartManager):
    addr_slave=0
    data=ModbusManager().init_rtu_frame_request(addr_slave,4,0,16); 
    print(data)
    uart.send_uart(data)

def main():
    try:
        print('start main')
        ser = serial.Serial(port='/dev/ttyAMA4',
                            baudrate=9600,
                            parity=serial.PARITY_NONE,
                            bytesize=serial.EIGHTBITS,
                            stopbits=serial.STOPBITS_ONE)
        
        u1=UartManager(ser,DE_PIN,RE_PIN,finish_callback=finish_callback,timeout_callback=timout_callback,timeout_s=5) 
        sw_timer=Soft_Timer()
        sw_timer.register('READ_SLAVES',read_slaves,u1,10)
        sw_timer.start()
        
        while True:
            time.sleep(1)
    finally:
            u1.free()

                   
######################################################
if __name__=="__main__":
    main() 