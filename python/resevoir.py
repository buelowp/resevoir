import time
import paho.mqtt.client as paho
import sys
import socket
import fcntl
import struct
from OmegaExpansion import oledExp, relayExp

broker = "172.24.1.10"
client = paho.Client("resevoir") 
g_oledAddress = 0
g_pingSuccess = False
g_pingStarted = False
g_pingFailCount = 0
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
    global g_oledAddress
    if relayExp.readChannel(g_oledAddress, 1) == 1:
        if relayExp.setChannel(g_oledAddress, 0, 1) == 0:
            client.publish("control/pump/on")

    print_status()


# Turn the pump off, then tell the controller we did it
def turn_pump_off():
    global g_oledAddress
    if relayExp.setChannel(g_oledAddress, 0, 0) == 0:
        client.publish("control/pump/off")
    print_status()


# Open the water valve. This just makes it possible to
# get the water out, it does not start the pump
def open_valve():
    global g_oledAddress
    if relayExp.setChannel(g_oledAddress, 1, 1) == 0:
        client.publish("control/valve/open")
    print_status()


# Close the valve
# If the pump is on, turn it off first
def close_valve():
    global g_oledAddress
    if relayExp.readChannel(g_oledAddress, 0) == 1:
        turn_pump_off()

    if relayExp.setChannel(g_oledAddress, 1, 0) == 0:
        client.publish("control/valve/close")
    print_status()


def print_status():
    global g_buttonsConnected, g_ipAddr
    oledExp.clear()
    oledExp.setCursor(0, 0)
    oledExp.write("Host  : " + g_ipAddr)
    oledExp.setCursor(1, 0)
    oledExp.write("Broker: " + broker)
    oledExp.setCursor(2, 0)
    if g_buttonsConnected:
        oledExp.write("Client: Connected")
    else:
        oledExp.write("                 ")

    print_relay_status()


def print_relay1_status():
    global g_oledAddress
    oledExp.setCursor(4, 0)
    if relayExp.readChannel(g_oledAddress, 0) == 0:
        oledExp.write("Pump  : off")
    else:
        oledExp.write("Pump  : on ")


def print_relay2_status():
    global g_oledAddress
    oledExp.setCursor(5, 0)
    if relayExp.readChannel(g_oledAddress, 1) == 0:
        oledExp.write("Valve : closed")
    else:
        oledExp.write("Valve : open  ")


def return_state():
    global g_pingStarted, g_pingFailCount, g_buttonsConnected
    relaystate = '00'
    if relayExp.readChannel(g_oledAddress, 0) == 1:
        relaystate[0] = '1'
    if relayExp.readChannel(g_oledAddress, 1) == 1:
        relaystate[1] = '1'

    client.publish("control/state", relaystate, 1, True)
    g_pingStarted = True
    g_buttonsConnected = True
    print_status()


def print_relay_status():
    global g_oledAddress
    bInit = relayExp.checkInit(g_oledAddress)
    oledExp.setCursor(3, 0)
    if bInit == 0:
        oledExp.write("Relay : Disabled")        
    else:
        oledExp.write("Relay : Available")        
        print_relay1_status()
        print_relay2_status()


def on_connect(c, ud, f, rc):
    print_status()


def on_disconnect(c, ud, rc):
    global g_oledAddress, g_buttonsConnected
    relayExp.setChannel(g_oledAddress, 0, 0)
    relayExp.setChannel(g_oledAddress, 1, 0)
    g_buttonsConnected = False
    print_status()


def on_message(c, ud, message):
    global g_pingSuccess, g_pingFailCount, g_pingStarted, g_buttonsConnected
    if message.topic == "resevoir/pump/on":
        turn_pump_on()

    if message.topic == "resevoir/pump/off":
        turn_pump_off()

    if message.topic == "resevoir/valve/open":
        open_valve()

    if message.topic == "resevoir/valve/close":
        close_valve()

    if message.topic == "resevoir/state":
        return_state()

    if message.topic == "resevoir/ping":
        client.publish("control/ping", "")
        g_pingSuccess = True
        g_pingFailCount = 0

    if message.topic == "resevoir/stop":
        g_pingStarted = False
        g_pingFailCount = 0
        g_buttonsConnected = False
        print_status()


def main(argv):
    global g_oledAddress, g_pingStarted, g_pingSuccess, g_pingFailCount, g_buttonsConnected
    g_oledAddress = int(argv[1])
    get_ip_address()
    print("g_oledAddress is " + str(g_oledAddress))
    oledExp.driverInit()
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker)
    oledExp.setDisplayPower(1)
    relayExp.driverInit(g_oledAddress)

    try:
        client.subscribe("resevoir/#")
        client.loop_start()
        while True:
            time.sleep(1);
            if g_pingStarted:
                if g_pingSuccess:
                    g_pingSuccess = False
                elif g_pingSuccess == False:
                    g_pingFailCount += 1
                    if g_pingFailCount > 5:
                        turn_pump_off()
                        g_buttonsConnected = False
                        print_status()
                        oledExp.setCursor(6, 0)
                        oledExp.write("Ping Fault")
                        g_pingStarted: bool = False
                        g_pingFailCount = 0


    except KeyboardInterrupt:
        print("exiting on ctrl-c")
        client.disconnect() #disconnect
        client.loop_stop() #stop loop
        g_buttonsConnected = False
        relayExp.setChannel(g_oledAddress, 0, 0)
        relayExp.setChannel(g_oledAddress, 1, 0)
        time.sleep(2)
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
