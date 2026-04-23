class AD7606_INFO:
    def __init__(self, id, AD7606_id, AD7606_description):
        self.id = id
        self.AD7606_id = AD7606_id
        self.AD7606_description = AD7606_description

    def __repr__(self):
        return f"<AD7606_INFO id={self.id}, AD7606_id={self.AD7606_id}, AD7606_description={self.AD7606_description}>"

class AD7606_CHANNEL:
    def __init__(self, id,AD7606_channel):
        self.id = id
        self.AD7606_channel = AD7606_channel
    
    def __repr__(self):
        return f"<AD7606_CHANNEL id={self.id}, AD7606_channel={self.valuAD7606_channele}>"

class AD7606_DETAIL:
    def __init__(self, id, AD7606_id,data_chanel,timestamp):
        self.id = id
        self.AD7606_id=AD7606_id
        self.ch1=data_chanel[0]
        self.ch2=data_chanel[1]
        self.ch3=data_chanel[2]
        self.ch4=data_chanel[3]
        self.ch5=data_chanel[4]
        self.ch6=data_chanel[5]
        self.ch7=data_chanel[6]
        self.ch8=data_chanel[7]
        self.timestamp = timestamp
        self.block=0
        self.convert_adc()
        
    def __repr__(self):
        channels=[self.ch1,self.ch2,self.ch3,self.ch4,self.ch5,self.ch6,self.ch7,self.ch8]
        return f"<AD7606_DETAIL id={self.id}, channels={channels},timestamp={self.timestamp}>"
    
    def to_dict(self,block=0):
        data=self.__dict__
        data.pop('id')
        data.pop('AD7606_id')
        data['block']=block
        return data
    
    def convert_adc(self):
        self.ch1= (self.ch1/32767.0 )*25
        self.ch2= (self.ch2/32767.0 )*450-50
        self.ch3= (self.ch3/32767.0 )*10*100*1000
        self.ch4= (self.ch4/32767.0 )*10*100*1000
        self.ch5= (self.ch5/32767.0 )*10
        self.ch6= (self.ch6/32767.0 )*10
        self.ch7= (self.ch7/32767.0 )*10
        self.ch8= (self.ch8/32767.0 )*10

class FR_E700:
    def __init__(self,data):
        self.frequency=data[0]
        self.current=data[1]
        self.torque=data[2]
        
    def to_dict(self):
        data=self.__dict__
        return data


class AD7606_FRE700:
    def __init__(self, id, AD7606_id,data_chanel,timestamp,data_fre700):
        self.id = id
        self.AD7606_id=AD7606_id
        self.ch1=data_chanel[0]
        self.ch2=data_chanel[1]
        self.ch3=data_chanel[2]
        self.ch4=data_chanel[3]
        self.ch5=data_chanel[4]
        self.ch6=data_chanel[5]
        self.ch7=data_chanel[6]
        self.ch8=data_chanel[7]
        self.timestamp = timestamp
        self.frequency=data_fre700[0]
        self.current=data_fre700[1]
        self.torque=data_fre700[2]
        self.block=0
        self.convert_adc()
        
    def __repr__(self):
        channels=[self.ch1,self.ch2,self.ch3,self.ch4,self.ch5,self.ch6,self.ch7,self.ch8]
        fre700s=[self.frequency,self.current,self.torque]
        return f"<AD7606_DETAIL id={self.id}, channels={channels},timestamp={self.timestamp}\nFRE700 data={fre700s}>"
    
    def to_dict(self,block=0):
        data=self.__dict__
        data.pop('id')
        data.pop('AD7606_id')
        data['block']=block
        return data
    
    def convert_adc(self):
        self.ch1= (self.ch1/32767.0 )*25
        self.ch2= (self.ch2/32767.0 )*450-50
        self.ch3= (self.ch3/32767.0 )*10*100*1000
        self.ch4= (self.ch4/32767.0 )*10*100*1000
        self.ch5= (self.ch5/32767.0 )*10
        self.ch6= (self.ch6/32767.0 )*10
        self.ch7= (self.ch7/32767.0 )*10
        self.ch8= (self.ch8/32767.0 )*10



class SENSOR_INFO:
    def __init__(self, id, sensor_id, AD7606_id, AD7606_channel):
        self.id = id
        self.sensor_id = sensor_id
        self.AD7606_id=AD7606_id
        self.AD7606_channel = AD7606_channel

    def __repr__(self):
        return f"<SENSOR_INFO id={self.id}, sensor_id={self.id}, AD7606_id={self.AD7606_id}, AD7606_channel={self.AD7606_channel}>"