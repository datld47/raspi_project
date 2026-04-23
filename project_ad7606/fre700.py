import time
import datetime
from datetime import timezone
from datetime import datetime as dt
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
#40201-40207
factor=[0.01,0.01,0.1,0.0,0.01,0.0,0.1]
unit=['Hz','A','V','','Hz','','%']
choose=[0,1,6]
factor_choose=[ factor[i] for i in choose]

def get_now_timestamp():
    timestamp =  dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+'Z'
    return timestamp

def init_modbus_client(port='/dev/ttyUSB0',baurate=19200):
    client = ModbusSerialClient(
    port=port,
    baudrate=baurate,
    parity='E',
    stopbits=1,
    bytesize=8,
    timeout=1) # Tăng timeout lên một chút để bù cho nhiễu)
    return client 

def fre70_read_raw_data_continue(client,modbus_address=40201,count=7,choose=choose):
    try:
        # Không cần gọi client.connect() liên tục nếu đã connect ở ngoài
        if len(factor)!=count:
            return None
        pymodbus_address = modbus_address - 40001
        result = client.read_holding_registers(address=pymodbus_address, count=count, device_id=1)
        if result.isError():
            print(f"Lỗi Modbus: {result}")
            return None
        return [result.registers[i] for i in choose]
    except ModbusIOException:
        print("Lỗi I/O: Mất phản hồi từ biến tần.")
    except Exception as e:
        print(f"Lỗi không xác định: {e}")
    return None

def fre700_decode_data(raw_data_16,factor=factor_choose):
    if len(raw_data_16)==len(factor):
        return [val * f for val, f in zip(raw_data_16, factor)]
    print('loi factor')
    return None

if __name__ == "__main__":
    client=init_modbus_client()        
    try:
        client.connect()
        try:
            while True:
                start_tick = time.perf_counter()
                print(fre70_read_raw_data_continue(client,40201,7))     
                elapsed = time.perf_counter() - start_tick
                if(elapsed<0.1):
                    print(f'elapsed={elapsed}')
                else:
                    print('loi')
                time.sleep(max(0, 0.1 - elapsed))
        except KeyboardInterrupt:
            print("Dừng chương trình.")
        finally:
            client.close()
    except:
        print('loi ket noi')
