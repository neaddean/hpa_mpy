from umqtt.simple import MQTTClient

c = MQTTClient("esp32-dev", "mqtt.thingsboard.cloud", user="h2sd5e2ppoz03j801azy", password='')
c.connect()

c.publish("v1/devices/me/telemetry", '{"temperature":25}')
