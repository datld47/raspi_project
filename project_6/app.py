from tkinter import *
from tkinter import messagebox,scrolledtext
from tkinter import filedialog
from tkinter import ttk
import tkinter as tk
import os
import sys
import requests
from PIL import Image as PILImage, ImageTk
import matplotlib.pyplot  as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime
from datetime import datetime as dt
import time
import serial
import json
import queue
import threading
from threading import Thread, Lock
from collections import deque

sys.path.append('./project/project6')
import my_sqlite
from my_model import AD7606_INFO,AD7606_CHANNEL,AD7606_DETAIL,SENSOR_INFO

#đường dẫn file config
PATH_MY_CONFIG='./project/project6/my_config.json'
#biến chứa kết quả đọc từ file config
MY_CONFIG=None
# khai báo queue phục vụ giao tiếp đa luồng
rx_queue = queue.Queue()
tx_queue=queue.Queue()
ui_queue=queue.Queue()
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
TIME_DB_PUSH=5
TIME_READ_ADC=0.005

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

# hàm lấy thời gian hiện tại và chuyển sang định dạng chuổi phù hợp lưu vào database
def get_now_timestamp():
    timestamp =  dt.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
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
def rx_loop(ser):
    global rx_queue
    buffer = bytearray()
    while True:
        try:
            data = ser.read(1)
            buffer.extend(data)
            while ser.in_waiting:
                buffer.extend(ser.read(ser.in_waiting))
            rx_queue.put(buffer.copy())
            buffer.clear()
        except Exception as e:
            print("Uart error:", e)
            time.sleep(0.1)

#thread lắng nghe để xử lý dữ liệu nhận
def process_data_loop():
    global rx_queue
    global tx_queue
    global ui_queue
    while True:
        try:
            data = rx_queue.get()
            result,rx_data= check_frame(data)
            if result==FRAME_OK:
                with buffer_lock:
                    rx_decode=decode_ad7606_data(rx_data)
                    buffer_write.append(AD7606_DETAIL(0,'AD7606_1',rx_decode,get_now_timestamp()))
        except Exception as e:
            print("Processing error:", e)

def db_push_loop():
    global buffer_write, buffer_send
    while True:
        time.sleep(TIME_DB_PUSH)
        with buffer_lock:
            swap_buffers()
        if buffer_send:
            # gửi xuống database theo batch
            # for data in list(buffer_send):
            #     #send_to_db(list(buffer_send))  # gửi batch
            #     print(data)
            my_sqlite.insert_ad7606_details(list(buffer_send))
            print('write db ok')
            buffer_send.clear()

#thread lắng nghe để phát dữ liẹu            
def tx_loop(ser):
    global tx_queue
    while True:
        try:
            data = tx_queue.get()
            ser.write(data)          
        except Exception as e:
            print("Processing error:", e)

def read_adc_loop():
    global tx_queue
    global stop_event
    global COMMANDS
    global MY_CONFIG
    while True:
        tx_queue.put(COMMANDS['start'])
        time.sleep(TIME_READ_ADC)
    
# def ui_event_loop():
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
    
    # load cấu file cấu hình
    try:
        with open(PATH_MY_CONFIG, "r", encoding="utf-8") as f:
            MY_CONFIG= json.load(f)
    except FileNotFoundError:
        default_config = {
            "serial": {"port": "COM10", "baudrate": 9600},
            "account": [
                {"username":"guest",
                 "password":"1",
                 "role":"user"}
            ]
        }
        with open(PATH_MY_CONFIG, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        MY_CONFIG=default_config
    except json.JSONDecodeError:
        print(f"lỗi cú pháp JSON")
        sys.exit(1)
 
    # lấy thông tin uart
    port=MY_CONFIG['serial']['port']
    baudrate=MY_CONFIG['serial']['baudrate']
    
    print(f"Khởi tạo uart ok:{port},{baudrate}")
    
    #--------------khởi tạo uart--------------------
    try:
        ser = serial.Serial(port=port,
                            baudrate=baudrate,
                            parity=serial.PARITY_NONE,
                            bytesize=serial.EIGHTBITS,
                            stopbits=serial.STOPBITS_ONE,
                            timeout=None)
    except Exception as err:
        print(err)
        sys.exit(1)

    # khởi tọa rx thread
    rx_thread=threading.Thread(
        target=rx_loop,
        args=(ser,),
        daemon=True)
    
    # khởi tạo tx_thread
    tx_thread=threading.Thread(
    target=tx_loop,
    args=(ser,),
    daemon=True)
    
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
    
    rx_thread.start()
    proc_thread.start()
    tx_thread.start()
    db_push_thread.start()
    read_adc_thread.start()
    
    #window.mainloop()
    while True:
        time.sleep(1)

if __name__=='__main__':
    main()

