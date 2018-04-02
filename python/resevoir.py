import time
import paho.mqtt.client as paho
import sys
import socket
import fcntl
import struct
from OmegaExpansion import oledExp,relayExp

broker = "172.24.1.10"
client = paho.Client("resevoir") 
oled_address = 0
connected = False
pingSuccess = False
pingStarted = False
pingFailCount = 0
clientConnected = False
g_buttonsConnected = False
g_ipAddr = ""

def get_ip_address():
	global g_ipAddr
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	g_ipAddr = s.getsockname()[0]
	s.close()

# Turn the pump on, but only if the valve is open
# otherwise, just ignore the command
def turn_pump_on():
	global oled_address
	if (relayExp.readChannel(oled_address, 1) == 1):
		if (relayExp.setChannel(oled_address, 0, 1) == 0):
			client.publish("control/pump/on")

	print_status()

# Turn the pump off, then tell the controller we did it
def turn_pump_off():
	global oled_address
	if (relayExp.setChannel(oled_address, 0, 0) == 0):
		client.publish("control/pump/off")
	print_status()

# Open the water valve. This just makes it possible to
# get the water out, it does not start the pump
def open_valve():
	global oled_address
	if (relayExp.setChannel(oled_address, 1, 1) == 0):
		client.publish("control/valve/open")
	print_status()

# Close the valve
# If the pump is on, turn it off first
def close_valve():
	global oled_address
	if (relayExp.readChannel(oled_address, 0) == 1):
		turn_pump_off()

	if (relayExp.setChannel(oled_address, 1, 0) == 0):
		client.publish("control/valve/close")
	print_status()

def print_status():
	global connected, g_buttonsConnected, g_ipAddr
	oledExp.clear()
	oledExp.setCursor(0, 0)
	oledExp.write("Host  : " + g_ipAddr)
	oledExp.setCursor(1, 0)
	oledExp.write("Broker: " + broker)
	oledExp.setCursor(2, 0)
	if (g_buttonsConnected == True):
		oledExp.write("Client: Connected")
	else:
		oledExp.write("                 ")

	print_relay_status()

def print_relay1_status():
	global oled_address
	oledExp.setCursor(4, 0)
	if (relayExp.readChannel(oled_address, 0) == 0):
		oledExp.write("Pump  : off")
	else:
		oledExp.write("Pump  : on ")

def print_relay2_status():
	global oled_address
	oledExp.setCursor(5, 0)
	if (relayExp.readChannel(oled_address, 1) == 0):
		oledExp.write("Valve : closed")
	else:
		oledExp.write("Valve : open  ")

def return_state():
	global pingStarted, pingFailCount, g_buttonsConnected
	relayState = '00'
	if (relayExp.readChannel(oled_address, 0) == 1):
		relayState[0] = '1'
	if (relayExp.readChannel(oled_address, 1) == 1):
		relayState[1] = '1'

	client.publish("control/state", relayState, 1, True)
	pingStarted = True
	g_buttonsConnected = True
	print_status()

def print_relay_status():
	global oled_address
	bInit = relayExp.checkInit(oled_address)
	oledExp.setCursor(3, 0)
	if (bInit == 0):
		oledExp.write("Relay : Disabled")		
	else:
		oledExp.write("Relay : Available")		
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
	global oled_address, g_buttonsConnected
	global connected
	relayExp.setChannel(oled_address, 0, 0)
	relayExp.setChannel(oled_address, 1, 0)
	connected = False
	g_buttonsConnected = False
	print_status()

def on_message(client, userdata, message):
	global pingSuccess, pingFailCount, pingStarted, g_buttonsConnected
	if (message.topic == "resevoir/pump/on"):
		turn_pump_on()

	if (message.topic == "resevoir/pump/off"):
		turn_pump_off()

	if (message.topic == "resevoir/valve/open"):
		open_valve()

	if (message.topic == "resevoir/valve/close"):
		close_valve()

	if (message.topic == "resevoir/state"):
		return_state()

	if (message.topic == "resevoir/ping"):
		client.publish("control/ping", "")
		pingSuccess = True
		pingFailCount = 0

	if (message.topic == "resevoir/stop"):
		pingStarted = False
		pingFailCount = 0
		g_buttonsConnected = False
		print_status()

def main(argv):
	global oled_address, pingStarted, pingSuccess, pingFailCount, g_buttonsConnected
	oled_address = int(argv[1])
	get_ip_address()
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
			if (pingStarted == True):
				if (pingSuccess == True):
					pingSuccess = False
				elif (pingSuccess == False):
					pingFailCount += 1
					if (pingFailCount > 5):
						turn_pump_off()
						g_buttonsConnected = False
						print_status()
						oledExp.setCursor(6, 0)
						oledExp.write("Ping Fault")
						pingStarted = False
						pingFailCount = 0


	except KeyboardInterrupt:
		print("exiting on ctrl-c")
		client.disconnect() #disconnect
		client.loop_stop() #stop loop
		g_buttonsConnected = False
		relayExp.setChannel(oled_address, 0, 0)
		relayExp.setChannel(oled_address, 1, 0)
		time.sleep(2)
		sys.exit(0)
	
if __name__ == "__main__":
	main(sys.argv)
