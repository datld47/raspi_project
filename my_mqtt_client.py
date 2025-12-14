from paho.mqtt.client import Client
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import paho.mqtt.client as mqtt
import json
import time

class My_Mqtt(Client):

    def __init__(self,**kwargs):
        
        protocol_info=kwargs.get('protocol_info',mqtt.MQTTv5)
        api_version_info=kwargs.get('api_version_info',mqtt.CallbackAPIVersion.VERSION2)
        client_id=kwargs.get('client_id','00000')
        
        super().__init__(
            api_version_info,
            client_id,
            protocol=protocol_info
        )

        self.on_message_callback=kwargs.get('on_message_callback',None)
        self.protocol_info=kwargs.get('protocol_info',mqtt.MQTTv5)
        self.api_version_info=kwargs.get('api_version_info',mqtt.CallbackAPIVersion.VERSION2)
        self.client_id=kwargs.get('client_id','00000')
        self.flag_connect=False
        self.session_expiry_interval=kwargs.get('session_expiry_interval',100)
        self.keepalive=kwargs.get('keepalive',60)
        self.clean_start=kwargs.get('clean_start',True)
        self.topic_will=kwargs.get('topic_will',"client/offline")
        self.topics_to_subscribe=kwargs.get('topics',[])

        self.msg_will=kwargs.get('msg_will',{
                        "client_id":f'{self.client_id}',
                        "status_connect":False})
        
        self.reconnect_delay_set(min_delay=5, max_delay=30)
        
        self.host=kwargs.get('host','127.0.0.1')
        self.port=kwargs.get('port',1883)
     
        self.on_message = self.on_message_
        self.on_connect = self.on_connect_
        self.on_subscribe = self.on_subscribe_
        self.on_publish=self.on_publish_
        self.on_disconnect=self.on_disconnect_

    def run(self):
        self.client_connect()
        self.loop_start()

    def subscribe_topic_message(self):
        
        if not self.is_connected():
            print(f'client {self.client_id} is not connected')
            return
        
        if not self.topics_to_subscribe:
            print('not topics subscribe')
            return
        
        for topic in self.topics_to_subscribe:
            rc,mid=self.subscribe(topic,qos=1)
            if rc==mqtt.MQTT_ERR_SUCCESS:
                print(f'subcribing to {topic} (mid={mid})')
            else:
                print(f'Failee subcribing to {topic} rc={mqtt.error_string(rc)}')

    def publish_message(self,topic,payload,qos=1):
        if not self.is_connected():
            print(f'client {self.client_id} is not connected')
            return
        self.publish(topic,json.dumps(payload),qos=qos)

    def client_connect(self,max_retry=10):
        
        if self.is_connected():
            print('Already connected...')
            return 
        
        retry_count = 0

        while not self.is_connected() and retry_count < max_retry:
   
            try:   
                connect_properties = Properties(PacketTypes.CONNECT)
                connect_properties.SessionExpiryInterval = self.session_expiry_interval
                
                if not self._will:
                    self.will_set(self.topic_will,json.dumps(self.msg_will),qos=1)
                
                print(f'start connect: host={self.host} port={self.port}')       
                self.connect(host=self.host,
                        port=self.port,
                        keepalive=self.keepalive,
                        clean_start=self.clean_start,
                        properties=connect_properties)                
                print('connect to broker ok')
                return
                
            except Exception as err:
                retry_count += 1
                wait_time = min(retry_count * 5, 30)
                print(f'[MQTT] Connect failed: {err}')
                print(f'[MQTT] Retry in {wait_time}s (attempt {retry_count})')
                time.sleep(wait_time)

        print('[MQTT] Failed to connect after multiple attempts.')

    def on_connect_(self,client, obj, flags, reason_code, properties):
        # print('#-----on_connect-----#')
        # print(f'client_id={client._client_id}')   #instant mqttc
        # print(f'type_pack={properties.packetType}')
        # #print(f'reason_code_code={reason_code.value:X}')
        # print(f'reason_code_name={str(reason_code)}')
        # print('#----------#')
        print('---on_connect---')
        self.subscribe_topic_message()

    def on_message_(self,mqttc, obj, msg):
        # global process
        # print(f'{msg.mid}-{str(msg.qos)}')
        # print(f'{msg.topic}')
        # msg_payload_decode=msg.payload.decode()
        # print(msg_payload_decode)
        # match msg.topic:
        #     case 'iot/heartbeat':
        #         print('xử lý heartbeat')
        #     case 'iot/offline':
        #         print('xử lý offline')
        #     case 'iot/data/temperate_humidity':
        #         print('xử lý dữ liệu dht22')
        print('--on_message---')
        try:
            topic=msg.topic
            msg_payload_decode = msg.payload.decode()
            print(f'topic: {topic}')
            print(f'Payload: {msg_payload_decode}')
        except Exception as e:
            print(f'[My_Mqtt] Failed to decode payload: {e}')
            return
        
        if self.on_message_callback:
            self.on_message_callback(topic=topic,msg_payload=msg_payload_decode)

        # if self.event_dispatcher and isinstance(self.event_dispatcher, EventDispatcher):
        #     self.event_dispatcher.dispatch('mqtt/on_message',msg)
    
    def on_publish_(self,client, obj, mid, reason_code, properties): 
        # print('#-----on_publish------------#')
        # print(f'client_id={client._client_id}')   #instant mqttc
        # print(f'message_id={mid}')
        # print(f'type_pack={properties.packetType}')
        # print(f'reason_code_code={reason_code.value:X}')
        # print(f'reason_code_name={str(reason_code)}')
        # print('#-----------------#')
        print('---on_publish--')

    def on_subscribe_(self,client, obj, mid, reason_code_list, properties):
        # print('#-----on_subscribe-----#')
        # print(f'client_id={client._client_id}')   #instant mqttc
        # print(f'message_id={mid}')
        # print(f'type_pack={properties.packetType}')
        # #print(f'reason_code_code={reason_code_list[0].value:X}')
        # print(f'reason_code_name={str(reason_code_list)}')
        # print('#----------#')
        print('---on_subcribe---')
        print(f'client_id={client._client_id}  mid={mid}')
    
    def on_disconnect_(self,client,obj,reason_code,properties):
        print('---disconnect---')
        print(f'Reason: {reason_code} ({mqtt.error_string(reason_code)})')
        print('Waiting for automatic reconnect...')