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
        #self.channels=channels
        self.CH1=data_chanel[0]
        self.CH2=data_chanel[1]
        self.CH3=data_chanel[2]
        self.CH4=data_chanel[3]
        self.CH5=data_chanel[4]
        self.CH6=data_chanel[5]
        self.CH7=data_chanel[6]
        self.CH8=data_chanel[7]
        self.timestamp = timestamp
    def __repr__(self):
        channels=[self.CH1,self.CH2,self.CH3,self.CH4,self.CH5,self.CH6,self.CH7,self.CH8]
        return f"<AD7606_DETAIL id={self.id}, channels={channels},timestamp={self.timestamp}>"
    
class SENSOR_INFO:
    def __init__(self, id, sensor_id, AD7606_id, AD7606_channel):
        self.id = id
        self.sensor_id = sensor_id
        self.AD7606_id=AD7606_id
        self.AD7606_channel = AD7606_channel

    def __repr__(self):
        return f"<SENSOR_INFO id={self.id}, sensor_id={self.id}, AD7606_id={self.AD7606_id}, AD7606_channel={self.AD7606_channel}>"