import json

from esp32 import NVS
from umqtt.simple import MQTTClient

from util.nvs import nvs_get_str


def get_app_type():
    nvs = NVS("_config")

    mqtt_broker = nvs_get_str(nvs, "mqtt_broker")
    access_token = nvs_get_str(nvs, "access_token")

    rsp = []

    def mqtt_sub_cb(topic, msg):
        topic = topic.decode()
        last_received_rpc_id = topic.split("/")[-1]
        msg = json.loads(msg)
        rsp.append((msg, last_received_rpc_id))

    mqtt_client = MQTTClient("lobby",
                             mqtt_broker,
                             user=access_token,
                             password='')

    mqtt_client.connect()
    mqtt_client.set_callback(mqtt_sub_cb)
    mqtt_client.subscribe("v1/devices/me/attributes/response/+")

    mqtt_client.publish("v1/devices/me/attributes/request/0", "{'sharedKeys': 'app'}")
    mqtt_client.wait_msg()
    app_type = rsp[0][0]['shared']['app']
    print(f"App type: {app_type}")

    return app_type
