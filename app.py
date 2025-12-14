import threading
import my_global
from my_event_dispatcher import EventDispatcher
from my_mqtt_client import My_Mqtt
from my_uart import My_Uart485 ,My_Uart,MessageFormat
from soft_timer import Soft_Timer
import time
import serial
import RPi.GPIO as GPIO

#callback tu my_mqtt_client:
def mqtt_on_message_handler(**kwargs):
    topic = kwargs.get('topic')
    msg_payload=kwargs.get('msg_payload')
    
    #day den module event_dispatcher de xu ly
    if my_global.event_dispatcher:
        my_global.event_dispatcher.dispatch('mqtt/on_message',{
            'topic':topic,
            'msg_payload':msg_payload
        })        

#callback tu uart
def uart_receive_handler(arg):
    print('receive...')
    if isinstance(arg,My_Uart):
        print(arg.buff_rx)

        #message=MessageFormat("ACK")
        #arg.send_uart(message.data)

def uart_timout_handler(arg):
    print('timout...')

#------------------------ process dispatcher event----------------------------------------- 

def mqtt_receive_msg(arg):
    print('mqtt_receive')
    payload=arg['msg_payload']
    print(f'Payload: {payload}')
    
#------------------------------------------------------------------------------------------

if __name__=='__main__':
    
    #khoi tao event_dispatcher
    my_global.event_dispatcher= EventDispatcher()
    my_global.event_dispatcher.register_handler('mqtt/on_message',mqtt_receive_msg,True)

    #chay event_dispatcher
    loop_thread = threading.Thread(target=my_global.event_dispatcher.start_loop, daemon=True)
    loop_thread.start()
    
    #dinh nghia cac topic
    sub_topics=[
        'django_app/esp/+/cmd',           # nhan lenh dieu khien tu django den app
        'django_app/esp/+/config',        # nhan lenh cau hinh tu djano den app
        'esp-app/esp/+/sensor/+/data'     # nhan du lieu tu esp (giao thuc mqtt)
    ]

    pub_topics=[
        'app-esp/esp/+/cmd',                # gui lenh dieu khien (lenh nay nhan tu django)  den esp (mqtt)
        'app-esp/esp/+/config',             # gui lenh cau hinh (lenh nay nhan tu django)  den esp (mqtt)
        'app-django/esp/+/sensor/+/data'    # gui du lieu cua esp sau khi dong goi  tu app len django
    ]

    #khoi tao module mqtt
    mqtt_1= My_Mqtt(
        topics=sub_topics,
        on_message_callback=mqtt_on_message_handler)
    
    #chay module mqtt
    mqtt_1.run()

    #khoi tao moudle uart
    ser = serial.Serial(port='/dev/ttyAMA4',
                            baudrate=9600,
                            parity=serial.PARITY_NONE,
                            bytesize=serial.EIGHTBITS,
                            stopbits=serial.STOPBITS_ONE)
    

    u1=My_Uart(ser,finish_callback=uart_receive_handler,
    timeout_callback=uart_timout_handler,timeout_s=5) 
    
    # sw_timer=Soft_Timer()
    # sw_timer.register('READ_SLAVES',read_slaves,u1,10)
    # sw_timer.start()
    
    while True:
        time.sleep(5)
        data=MessageFormat("hello")
        u1.send_uart(data.to_default_format())
    