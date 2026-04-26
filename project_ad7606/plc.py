import time
import datetime
from datetime import timezone
from datetime import datetime as dt
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
import time
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException


factor=[0.01,0.01,0.1,0.0,0.01,0.0,0.1]
unit=['Hz','A','V','','','','%']
choose=[0,1,6]
factor_choose=[ factor[i] for i in choose]

def get_now_timestamp():
    timestamp =  dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+'Z'
    return timestamp


def init_tcp_modbus_client(ip_plc='192.168.0.1',port=502):
    client = ModbusTcpClient(host=ip_plc, port=port)
    return client 

def plc_read_data(client,modbus_address=40001,count=7,choose=choose):
    try:
        # Kh�ng c?n g?i client.connect() li�n t?c n?u d� connect ? ngo�i
        if len(factor)!=count:
            return None
        pymodbus_address = modbus_address - 40001
        result = client.read_holding_registers(address=pymodbus_address, count=count, device_id=1)
        if result.isError():
            print(f"L?i Modbus: {result}")
            return None
        return [result.registers[i] for i in choose]
    except ModbusIOException:
        print("L?i I/O: M?t ph?n h?i t? bi?n t?n.")
    except Exception as e:
        print(f"L?i kh�ng x�c d?nh: {e}")
    return None


def plc_decode_data(raw_data_16,factor=factor_choose):
    if len(raw_data_16)==len(factor):
        return [val * f for val, f in zip(raw_data_16, factor)]
    print('loi factor')
    return None

if __name__ == "__main__":
    client=init_tcp_modbus_client()        
    try:
        client.connect()
        try:
            while True:
                start_tick = time.perf_counter()
                print(plc_read_data(client,40001,7))  
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("D?ng chuong tr�nh.")
        finally:
            client.close()
    except:
        print('loi ket noi')

