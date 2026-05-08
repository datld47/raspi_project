# khoi dong dich vu bluetooth


#pip install bleak
#sudo systemctl restart hciuart
#sudo systemctl restart bluetooth



import asyncio
import threading
import time
import signal
import json
from queue import Queue, Empty
from datetime import datetime as dt

from bleak import BleakScanner, BleakClient
import subprocess



#===============  kiem tra bluetooth

def check_bluetooth_status():
    """Kiểm tra xem Bluetooth có đang bật hay không."""
    try:
        # Chạy lệnh 'bluetoothctl show' và lấy kết quả trả về
        result = subprocess.run(['bluetoothctl', 'show'], capture_output=True, text=True)
        if "Powered: yes" in result.stdout:
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra trạng thái Bluetooth: {e}")
        return False

def turn_on_bluetooth():
    """Bật Bluetooth bằng lệnh hệ thống."""
    try:
        print("Đang bật Bluetooth...")
        # Lệnh 1: Đảm bảo Bluetooth không bị khóa mềm bởi hệ điều hành (yêu cầu quyền sudo nếu cần)
        subprocess.run(['sudo', 'rfkill', 'unblock', 'bluetooth'], check=True)
        # Lệnh 2: Bật nguồn adapter Bluetooth
        subprocess.run(['bluetoothctl', 'power', 'on'], check=True, capture_output=True)
        print("✅ Đã bật Bluetooth thành công!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi: Không thể bật Bluetooth thông qua subprocess: {e}")
        return False

#=================

# =========================================================
# BLE CONFIG
# =========================================================
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHAR_UUID    = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

ESP_1="BLE_ESP32_1"
ESP_2="BLE_ESP32_2"
ESP_3="BLE_ESP32_3"
ESP_4="BLE_ESP32_4"
ESP_LIST=[ESP_1,ESP_2,ESP_3,ESP_4]
connected_esps = set()
# stop app
stop_event = threading.Event()

# =========================================================
# BLE NOTIFY CALLBACK
# =========================================================

def handle_notification(sender: int, data: bytearray):

    try:
        text = data.decode("utf-8")
        payload = json.loads(text)
        print(payload)
        # do something next
    except Exception as e:
        print("[BLE NOTIFY ERROR]", e)

# =========================================================
# BLE SCAN
# =========================================================


# =========================================================
# BLE MAIN
# =========================================================


async def connect_esp(device):
    """Hàm quản lý kết nối độc lập cho từng thiết bị"""
    name = device.name
    address = device.address
    connected_esps.add(name)
    client = BleakClient(device)
    
    try:
        await client.connect()
        print(f"[CONNECT ESP] {name} ({address}) connected!")
        await client.start_notify(CHAR_UUID, handle_notification)
        while not stop_event.is_set() and client.is_connected:
            await asyncio.sleep(1)
    
    except Exception as err:
        print(f'[CONNECT ESP] {name} except: {err}')
    
    if client.is_connected:
        await client.stop_notify(CHAR_UUID)
        await client.disconnect()
        
    if name in connected_esps:
        print(f"[CONNECT ESP] {name} remove")
        connected_esps.remove(name)
    print(f"[CONNECT ESP] {name} exit")

async def ble_main():
    is_on = check_bluetooth_status()
    if not is_on:
        print("Bluetooth hiện đang tắt.")
        success = turn_on_bluetooth()
        if not success:
            print("Dừng chương trình vì phần cứng Bluetooth không sẵn sàng.")
            return
        
    active_tasks = set()
    while not stop_event.is_set():
        if len(connected_esps) < len(ESP_LIST):
            print(f"[BLE] Đang quét... (Đã kết nối: {list(connected_esps)})")
            devices = await BleakScanner.discover(timeout=5)
            for d in devices:
                if d.name in ESP_LIST and d.name not in connected_esps:
                    print(f"[SCAN] Tìm thấy thiết bị mới: {d.address} | {d.name}")
                    task = asyncio.create_task(connect_esp(d))
                    active_tasks.add(task)
                    task.add_done_callback(active_tasks.discard)
        await asyncio.sleep(2)
    if active_tasks:
        await asyncio.gather(*active_tasks, return_exceptions=True)
    print('exit ble_main')
    
# =========================================================
# BLE THREAD
# =========================================================


def ble_thread():
    print("[BLE THREAD] started")
    asyncio.run(ble_main())
    print('exit ble_thread')
    
# =========================================================
# SIGNAL
# =========================================================

def signal_handler(sig, frame):
    print("\n[CTRL+C]")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    ble = threading.Thread(
        target=ble_thread,
        daemon=True
    )
    ble.start()
    
    while not stop_event.is_set():
        time.sleep(5)
    
    ble.join()
    print('exit main')
    
    
    