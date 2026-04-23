
import time
import RPi.GPIO as GPIO
import spidev
import sys
import json
import queue
import threading
from threading import Thread, Lock
from collections import deque
import datetime
from datetime import timezone
from datetime import datetime as dt
sys.path.append('./iot_project_app/project_ad7606')
import my_sqlite
from my_model import AD7606_INFO,AD7606_CHANNEL,AD7606_DETAIL,SENSOR_INFO
import connect_server

pin_miso=9
pin_sclk=11
pin_rst=17
pin_ca=27
pin_busy=22
pin_cs=23

GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_ca, GPIO.OUT)
GPIO.setup(pin_rst, GPIO.OUT)
GPIO.setup(pin_cs, GPIO.OUT)
GPIO.setup(pin_busy, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

spi = spidev.SpiDev()
spi.open(0, 0)  # Bus=0, Device=0 (CE0)

spi.max_speed_hz = 8_000_000    # tuong duong 8 MHz
spi.mode = 0                    # CPOL=0, CPHA=0
spi.bits_per_word = 8
spi.lsbfirst = False   

# ==== H�M �?C AD7606 (Gi?ng ESP32 1:1) ====
def ad7606_read():
    adc_voltage = [0.0] * 8

    # 1. K�ch CONVST: CA = 1 -> 0
    GPIO.output(pin_ca, 1)
    GPIO.output(pin_ca, 0)

    # 2. �?i BUSY xu?ng
    while GPIO.input(pin_busy) == 1:
        pass

    # 3. CS = 0
    GPIO.output(pin_cs, 0)

    # 4. �?c 16 byte y nhu rx_buf ESP32
    rx_buf = spi.readbytes(16)

    # 5. CS = 1
    GPIO.output(pin_cs, 1)

    # 6. Convert d? li?u (gi?ng h?t ESP32)
    for i in range(8):
        raw = (rx_buf[2*i] << 8) | rx_buf[2*i + 1]
        if raw & 0x8000:        # signed 16-bit
            raw -= 65536

        adc_voltage[i] = raw / 32767.0 * 10.0

    return adc_voltage


#đường dẫn file config
PATH_MY_CONFIG='/home/dat/Project/iot_project_app/project_ad7606/my_config.json'

#biến chứa kết quả đọc từ file config
MY_CONFIG=None
# khai báo queue phục vụ giao tiếp đa luồng
rx_queue = queue.Queue()
tx_queue=queue.Queue()
ui_queue=queue.Queue()
url_heartbeat=''
url_upload=''
AD7606_ID=''


# biến lưu toàn bộ giao điện ứng dụng : dùng trong trưởng hợp cập nhập ui
window=None
stop_event = None
COMMANDS = {
    "start": b"\x02\x00\x01\x01\x01\x03"}

START_BYTE=0x02
END_BYTE=0x03
FRAME_OK = 0
FRAME_ERROR = 1
FRAME_WAIT = 2


TIME_DB_PUSH=5 #thoi gian day du lieu len server
TIME_READ_ADC=0.005  #thoi gian doc adc

BUFFER_MAX = 4000
buffer_write = deque(maxlen=BUFFER_MAX)
buffer_send = deque(maxlen=BUFFER_MAX)
buffer_lock = Lock()

def calculate_checksum(data: bytes) -> int:
    cs = 0
    for b in data:
        cs ^= b
    return cs & 0xFF

def check_frame(frame: bytes):

    if frame[0] != START_BYTE:
        return FRAME_ERROR, None

    if len(frame) < 6:
        return FRAME_WAIT, None

    if frame[-1] != END_BYTE:
        return FRAME_WAIT, None

    data_len = (frame[1] << 8) | frame[2]
    
    if len(frame) != (3 + data_len + 2):
        return FRAME_ERROR, None

    data = frame[3:3+data_len]
    cs_recv = frame[3+data_len]
    cs_calc = calculate_checksum(data)
    if cs_calc != cs_recv:
        return FRAME_ERROR, None

    return FRAME_OK, data

def swap_buffers():
    global buffer_write, buffer_send
    buffer_write, buffer_send = buffer_send, buffer_write

# chuyển đổi ánh sang dạng ImageTk để load lên giao diện
# def to_image_tk(path_img,size=(50,50)):
#     try:
#         img_ = PILImage.open(path_img)
#         img_resized = img_.resize(size, PILImage.LANCZOS)
#         tk_img = ImageTk.PhotoImage(img_resized)
#         return tk_img
#     except:
#         return None

# hàm lấy thời gian hiện tại và chuyển sang định dạng chuổi phù hợp lưu vào database : thoi gian UCT
def get_now_timestamp():
    timestamp =  dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+'Z'
    return timestamp

def decode_ad7606_data(data):
    adc_voltage = []
    for i in range(8):
        # ghép 2 byte thành 16-bit signed
        raw = int.from_bytes(data[2*i:2*i+2], byteorder='big', signed=True)
        # chuyển sang voltage ±10V
        voltage = raw / 32768.0 * 10.0
        adc_voltage.append(voltage)
    return adc_voltage

#thread lắng nghe nhận dữ liệu
# def rx_loop(ser):
#     global rx_queue
#     buffer = bytearray()
#     while True:
#         try:
#             data = ser.read(1)
#             buffer.extend(data)
#             while ser.in_waiting:
#                 buffer.extend(ser.read(ser.in_waiting))
#             rx_queue.put(buffer.copy())
#             buffer.clear()
#         except Exception as e:
#             print("Uart error:", e)
#             time.sleep(0.1)

#thread lắng nghe để xử lý dữ liệu nhận
def process_data_loop():
    global rx_queue
    global tx_queue
    global ui_queue
    global AD7606_ID
    while True:
        try:
            result = rx_queue.get()
            if result:
                with buffer_lock:
                    buffer_write.append(AD7606_DETAIL(0,AD7606_ID,result,get_now_timestamp()))
        except Exception as e:
            print("Processing error:", e)
# gui du lien len server neu co mang/ neu rot mang luu tam thoi vao sqlite
def db_push_loop():
    global buffer_write, buffer_send
    global url_heartbeat
    global url_upload
    global TIME_DB_PUSH
    while True:
        print(f'cho timer: {TIME_DB_PUSH}s ...')
        time.sleep(TIME_DB_PUSH)
        with buffer_lock:
            swap_buffers()
        if buffer_send:
            # kiem tra co mang va lay block moi nhat
            data= connect_server.send_heartbeat(url_heartbeat)
            if data:
                block = data['data']['block']
                print(block)
                # gui du lieu len server voi block tiep theo
                block=block+1
                list_ad7606 = list(buffer_send)
                result=[]
                for l in list_ad7606:
                    result.append(l.to_dict(block=block))
                # gui len server
                connect_server.upload_data(result,url_upload)
            else:
                # rot mang
                print('rot mang , luu tam vao database -- xu ly sau')
                #my_sqlite.insert_ad7606_details(list(buffer_send))
                #print('write db ok')
                #print(list(buffer_send)[0])
            buffer_send.clear()

#thread lắng nghe để phát dữ liẹu            
# def tx_loop(ser):
#     global tx_queue
#     while True:
#         try:
#             data = tx_queue.get()
#             ser.write(data)          
#         except Exception as e:
#             print("Processing error:", e)

def read_adc_loop():
    global tx_queue
    global stop_event
    global COMMANDS
    global MY_CONFIG
    while True:
        #tx_queue.put(COMMANDS['start'])
        result=ad7606_read()
        rx_queue.put(result)
        time.sleep(TIME_READ_ADC)
    
# def ui_event_loop():s
#     global window
#     global ui_queue
#     global charts
#     global current_status
#     global config_info
#     global current_weather
#     #print('ui event loop ...')
    
#     while not ui_queue.empty():
#         data = ui_queue.get()
#         type=data['type']
#     window.after(100, ui_event_loop)  # quét nhanh mỗi 100ms     

def main():
    
    global rx_queue
    global tx_queue
    #global is_login
    #global window
    global stop_event
    global MY_CONFIG
    global url_heartbeat
    global url_upload
    global AD7606_ID
    global TIME_DB_PUSH
    global TIME_READ_ADC
    # load cấu file cấu hình
    try:
        with open(PATH_MY_CONFIG, "r", encoding="utf-8") as f:
            MY_CONFIG= json.load(f)
    except json.JSONDecodeError:
        print(f"lỗi cú pháp JSON")
        sys.exit(1)

    print(MY_CONFIG)
    url_heartbeat=connect_server.create_url_heartbeat(MY_CONFIG['server'])
    url_upload=connect_server.create_url_upload(MY_CONFIG['server'])
    AD7606_ID=MY_CONFIG['ad7606']['ad7606_id']
    TIME_DB_PUSH=MY_CONFIG['app_config']['time_db_push']
    TIME_READ_ADC=MY_CONFIG['app_config']['time_read_adc']
    print(AD7606_ID)
    print(url_heartbeat)
    print(url_upload)
  
    # # lấy thông tin uart
    # port=MY_CONFIG['serial']['port']
    # baudrate=MY_CONFIG['serial']['baudrate']
    
    # print(f"Khởi tạo uart ok:{port},{baudrate}")
    
    #--------------khởi tạo uart--------------------
    # try:
    #     ser = serial.Serial(port=port,
    #                         baudrate=baudrate,
    #                         parity=serial.PARITY_NONE,
    #                         bytesize=serial.EIGHTBITS,
    #                         stopbits=serial.STOPBITS_ONE,
    #                         timeout=None)
    # except Exception as err:
    #     print(err)
    #     sys.exit(1)

    # khởi tọa rx thread
    # rx_thread=threading.Thread(
    #     target=rx_loop,
    #     args=(ser,),
    #     daemon=True)
    
    # khởi tạo tx_thread

    # tx_thread=threading.Thread(
    # target=tx_loop,
    # args=(ser,),
    # daemon=True)
    
    # khởi tạo process_data thread
    proc_thread = threading.Thread(
        target=process_data_loop, 
        daemon=True)
    
    db_push_thread = threading.Thread(
        target=db_push_loop, 
        daemon=True)
    
    read_adc_thread=threading.Thread(
        target=read_adc_loop, 
        daemon=True)
    
    
    # khởi tạo biến sự kiện báo hiệu ứng dụng đóng
    stop_event=threading.Event()
        
    ##-------------tkiner---------------###
    
    # 1. Khởi tạo đối tượng giao diện
    # window = Tk()
    # window.title('app')
    # window.minsize(640,480)

    # một event_loop dựa vào after() để cập nhập giao diện
    #ui_event_loop()  
    # khởi chạy các thread nền
    
    # rx_thread.start()
    proc_thread.start()
    # tx_thread.start()
    db_push_thread.start()
    read_adc_thread.start()
    
    #window.mainloop()
    while True:
        time.sleep(1)

if __name__=='__main__':
    main()
















