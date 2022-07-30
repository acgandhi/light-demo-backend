from xmlrpc.client import boolean
from fastapi import FastAPI
from fastapi_mqtt import FastMQTT, MQTTConfig
from fastapi.middleware.cors import CORSMiddleware


import json

from pydantic import BaseModel

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

mqtt_config = MQTTConfig(host="mqttbroker.private.tcehomelab.com")

mqtt = FastMQTT(
    config=mqtt_config
)

mqtt.init_app(app)


def get_light_state():
    with open('light_state.json') as f:
        light_state = json.load(f)['value']
    return light_state

def set_light_state(state: bool):
    light_state = {'value': state}
    with open('light_state.json', 'w') as f:
        json.dump(light_state, f)


@mqtt.on_connect()
def connect(client, flags, rc, properties):
    mqtt.client.subscribe("zwave/nodeID_2/37/0/currentValue") #subscribing mqtt topic
    print("Connected: ", client, flags, rc, properties)

@mqtt.on_message()
async def message(client, topic, payload, qos, properties):
    print("Received message: ",topic, payload.decode(), qos, properties)
    set_light_state(json.loads(payload)['value'])
    # light_state = payload.decode()['value']


@mqtt.on_disconnect()
def disconnect(client, packet, exc=None):
    print("Disconnected")

@mqtt.on_subscribe()
def subscribe(client, mid, qos, properties):
    print("subscribed", client, mid, qos, properties)

# @mqtt.on_connect()
# def connect(client, flags, rc, properties):
#     mqtt.client.subscribe("/mqtt") #subscribing mqtt topic
#     print("Connected: ", client, flags, rc, properties)

class LightState(BaseModel):
    state: bool


@app.put("/light")
async def set_light(new_state: LightState):
    mqtt.publish("zwave/nodeID_2/37/0/targetValue/set", str(new_state.state))

@app.get("/light")
async def get_light() -> LightState:
    return LightState(state=get_light_state())