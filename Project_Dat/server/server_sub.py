from usercustomize import *
import paho.mqtt.client as mqtt
from paho.mqtt.client import Client
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import time
import json
from info import paths,get_info,info

#khi import models đã tích hợp luôn tính năng tạo database
from my_model import (
                    DeviceType,
                    ClientInfo,
                    Device,
                    ClientConnection,
                    Temperate_Humidity)

from my_database import my_database

from process_db import ProcessDB
import datetime as dt
from soft_timer import Soft_Timer


############lấy thông tin phiên bản tử info.py################################################################
path_db=paths['db_path']
(broker_info,client_info,topic_info,properties_info)=get_info()   
######################Khởi tạo các biến: process##############################################################
db=my_database(path_db)
db.create_trigger_auto_remove_data(Temperate_Humidity,48*3600)
process=ProcessDB(db.create_session())
#######################Khởi tạo protocol mqtt, api version####################################################
protocol_info=mqtt.MQTTv311
api_version_info=mqtt.CallbackAPIVersion.VERSION1

if client_info['protocol']=='MQTT5':
    protocol_info=mqtt.MQTTv5
if client_info['api_version']=='VER2':
    api_version_info=mqtt.CallbackAPIVersion.VERSION2
##############################################################################################################
flag_connect=False 
###############################Hàm xử lý sự kiện#############################################################

#----------------CONNACK MESSAGE-----------------------------#
#CONNACK
# 0	Connection accepted
# 1	Connection refused, unacceptable protocol version
# 2	Connection refused, identifier rejected
# 3	Connection refused, server unavailable
# 4	Connection refused, bad user name or password
# 5	Connection refused, not authorized

def on_connect(client, obj, flags, reason_code, properties):
    print('#-----on_connect-----#')
    print(f'client_id={client._client_id}')   #instant mqttc
    print(f'type_pack={properties.packetType}')
    #print(f'reason_code_code={reason_code.value:X}')
    print(f'reason_code_name={str(reason_code)}')
    print('#----------#')
    
#PUBACK: 4
#PUBCOMP : 7
def on_publish(client, obj, mid, reason_code, properties): 
    print('#-----on_publish------------#')
    print(f'client_id={client._client_id}')   #instant mqttc
    print(f'message_id={mid}')
    print(f'type_pack={properties.packetType}')
    print(f'reason_code_code={reason_code.value:X}')
    print(f'reason_code_name={str(reason_code)}')
    print('#-----------------#')

#--------------------SUBACK MESSAGE------------------------#
#SUBACK
# 0	Success - Maximum QoS 0
# 1	Success - Maximum QoS 1
# 2	Success - Maximum QoS 2
# 128	Failure

def on_subscribe(client, obj, mid, reason_code_list, properties):
    print('#-----on_subscribe-----#')
    print(f'client_id={client._client_id}')   #instant mqttc
    print(f'message_id={mid}')
    print(f'type_pack={properties.packetType}')
    #print(f'reason_code_code={reason_code_list[0].value:X}')
    print(f'reason_code_name={str(reason_code_list)}')
    print('#----------#')
#--------------------MESSAGE------------------------#
#payload
#topic
#qos
#retain flag
#-------------------retained message---------------#
# A retained message is a normal MQTT message with the retained flag set to true. 
# The broker stores the last retained message and the corresponding QoS for that topic. 
# Each client that subscribes to a topic pattern that matches the topic of the retained message receives the retained message immediately after they subscribe. 
# The broker stores only one retained message per topic
#-------------------How to Send a Retained Message in MQTT---------------#
#To mark a message as retained, all you need to do is set the retained flag of your MQTT publish message to true
def on_message(mqttc, obj, msg):
    global process
    print(f'{msg.mid}-{str(msg.qos)}')
    print(f'{msg.topic}')
    msg_payload_decode=msg.payload.decode()
    print(msg_payload_decode)
    match msg.topic:
        case 'iot/heartbeat':
            print('xử lý heartbeat')
        case 'iot/offline':
            print('xử lý offline')
        case 'iot/data/temperate_humidity':
            print('xử lý dữ liệu dht22')
   
    # parts=msg.topic.split('/')
    # if len(parts)==3 and parts[0]=='iot' and parts[-1]=='devices':
    #     try:
    #         message_dict=json.loads(msg.payload.decode())
    #         client_id_=message_dict['client']['id']
    #         client_name_=message_dict['client']['name']
    #         devices_=message_dict['devices']
    #         if len(devices_)>0:
    #             devices= [Device(
    #                                 client_id=client_id_,
    #                                 device_id=d['device_id'],
    #                                 type=DeviceType(d['type']),
    #                                 name=d['name'],
    #                                 location=d['location'],
    #                             ) for d in devices_]             
    #             client_=process.querry_by_condition(ClientInfo,ClientInfo.client_id==client_id_)                
    #             if client_:
    #                 for dev in devices:
    #                     process.insert(dev)
    #             else:   
    #                 client_=ClientInfo(client_id=client_id_,name=client_name_)
    #                 client_.devices=devices
    #                 process.insert(client_)                  
    #     except Exception as error:
    #         print(error)     
    # else:
    #     match msg.topic:
    #         case 'iot/heartbeat':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client']['id']
    #             status_connect_=message_dict['status_connect']
    #             timestamp_online_=message_dict['timestamp_online']
    #             client_connect_=ClientConnection(
    #                 client_id=client_id_,
    #                 status_connect=status_connect_,
    #                 timestamp_online=dt.datetime.fromisoformat(timestamp_online_)
    #             )
    #             client_connect_tmp=process.querry_by_condition(ClientConnection,ClientConnection.client_id==client_id_)
    #             if client_connect_tmp:
    #                 process.update(client_connect_tmp,client_connect_)
    #             else:                  
    #                 process.insert(client_connect_)
                    
    #         case 'iot/offline':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             status_connect_=message_dict['status_connect']
    #             timestamp_offline_=dt.datetime.now()
    #             client_connect_=ClientConnection(
    #                 client_id=client_id_,
    #                 status_connect=status_connect_,
    #                 timestamp_offline=timestamp_offline_
    #                 )   
    #             client_connect_tmp=process.querry_by_condition(ClientConnection,ClientConnection.client_id==client_id_)
    #             if client_connect_tmp:
    #                 process.update(client_connect_tmp,client_connect_)
    #             else:                  
    #                 process.insert(client_connect_)                           
        
    #         case 'iot/data/temperate':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             device_id_=message_dict['device_id']
    #             value_=message_dict['value']
    #             timestamp_=message_dict['timestamp']
    #             temperature_=Temperature(
    #                 client_id=client_id_,
    #                 device_id=device_id_,
    #                 value=value_,
    #                 timestamp=dt.datetime.fromisoformat(timestamp_)
    #                 )
    #             process.insert(temperature_,
    #                             ClientInfo,ClientInfo.client_id==temperature_.client_id,
    #                             Device,Device.device_id==temperature_.device_id)
            
    #         case 'iot/data/temperate_humidity':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             device_id_=message_dict['device_id']
    #             value_temperate_=message_dict['value_temperate']
    #             value_humidity_=message_dict['value_humidity']
    #             timestamp_=message_dict['timestamp']
    #             temperature_humidity_=Temperate_Humidity(
    #                 client_id=client_id_,
    #                 device_id=device_id_,
    #                 value_temperate=value_temperate_,
    #                 value_humidity=value_humidity_,
    #                 timestamp=dt.datetime.fromisoformat(timestamp_)
    #                 )
    #             process.insert(temperature_humidity_,
    #                             ClientInfo,ClientInfo.client_id==temperature_humidity_.client_id,
    #                             Device,Device.device_id==temperature_humidity_.device_id)
            
    #         case 'iot/data/switch':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             device_id_=message_dict['device_id']
    #             status_=message_dict['status']
    #             timestamp_=message_dict['timestamp']
    #             switch_=Switch(
    #                 client_id=client_id_,
    #                 device_id=device_id_,
    #                 status=status_,
    #                 timestamp=dt.datetime.fromisoformat(timestamp_)
    #                 )
    #             process.insert(switch_,
    #                             ClientInfo,ClientInfo.client_id==switch_.client_id,
    #                             Device,Device.device_id==switch_.device_id)
           
    #         case 'iot/data/lamp':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             device_id_=message_dict['device_id']
    #             status_=message_dict['status']
    #             brightness_=message_dict['brightness']
    #             timestamp_=message_dict['timestamp']
    #             lamp_=Lamp(
    #                 client_id=client_id_,
    #                 device_id=device_id_,
    #                 status=status_,
    #                 brightness=brightness_,
    #                 timestamp=dt.datetime.fromisoformat(timestamp_)
    #                 )
    #             process.insert(lamp_,
    #                             ClientInfo,ClientInfo.client_id==lamp_.client_id,
    #                             Device,Device.device_id==lamp_.device_id)
            
    #         case 'iot/data/humidity':
    #             message_dict=json.loads(msg.payload.decode())
    #             client_id_=message_dict['client_id']
    #             device_id_=message_dict['device_id']
    #             value_=message_dict['value']
    #             timestamp_=message_dict['timestamp']
    #             humidity_=Humidity(
    #                 client_id=client_id_,
    #                 device_id=device_id_,
    #                 value=value_,
    #                 timestamp=dt.datetime.fromisoformat(timestamp_)
    #                 )
    #             process.insert(humidity_,
    #                             ClientInfo,ClientInfo.client_id==humidity_.client_id,
    #                             Device,Device.device_id==humidity_.device_id)
            
    #         case 'iot/data/weather':
    #             message_dict=json.loads(msg.payload.decode())
    #             weather_=Weather(
    #                 client_id=message_dict['client_id'],
    #                 device_id=message_dict['device_id'],
    #                 inside_humidity=message_dict['inside_humidity'],
    #                 inside_temperature=message_dict['inside_temperature'],
    #                 inside_CO2=message_dict['inside_CO2'],
    #                 outside_humidity=message_dict['outside_humidity'],
    #                 outside_temperature=message_dict['outside_temperature'],
    #                 outside_CO2=message_dict['outside_CO2'],
    #                 timestamp=dt.datetime.fromisoformat(message_dict['timestamp'])
    #                 )
    #             process.insert(weather_,
    #                             ClientInfo,ClientInfo.client_id==weather_.client_id,
    #                             Device,Device.device_id==weather_.device_id)
                    
##-------------------code-----------------------##

def on_connect_fail():
    print('connect fail')

def on_disconnect():
    print('disconnect')
 
def init_device_id_message():
    global process
    message=[]
    clients = process.querry_all(ClientInfo)
    if clients is not None:
        for client in clients:
            devices=client.devices
            devices_info = []
            for device in devices:
                devices_info.append({'device_id':device.device_id,'type':device.type.name})
            message.append({'client':client.client_id,'devices':devices_info})
    return message

def publish_device_id_message(mqttc:Client,messages):
    if messages:
        for message in messages:
            client_id=message['client']
            topic=f'{client_id}/devices'
            mqttc.publish(topic,json.dumps(message),qos=1,retain=True)
    else:
        print("lỗi tìm thiết bị")

def subcribe_topic_message(mqttc:Client,topics):
    for sub in topics:
        mqttc.subscribe(sub,qos=1)

def client_connect(mqttc):
    global properties_info,broker_info,topic_info,flag_connect
    if flag_connect==False:
        try:   
            connect_properties = Properties(PacketTypes.CONNECT)
            connect_properties.SessionExpiryInterval = properties_info['SessionExpiryInterval']
            mqttc.will_set(topic_info['will']['topic'],json.dumps(topic_info['will']['message']),qos=1)            
            mqttc.connect(host=broker_info['ip'],
                    port=broker_info['port'],
                    keepalive=properties_info['keepalive'],
                    clean_start=properties_info['clean_start'],
                    properties=connect_properties)
        except Exception as err:
            print(err)
            print('reconnect')
        else:
            flag_connect=True
            subcribe_topic_message(mqttc,topic_info['subcrible'])
            messages=init_device_id_message()
            publish_device_id_message(mqttc,messages)           

def main():
    mqttc = Client(api_version_info,client_info['id'],protocol=protocol_info)
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    mqttc.on_publish=on_publish
    mqttc.on_connect_fail=on_connect_fail
    mqttc.on_disconnect=on_disconnect
    client_connect(mqttc)
    mqttc.loop_start()
    
    sw_timer=Soft_Timer()
    sw_timer.register('connect',client_connect,mqttc,info['delay']['delay_connect'])
    sw_timer.start()
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
   
 





        


