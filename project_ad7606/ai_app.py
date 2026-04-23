import time
import zmq
import struct
import os
import sys
import signal
import numpy as np
from datetime import datetime as dt
from model_app import get_ort_session,create_channel_dataframe,ONNXTimeSeriesModel
import pandas as pd
import joblib
from datetime import timezone
from datetime import datetime as dt


# --- 1. CẤU HÌNH ---
NUM_CHANNELS = 11
FRAME_PER_BLOCK = 512
BYTES_PER_BLOCK = FRAME_PER_BLOCK * NUM_CHANNELS * 2
TOTAL_ELEMENTS = FRAME_PER_BLOCK * NUM_CHANNELS

context = None
pub_socket = None
pull_socket=None
ort_session=None
path_onnx='/home/dat/hoang_project/raspi_project/project_ad7606/2_cnn_lstm_model.onnx'
path_combined_scalers = '/home/dat/hoang_project/raspi_project/project_ad7606/combined_scalers.pkl'
scaler_vibration=None
scaler_current=None

def get_now_timestamp():
    timestamp =  dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]+'Z'
    return timestamp

# --- 2. CƠ CHẾ XỬ LÝ NGẮT & BÁO TỬ ---
def handle_sigterm(signum, frame):
    global pub_socket
    global context
    print("\n[App 2] Nhận lệnh tắt. Đang chào tạm biệt Master...")
    try:
        pub_socket.send_json({
            "result": "APP2_OFFLINE",
            "details": "AI Worker chủ động dừng (Stop/Bảo trì)."
        })
    except Exception as err:
        print(err)
    finally:
        pub_socket.close()
        pull_socket.close()
        context.term()
        print("[App 2] Đã tắt an toàn.")
        sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

# --- 3. KHỞI TẠO TIẾN TRÌNH TRÊN RASPBERRY PI 4 ---
def setup_environment():
    global ort_session
    global context, pub_socket
    global scaler_current
    global scaler_vibration
    
    # 1. Khóa cứng tiến trình vào Core 3 (Nhân số 4 của Pi)
    try:
        os.sched_setaffinity(0, {3})
        print(f"[App 2] [OK] Đã khóa tiến trình vào Core 3 (PID: {os.getpid()})")
    except Exception as e:
        print(f"\n[FATAL] KHÔNG THỂ KHÓA CORE 3!")
        print(f"[Chi tiết lỗi]: {e}")
        print("[!] Đảm bảo bạn có đủ quyền (thử sudo) và CPU chưa bị chiếm dụng độc quyền.")
        sys.exit(1)
  
    try:
        ort_session= get_ort_session(path_onnx)
        # Đọc file lên. Lúc này 'loaded_data' chính là cái Dictionary bạn đã lưu
        loaded_data = joblib.load(path_combined_scalers)
        # Phân giải (lấy) từng scaler ra để sử dụng dựa vào key (tên) đã đặt
        scaler_vibration = loaded_data['vibration']
        scaler_current = loaded_data['current']
    except Exception as e:
        print(f"\n[FATAL] KHỞI TẠO ORT_SESSION LOI!")
        print(f"[Chi tiết lỗi]: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_environment()
    context = zmq.Context()
    # =================================================================
    # LÀN 2: TRẠM PHÁT TÍN HIỆU ĐIỀU KHIỂN (PUB)
    # Lưu ý: Vì App 1 dùng 'connect' cho Làn 2, nên App 2 phải dùng 'bind'
    # =================================================================
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind("ipc:///tmp/ai_status.ipc")
    
    pull_socket = context.socket(zmq.PULL)
    pull_socket.connect("ipc:///tmp/daq_data.ipc")

    print("[App 2] AI Worker đang khởi động...")
    time.sleep(1) # Ngủ 1 giây để đảm bảo ZMQ đã kết nối vật lý xong xuôi
    
    pub_socket.send_json({
        "result": "APP2_ONLINE",
        "details": "AI Worker đã sẵn sàng nhận dữ liệu!"
    })
    print("[App 2] Đã báo ONLINE cho App 1.\n")
    
    while True:
        try:
            # CHỜ APP 1
            
            raw_data = pull_socket.recv()
            start_time = time.perf_counter()            
            data_list = struct.unpack(f'{TOTAL_ELEMENTS}h', raw_data)
           
            # CHẠY MÔ HÌNH AI (Core 3)
            
            print(f'[CORE 3] [{get_now_timestamp()}]| Chạy mô hình')
            ai_input = np.array(data_list).reshape(FRAME_PER_BLOCK, NUM_CHANNELS)
            
            
            ##===============Chon so kenh va phan giai phu hop voi mo hinh===========================
            df=create_channel_dataframe(ai_input,['CH1','CH3'])
            df['CH1'] = (df['CH1'] / 32767.0) * 25.0
            df['CH3'] = (df['CH3'] / 32767.0) *10*100*1000
            ##=========================================================================================
            
            
            onnx_timeseries_model = ONNXTimeSeriesModel(
                ort_session=ort_session,
                data_input=df,
                scaler_vibration=scaler_vibration,
                scaler_current=scaler_current
            )
            pred, logits=onnx_timeseries_model.predict()
            ai_result_clean = int(pred[0])

            # TRẢ KẾT QUẢ VỀ APP 1
            
            pub_socket.send_json({
                "result": ai_result_clean,
            })
            
            # IN log
            
            process_time_ms= round((time.perf_counter() - start_time) * 1000, 2)
            print(f"[CORE 3] [{get_now_timestamp()}] | KQ: {ai_result_clean} | time: {process_time_ms}")
                
        except Exception as e:
            error_msg = f"Lỗi quá trình xử lý AI: {str(e)}"
            print(f"\n[FATAL] {error_msg}")
            # Trăng trối với App 1 rồi tự thoát
            pub_socket.send_json({
                "result": "ERROR_APP2",
                "details": error_msg
            })
            time.sleep(0.1) 
            pub_socket.close()
            pull_socket.close()
            context.term()
            sys.exit(1)
    