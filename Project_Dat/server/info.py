import os

client_id='00000'

info={
    
    "server":{        
                "local":{"ip":"localhost","port":1883}, 
                
                "remote":{"ip":"0.tcp.ap.ngrok.io","port":12324}
            },
    
    "client":{
                "id":f'{client_id}',
                "protocol":"MQTT5",
                "api_version":"VER2"
    },

    "properties":{
        "SessionExpiryInterval":100,
        "keepalive":60,
        "clean_start":True,
    },
    
    "delay":{
        "delay_data":3,
        "delay_connect":5,
        "delay_heartbeat":5
    },

    "topic":{
                "subcrible":[
                    "iot/data/#",
                    "iot/heartbeat",
                    "iot/offline"
                ],
                "publish":{
                    "info":'iot/server/info'
                },
                
                "will":{
                    "topic":"iot/server/offline",
                    "message":{
                        "client_id":f'{client_id}',
                        "status_connect":False}
                },              
            },
    
    "api":{
        
            "api_local":{"ip":"localhost","port":5000},
                
            "api_global":{"ip":"0.0.0.0","port":5000},
            
            "timeout_cache":10
    }
}

paths={
    "db_path":f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__),'../server/iot_database.db'))}"  
}


def get_info(mode=None):
    if mode=='remote':
        return (info['server']['remote'], 
                info['client'],
                info['topic'],
                info['properties'])
    else:
        return (info['server']['local'],
                info['client'],
                info['topic'],
                info['properties'])

def get_ip_api(mode=None):
    if mode=='remote':
        return info['api']['api_global']

    else:
        return info['api']['api_local']

def get_timout_cache():
    return info['api']['timeout_cache']