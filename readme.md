pip install paho-mqtt


### UartManager

- Thuoc tinh
    
    - serial
    - status_mutex
    - buff_rx
    - buff_tx
    - queue
    - timeout_callback
    - finish_callback
    - timer

    - pre_bytes_in_buffer: de nhan biet khi nao truyen xong
    - DE_PIN
    - RE_PIN 

    - tiemout_s
    - time_s
    - time_3_5_char_s
    - timeout_tick = timeout_s/self.time_s

- Phuong thuc
    - enable_mode_transmit() : chuyen sang mode tranmist:  raspi phat du lieu
    - enable_mode_receive() : chuyen sang mode receive:  raspi lang nghe
    - start_timer() : khoi tao timer  cho viec dinh thoi: timeout
    - stop_timer()  : dung timer
    - timer_callback(): khi timer ellapse (ellapse  sau moi  time_s): de phat hie du lieu

    - register_timeout_callback() : dang ky ham xu ly su kien timeout
    - register_finish_callback()  : dang ky ham xu ly su kien khi nhan du lieu hoan thanh
    - send_uart() : gui du lieu
    - free() : giai phong tai nguyen:queue, mutex, timer, io....
