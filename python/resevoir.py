import time
import paho.mqtt.client as paho
import sys
from OmegaExpansion import oledExp,relayExp

broker = "172.24.1.10"
client = paho.Client("resevoir") 
oled_address = 0
connected = False

def turn_pump_on():
	global oled_address
	if (relayExp.setChannel(oled_address, 0, 1) == 0):
		client.publish("control/pump/on")
	print_status()

def turn_pump_off():
	global oled_address
	if (relayExp.setChannel(oled_address, 0, 0) == 0):
		client.publish("control/pump/off")
	print_status()

def open_valve():
	global oled_address
	if (relayExp.setChannel(oled_address, 1, 1) == 0):
		client.publish("control/valve/open")
	print_status()

def close_valve():
	global oled_address
	if (relayExp.setChannel(oled_address, 1, 0) == 0):
		client.publish("control/valve/close")
	print_status()

def run_test():
	print("testing interface")

def print_status():
	global connected
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

def print_relay1_status():
	global oled_address
	oledExp.setCursor(4, 0)
	if (relayExp.readChannel(oled_address, 0) == 0):
		oledExp.write("Pump:  off")
	else:
		oledExp.write("Pump:  on ")

def print_relay2_status():
	global oled_address
	oledExp.setCursor(5, 0)
	if (relayExp.readChannel(oled_address, 1) == 0):
		oledExp.write("Valve: closed")
	else:
		oledExp.write("Valve: open  ")

def return_state():
	relayState = '00'
	if (relayExp.readChannel(oled_address, 0) == 1):
		relayState[0] = '1'
	if (relayExp.readChannel(oled_address, 1) == 1):
		relayState[1] = '1'

	client.publish("control/state", relayState, 1, True)

def print_relay_status():
	global oled_address
	bInit = relayExp.checkInit(oled_address)
	oledExp.setCursor(3, 0)
	if (bInit == 0):
		oledExp.write("Relay Not Available")		
	else:
		oledExp.write("Relay Available")		
		print_relay1_status()
		print_relay2_status()

def on_connect(client, userdata, flags, rc):
	global connected
	if rc == 0:
		connected = True
		print_status()
	else:
		connected = False
		print_status()

def on_disconnect(client, userdata, rc):
	global oled_address
	global connected
	relayExp.setChannel(oled_address, 0, 0)
	relayExp.setChannel(oled_address, 1, 0)
	connected = False
	print_status()

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

	if (message.topic == "resevoir/state"):
		return_state()

def main(argv):
	global oled_address
	oled_address = int(argv[1])
	print("oled_address is " + str(oled_address))
	oledExp.driverInit()
	client.on_message = on_message
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.connect(broker)	#connect
	oledExp.setDisplayPower(1)
	relayExp.driverInit(oled_address)

	try:
		client.subscribe("resevoir/#") #subscribe
		client.loop_start()
		while True:
			time.sleep(1);

	except KeyboardInterrupt:
		print("exiting on ctrl-c")
		client.disconnect() #disconnect
		client.loop_stop() #stop loop
		relayExp.setChannel(oled_address, 0, 0)
		relayExp.setChannel(oled_address, 1, 0)
		time.sleep(2)
		sys.exit(0)
	
if __name__ == "__main__":
	main(sys.argv)
