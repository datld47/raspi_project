import threading
import queue
import zmq
import struct
import sys
import time
import RPi.GPIO as GPIO
import spidev
import json
from threading import Thread, Lock
from collections import deque
import datetime
from datetime import timezone
from datetime import datetime as dt

#import my_sqlite
from my_model import AD7606_DETAIL,AD7606_FRE700
import connect_server
import random
#from fre700 import init_modbus_client,fre70_read_raw_data_continue,fre700_decode_data 
from plc import init_tcp_modbus_client,plc_decode_data,plc_read_data 
import serial.tools.list_ports

def error_handler(err):
    print(f'[ERROR SYSTEM]:{err}')
    while True:
        pass


#đường dẫn file config
PATH_MY_CONFIG='/home/dat/hoang_project/raspi_project/project_ad7606/my_config.json'
#biến chứa kết quả đọc từ file config
MY_CONFIG=None
try:
    with open(PATH_MY_CONFIG, "r", encoding="utf-8") as f:
        MY_CONFIG= json.load(f)
except json.JSONDecodeError:
        print(f"lỗi cú pháp JSON")
        sys.exit(1)

PI_ID=MY_CONFIG['pi']['pi_id']
AD7606_ID=MY_CONFIG['ad7606']['ad7606_id']
TIME_DB_PUSH=MY_CONFIG['app_config']['time_db_push']
TIME_READ_ADC=MY_CONFIG['app_config']['time_read_adc']
TIME_READ_MODBUS= MY_CONFIG['app_config']['time_modbus']
FRAME_PER_BLOCK = MY_CONFIG['frame']['FRAME_PER_BLOCK']
SERVER_BATCH_SIZE = MY_CONFIG['frame']['SERVER_BATCH_SIZE']
NUM_CHANNELS=MY_CONFIG['frame']['NUM_CHANNELS']
IP_PLC=MY_CONFIG['plc']['IP']
PORT_PLC=MY_CONFIG['plc']['PORT']
plc_alarm_delay= MY_CONFIG['plc']['ALARM_LEVEL_1']

url_heartbeat=''
url_upload=''

pin_miso=9
pin_sclk=11
pin_rst=17
pin_ca=27
pin_busy=22
pin_alarm_plc =12

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_ca, GPIO.OUT)
GPIO.setup(pin_rst, GPIO.OUT)
#GPIO.setup(pin_cs, GPIO.OUT)
GPIO.setup(pin_busy, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pin_alarm_plc, GPIO.OUT)

spi = spidev.SpiDev()
spi.open(0, 0)  # Bus=0, Device=0 (CE0)

spi.max_speed_hz = 1000000    # tuong duong 8 MHz
spi.mode = 0                    # CPOL=0, CPHA=0
spi.bits_per_word = 8
spi.lsbfirst = False

# --- 1. RESET CHIP AD7606 (BẮT BUỘC) ---
GPIO.output(pin_rst, 1)
time.sleep(0.01)  # Giữ HIGH một chút
GPIO.output(pin_rst, 0)
time.sleep(0.01)


#================cau hinh modbus====================#
data_modbus=[]
client_modbus=init_tcp_modbus_client(IP_PLC,PORT_PLC)
time_sleep_for_client=0
while True:
    try:
        client_modbus.connect()
        print('ket noi modbus thanh cong')
        break
    except:
       print('loi connect plc')
    # cho tang dan
    time_sleep_for_client+=5
    print(f'ket noi lai sau {time_sleep_for_client} s')
    if(time_sleep_for_client>60):
        time_sleep_for_client=60
    time.sleep(time_sleep_for_client)

#============================================================#

# --- 2. BIẾN TOÀN CỤC & HÀNG ĐỢI ---
rx_1 = queue.Queue(maxsize=1000)
server_queue = queue.Queue(maxsize=50)
error_queue = queue.Queue()
plc_queue = queue.Queue(maxsize=10)
fre700_lock=threading.Lock()


# Trạng thái của App 2 (Bắt đầu là False, chờ App 2 lên tiếng)
ai_is_online = False 

# ------------khai báo hàm------------------------
def ad7606_read():
    adc_voltage = [0] * 8
    GPIO.output(pin_ca, 0)
    GPIO.output(pin_ca, 1)
    GPIO.output(pin_ca, 0)

    start_time = time.perf_counter()
    timeout = 0.001  # Giới hạn thời gian chờ: 1ms = 0.001 giây
    
    while (GPIO.input(pin_busy)==0):
        if (time.perf_counter() - start_time) > timeout:
            return [0] * 8  # Quá 1ms, thoát và trả về mảng 0
    while(GPIO.input(pin_busy)==1):
       if (time.perf_counter() - start_time) > timeout:
            return [0] * 8  # Quá 1ms, thoát và trả về mảng 0
    
    rx_buf = spi.readbytes(16)

    for i in range(8):
        raw = (rx_buf[2*i] << 8) | rx_buf[2*i + 1]
        if raw & 0x8000:        # signed 16-bit
            raw -= 65536
        adc_voltage[i] = raw
    return adc_voltage

def get_now_timestamp():
    timestamp =  dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+'Z'
    return timestamp


# --- 4. LUỒNG 1: THU THẬP DỮ LIỆU ---

def thread_1_daq():
    global rx_1
    global TIME_READ_ADC
    global error_queue
    try:
        print("[L1] Đang thu thập dữ liệu 8 kênh (10ms)...")
        while True:
            start_tick = time.perf_counter()
            rresult=ad7606_read()
            rx_1.put(rresult)
            elapsed = time.perf_counter() - start_tick
            time.sleep(max(0, TIME_READ_ADC - elapsed))
    except Exception as e:
        error_queue.put(("DAQ_CORE (Luồng 1)", str(e)))

# --- 5. LUỒNG 2 & 3: QUẢN LÝ BUFFER & GHI SHM ---
def thread_2_3_manager():
    print("[L2-3] Quản lý bộ nhớ chia sẻ đang chạy...")
    global ai_is_online
    global rx_1
    global lock1
    global server_queue
    global error_queue
    global data_modbus
    frame_count = 0
    current_block = []
    buffer_write=[]
    try:
        context = zmq.Context()
        daq_socket = context.socket(zmq.PUSH)
        daq_socket.setsockopt(zmq.SNDHWM, 50) # Chống tràn RAM (chứa tối đa 50 gói)
        daq_socket.bind("ipc:///tmp/daq_data.ipc") # Tạo cổng IPC cho App 2 c
        while True:
            record = rx_1.get()
            current_block.extend(record)
            with fre700_lock:
                data_tmp=data_modbus
            current_block.extend(data_tmp)
            data_tmp_decode=plc_decode_data(data_tmp)
            buffer_write.append(AD7606_FRE700(0,AD7606_ID,record,get_now_timestamp(),data_tmp_decode))
            frame_count += 1
            if frame_count >= FRAME_PER_BLOCK:
                packed_data = struct.pack(f'{len(current_block)}h', *current_block)
                if ai_is_online:
                    daq_socket.send(packed_data)
                else:
                    print('cho ai_app ket noi')
                server_queue.put(buffer_write.copy())
                buffer_write.clear()
                current_block.clear()
                frame_count = 0
    except Exception as e:
        error_queue.put(("BUFFER_MGR (Luồng 2-3)", str(e)))
    finally:
        daq_socket.close()
        context.term()

# --- 6. LUỒNG 4: LẮNG NGHE ĐIỀU KHIỂN (ZMQ) ---
def thread_4_control_listener():
    global ai_is_online
    global context
    global lock1
    global error_queue
    global plc_alarm_delay
    global plc_queue
    try:
        context = zmq.Context()
        sub = context.socket(zmq.SUB)
        sub.connect("ipc:///tmp/ai_status.ipc")
        sub.setsockopt_string(zmq.SUBSCRIBE, "")
        print("[L4] Đang trực lệnh ZMQ...")
        while True:
            msg = sub.recv_json()
            result = msg.get('result')
            if result == "APP2_ONLINE":
                print(f"\n[+] TIN VUI: {msg.get('details')}")
                ai_is_online = True  
            elif result == "APP2_OFFLINE":
                print(f"\n[-] THÔNG BÁO: {msg.get('details')}")
                print("[-] App 1 chuyển sang chế độ CHỜ AI (Chỉ thu thập & Gửi Server).")
                ai_is_online = False 
                
            elif result == "ERROR_APP2":
                print(f"\n[!] AI CRASH: {msg.get('details')}")
                print("[!] Tạm ngưng gửi dữ liệu cho AI để tránh lỗi hệ thống.")
                ai_is_online = False

            elif result == 1:
                print("\n[!!!] CẢNH BÁO: PHÁT HIỆN SỰ CỐ! NGẮT THIẾT BỊ! [!!!]\n")
                print(msg)
                plc_queue.put("TRIGGER_ALARM")
            else:
                pass
            
    except Exception as e:
        error_queue.put(("ZMQ_CONTROL (Luồng 4)", str(e)))
    finally:
        sub.close()
        context.term()
        
# --- 7. LUỒNG 5: GỬI DỮ LIỆU LÊN SERVER ---
def thread_5_server_uploader():
    global error_queue
    global server_queue
    global SERVER_BATCH_SIZE
    try:
        print("[L5] Luồng Server đã chạy...")
        big_batch = []
        block_count = 0
        buffer_send=[]
        while True:
            block_data = server_queue.get()
            big_batch.append(block_data)
            block_count += 1
            if block_count >= SERVER_BATCH_SIZE:
                try:
                    data= connect_server.send_heartbeat(url_heartbeat)
                    if data:
                        block = data['data']['block']
                        print(f'block={block}')
                        base_block_id=block+1
                        for i, current_block_list in enumerate(big_batch):
                            actual_id = base_block_id + i
                            for obj in current_block_list:
                                buffer_send.append(obj.to_dict(block=actual_id))
                        data_copy_for_thread = list(buffer_send)
                        # --- BẮN THREAD CON ĐỂ GỬI BẤT ĐỒNG BỘ ---
                        upload_thread = threading.Thread(
                            target= connect_server.upload_data, 
                            args=(data_copy_for_thread, url_upload)
                        )
                        # Daemon = True để nếu chương trình chính tắt, thread này cũng chết theo
                        upload_thread.daemon = True 
                        upload_thread.start()
                    else:
                        print('rot mang , luu tam vao database -- xu ly sau')
                except:
                    pass
                finally:
                    big_batch.clear()
                    buffer_send.clear()
                    block_count = 0
    except Exception as e:
        error_queue.put(("SERVER_UPLOADER (Luồng 5)", str(e)))
    
def thread_6_plc_control():
    print("[L-PLC] Luồng điều khiển Alarm PLC đã sẵn sàng (Trễ 2s)...")
    flag_alarm=0
    alarm_until = 0
    global plc_alarm_delay
    while True:
        try:
            # Chờ lệnh (ví dụ: "TRIGGER_ALARM")
            cmd = plc_queue.get() 
            if cmd == "TRIGGER_ALARM":
                if flag_alarm==0:
                    flag_alarm=1
                    print('bật alarm')
                    GPIO.output(pin_alarm_plc,1)
                    alarm_until=time.time()+plc_alarm_delay
            
            if flag_alarm==1:
                if time.time() > alarm_until:
                    flag_alarm=0
                    print('tắt alarm')
                    
            plc_queue.task_done()
        except Exception as e:
            print(f"Lỗi luồng PLC: {e}")

def thread_7_modbus():
    global data_modbus
    global client_modbus
    data=[]
    try:
        print("[L7] thu thập modbus")
        while True:
            start_tick = time.perf_counter()
            data=plc_read_data(client_modbus)
            with fre700_lock:
                data_modbus=data
            elapsed = time.perf_counter() - start_tick
            time.sleep(max(0, TIME_READ_MODBUS - elapsed))
    except Exception as e:
        print(e)
        error_queue.put(("DAQ_CORE (Luồng 1)", str(e)))


#========================TESST ADC ===========================
if False:
    while True:
        print('bat dau test')
        adc_voltage = [0.0] * 8
        GPIO.output(pin_ca, 0)
        GPIO.output(pin_ca, 1)
        GPIO.output(pin_ca, 0)
        while (GPIO.input(pin_busy)==0):
            pass
        while(GPIO.input(pin_busy)==1):
            pass
        rx_buf = spi.readbytes(16)
        for i in range(8):
            raw = (rx_buf[2*i] << 8) | rx_buf[2*i + 1]
            if raw & 0x8000:        # signed 16-bit
                raw -= 65536
            adc_voltage[i] = (raw/32767.0 )*10
        print(adc_voltage)
        time.sleep(1)
#=================================================================


#========================TESST MODBUS ===========================
if False:
    while True:
        data=plc_read_data(client_modbus)
        print(data)
        print(plc_decode_data(data))
        time.sleep(5)
        
#=================================================================



# =========================Chương trình bắt đầu chạy =============================-
if __name__ == "__main__":
  
    url_heartbeat=connect_server.create_url_heartbeat(MY_CONFIG['server'])
    url_upload=connect_server.create_url_upload(MY_CONFIG['server'])
    
    print(f'=====Thông tin cấu hình=====\n-PI_ID:{PI_ID}\n-AD7606_ID:{AD7606_ID}\n-TIME_READ_ADC:{TIME_READ_ADC}\n-TIME_READ_MODBUS:{TIME_READ_MODBUS}\n-FRAME_PER_BLOCK:{FRAME_PER_BLOCK}\n-SERVER_BATCH_SIZE:{SERVER_BATCH_SIZE}\nNUM_CHANNELS={NUM_CHANNELS}\n-url_heartbeat:{url_heartbeat}\n-url_upload:{url_upload}\nTime PLC delay:{plc_alarm_delay}\n=========================')
    
    try:
        data_modbus=plc_read_data(client_modbus)
        if data_modbus==None:
            error_handler('loi doc modbus')
        print(f'[modbus]:{data_modbus}')
        print(f'[modbus decode]:{plc_decode_data(data_modbus)}')
    except:
          error_handler('loi doc modbus')
        
    workers = [
        threading.Thread(target=thread_1_daq, daemon=True),
        threading.Thread(target=thread_2_3_manager, daemon=True),
        threading.Thread(target=thread_4_control_listener, daemon=True),
        threading.Thread(target=thread_5_server_uploader, daemon=True),
        threading.Thread(target=thread_6_plc_control, daemon=True),
        threading.Thread(target=thread_7_modbus, daemon=True),
    ]

    for t in workers:
        t.start()
        
    print("\n--- APP 1: HỆ THỐNG ĐÃ KÍCH HOẠT ---")
    print("Đang chờ App 2 (AI Worker) kết nối...\n")

    try:
        failed_thread, error_msg = error_queue.get()
        print("\n" + "="*50)
        print(f"!!! CRASH HỆ THỐNG PHÁT HIỆN TỪ APP 1 !!!")
        print(f"- Nguồn lỗi: {failed_thread}")
        print(f"- Chi tiết: {error_msg}")
        print("="*50)
    except KeyboardInterrupt:
        print("\n[App 1] Tắt thủ công (Ctrl+C).")
    finally:
        print("[Hệ thống] Dọn dẹp RAM và dừng hoàn toàn...")
        client_modbus.close()
        sys.exit(1)