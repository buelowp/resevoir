import time
import paho.mqtt.client as paho
import sys
from OmegaExpansion import oledExp,relayExp

broker = "172.24.1.10"
client = paho.Client("resevoir") 

def turn_pump_on():
	relayExp.setChannel(7, 0, 1)
	print_relay_status()

def turn_pump_off():
	relayExp.setChannel(7, 0, 0)
	print_relay_status()

def open_valve():
	relayExp.setChannel(7, 1, 1)
	print_relay_status()

def close_valve():
	relayExp.setChannel(7, 1, 0)
	print_relay_status()

def run_test():
	print("testing interface")

def print_status(connected):
	oledExp.clear()
	oledExp.setCursor(0, 0)
	oledExp.write("Resevoir")
	oledExp.setCursor(1, 0)
	if connected == True :
		oledExp.write("Broker: " + broker)
		oledExp.setCursor(2, 0)
			
	if connected == True :
		oledExp.write("Connected")
	else:
		oledExp.write("Disconnected")

	print_relay_status()

def print_relay_status():
	bInit = relayExp.checkInit(7)
	oledExp.setCursor(3, 0)
	if (bInit == 0):
		oledExp.write("Relay Not Available")		
	else:
		oledExp.write("Relay Available")		

	oledExp.setCursor(4, 0)
	if (relayExp.readChannel(7, 0) == 0):
		oledExp.write("Relay 0 is off")
	else:
		oledExp.write("Relay 0 is on")

	oledExp.setCursor(5, 0)
	if (relayExp.readChannel(7, 1) == 0):
		oledExp.write("Relay 1 is off")
	else:
		oledExp.write("Relay 1 is on")

def on_connect(client, userdata, flags, rc):
	print("Connection returned result: " + str(rc))
	if rc == 0:
		print_status(True)
	else:
		print_status(False)

def on_disconnect(client, userdata, rc):
	print_status(False)

def on_message(client, userdata, message):
	if (message.topic == "resevoir/pump/on"):
		turn_pump_on()

	if (message.topic == "resevoir/pump/off"):
		turn_pump_off()

	if (message.topic == "resevoir/valve/open"):
		open_valve()

	if (message.topic == "resevoir/valve/close"):
		close_valve()

	if (message.topic == "resevoir/test"):
		run_test()

#	print("Received message '" + str(message.payload) + "' on topic '" + message.topic + "' with QoS " + str(message.qos))

def main(argv):
	oledExp.driverInit()
	client.on_message = on_message
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.connect(broker)	#connect
	oledExp.setDisplayPower(1)
	relayExp.driverInit(7)

	try:
		client.subscribe("resevoir/#") #subscribe
		client.loop_start()
		while True:
			time.sleep(1);

	except KeyboardInterrupt:
		print("exiting on ctrl-c")
		client.disconnect() #disconnect
		client.loop_stop() #stop loop
		relayExp.setChannel(7, 0, 0)
		relayExp.setChannel(7, 1, 0)
		time.sleep(5)
		sys.exit(0)
	
if __name__ == "__main__":
	main(sys.argv)
