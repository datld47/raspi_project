
from sqlalchemy import Column,Integer,String,Float,ForeignKey,Boolean,UniqueConstraint,Enum,DateTime
from sqlalchemy.orm import declarative_base,relationship
import enum

Base=declarative_base()

class BaseModel:                   
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class DeviceType(enum.Enum):
    TH=0,
    SS=1,
    VS=2

class ClientInfo(Base):
    __tablename__ = 'clients'  
    id = Column(Integer, primary_key=True)
    client_id=Column(String, unique=True)
    name = Column(String)
    devices=relationship('Device',back_populates='client',cascade="all, delete-orphan")
    connects=relationship('ClientConnection',back_populates='client',cascade="all, delete-orphan")

class ClientConnection(Base):
    __tablename__ = 'connects'  
    id = Column(Integer, primary_key=True)
    client_id=Column(String, ForeignKey('clients.client_id'),nullable=False,unique=True)
    status_connect=Column(Boolean,default=False)
    timestamp_online=Column(DateTime)
    timestamp_offline=Column(DateTime)
    client=relationship('ClientInfo',back_populates='connects')
    
class Device(Base):
    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'),nullable=False)
    device_id=Column(String,nullable=False)
    type=Column(Enum(DeviceType))
    name=Column(String)
    location=Column(String)
    __table_args__ = (
        UniqueConstraint('client_id', 'device_id', name='uix_client_device_id'),
    )
    client=relationship('ClientInfo',back_populates='devices')
    temperate_hummidity_s = relationship('Temperate_Humidity', back_populates='device', cascade="all, delete-orphan")

class Temperate_Humidity(Base):
    __tablename__ = 'temperate_humidity'
    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey('clients.client_id'),nullable=False)
    device_id = Column(String, ForeignKey('devices.device_id'),nullable=False)
    value_temperate = Column(Float)
    value_humidity= Column(Float)
    timestamp=Column(DateTime)
    device = relationship('Device', back_populates='temperate_hummidity_s')
