import requests
import time

def create_url_heartbeat(server_config):
    ip=server_config['ip']
    port=server_config['port']
    url=server_config['url_heartbeat']
    return f"http://{ip}:{port}/{url}"

def create_url_upload(server_config):
    ip=server_config['ip']
    port=server_config['port']
    url=server_config['url_upload']
    return f"http://{ip}:{port}/{url}"


def send_heartbeat(url):
    """Hàm để đọc block mới nhất từ server"""
    try:
        response = requests.get(url, timeout=10) # Thêm timeout là thực hành tố
        if response.status_code == 200:
            print("Kết nối thành công (200)")
            data = response.json()
            return data
        elif response.status_code == 404:
            print(f"Lỗi 404: Không tìm thấy tài nguyên tại {url}")
            return None   
        else:
            print(f"Server trả về mã lỗi: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
            print("Lỗi: Kết nối bị quá thời gian (Timeout)")
    except requests.exceptions.RequestException as e:
            print(f"Đã xảy ra lỗi kết nối: {e}")
    return None


def upload_data(data, url):
    try:
        start_time = time.time()
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            duration = time.time() - start_time
            print(f"✅ Đã gửi {len(data)} bản ghi. Server phản hồi trong {duration:.2f}s")
        else:
            print(f"❌ upload loi ! Mã lỗi: {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")