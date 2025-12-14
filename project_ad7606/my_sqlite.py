import sqlite3
import sys
from typing import List
from my_model import AD7606_INFO,AD7606_CHANNEL,AD7606_DETAIL,SENSOR_INFO

path='/home/dat/Project/iot_project_app/project_ad7606/iot2.db'
# try:
#     conn = sqlite3.connect(path)  # mở/ tạo file DB
#     cursor = conn.cursor()
# except Exception as err:
#     print(f"Lỗi khi kết nối SQLite: {err}")
#     sys.exit(1)

# def close_connect():
#     conn.close()

##sensor

def get_connection():
    try:
        conn = sqlite3.connect(path)  # mở/ tạo file DB
        return conn
    except Exception as err:
        print(err)



def insert_ad7606_detail(data:AD7606_DETAIL):
    result=False
    try:
        conn=get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO AD7606_DETAIL (AD7606_id, CH1, CH2,CH3,CH4,,CH5,CH6,CH7,CH8,timestamp)
        VALUES (?, ?, ?)
        """
        cursor.execute(query, (data.AD7606_id, 
                               data.CH1, 
                               data.CH2,
                               data.CH3,
                               data.CH4,
                               data.CH5, 
                               data.CH6,
                               data.CH7,
                               data.CH9,
                               data.timestamp))
        conn.commit()
        result=True
    except Exception as err:
        print(err)
    finally:
        conn.close()
        return result




def insert_ad7606_details(data_list: List[AD7606_DETAIL]):
    """Insert nhiều record AD7606_DETAIL vào SQLite cùng lúc"""
    result = False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO AD7606_DETAIL 
        (AD7606_id, CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        print(data_list)
        
        # chuẩn bị dữ liệu dạng list of tuple
        values = [
            (d.AD7606_id, d.CH1, d.CH2, d.CH3, d.CH4, d.CH5, d.CH6, d.CH7, d.CH8, d.timestamp)
            for d in data_list
        ]
        
        cursor.executemany(query, values)
        conn.commit()
        result = True
    except Exception as err:
        print(err)
    finally:
        conn.close()
        return result

# def get_sensors_from_num(num):
#     result = []
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#     SELECT * FROM sensor_data
#     ORDER BY timestamp DESC LIMIT ?
#     """
#         params = (num,)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()
#         for row in rows:
#             id = row[0]
#             temperature = row[1]
#             humidity = row[2]
#             timestamp = row[3]
#             sensor = SensorData(id, temperature, humidity, timestamp)
#             result.append(sensor)
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result

# def get_lastest_sensor():
#     result=get_sensors_from_num(1)
#     if result:
#         result=result[0]
#     return result    
 
# def get_sensors_from_date(date:str):
#     '''
#     date: 2025-10-04
#     '''

#     result = []    
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#         SELECT * FROM sensor_data
#         WHERE timestamp BETWEEN ? AND ?
#         """
#         params = (date + " 00:00:00", date + " 23:59:59")
#         cursor.execute(query, params)
#         rows = cursor.fetchall()
#         for row in rows:
#             id = row[0]
#             temperature = row[1]
#             humidity = row[2]
#             timestamp = row[3]
#             sensor = SensorData(id, temperature, humidity, timestamp)
#             result.append(sensor)
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result

# def insert_sensor(data:SensorData):
#     result=False
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#         INSERT INTO sensor_data (temperature, humidity, timestamp)
#         VALUES (?, ?, ?)
#         """
#         cursor.execute(query, (data.temperature, data.humidity, data.timestamp))
#         conn.commit()
#         result=True
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result

# ##setting

# def get_setting_data():
#     result=None
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#     SELECT * FROM setting_data WHERE id = 1 
#     """
#         cursor.execute(query)
#         row = cursor.fetchone()
#         id = row[0]
#         temperature_threshold = row[1]
#         humidity_threshold = row[2]
#         timestamp = row[3]
#         result = SettingData(id, temperature_threshold, humidity_threshold, timestamp)
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result
    
# def update_setting(data:SettingData):
#     result=False
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
# UPDATE setting_data SET temperature_threshold=?,humidity_threshold=?,timestamp=? WHERE id=1
#     """
#         params = (data.temperature_threshold, data.humidity_threshold,data.timestamp)
#         cursor.execute(query,params)
#         conn.commit()
#         result = True
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result

# ##fan

# def get_fans_from_num(num):
#     result = []
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#     SELECT * FROM fan_data
#     ORDER BY timestamp DESC LIMIT ?
#     """
#         params = (num,)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()
#         for row in rows:
#             id = row[0]
#             value = row[1]
#             timestamp = row[2]
#             fan = FanData(id, value,timestamp)
#             result.append(fan)
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result
    
# def get_lastest_fan():
#     result=get_fans_from_num(1)
#     if result:
#         result=result[0]
#     return result

# def insert_fan(data:FanData):
#     result=False
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#         INSERT INTO fan_data (value,timestamp)
#         VALUES (?, ?)
#         """
#         cursor.execute(query, (data.value,data.timestamp))
#         conn.commit()
#         result=True
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result
    
# ##pumb
# def get_pumbs_from_num(num):
#     result = []
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#     SELECT * FROM pump_data
#     ORDER BY timestamp DESC LIMIT ?
#     """
#         params = (num,)
#         cursor.execute(query, params)
#         rows = cursor.fetchall()
#         for row in rows:
#             id = row[0]
#             value = row[1]
#             timestamp = row[2]
#             fan = PumpData(id, value,timestamp)
#             result.append(fan)
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result
    
# def get_lastest_pump():
#     result=get_pumbs_from_num(1)
#     if result:
#         result=result[0]
#     return result

# def insert_pump(data:PumpData):
#     result=False
#     try:
#         conn=get_connection()
#         cursor = conn.cursor()
#         query = """
#         INSERT INTO pump_data (value,timestamp)
#         VALUES (?, ?)
#         """
#         cursor.execute(query, (data.value,data.timestamp))
#         conn.commit()
#         result=True
#     except Exception as err:
#         print(err)
#     finally:
#         conn.close()
#         return result