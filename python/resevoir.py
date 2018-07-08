import time
import paho.mqtt.client as paho
import sys
import socket
import onionGpio
from OmegaExpansion import oledExp, relayExp

broker = "172.24.1.10"
client = paho.Client("resevoir") 
g_relayAddress = 0
g_pingSuccess = False
g_pingStarted = False
g_pingFailCount = 0
g_buttonsConnected = False
g_ipAddr = ""
g_filterState = False
g_gpioHandler = onionGpio.OnionGpio(18)


def get_ip_address():
    global g_ipAddr
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    g_ipAddr = s.getsockname()[0]
    s.close()


# Turn the pump on, but only if the valve is open
# otherwise, just ignore the command
def turn_pump_on():
    print("Turning pump on")
    global g_relayAddress
    if relayExp.readChannel(g_relayAddress, 0) == 0:
        if relayExp.setChannel(g_relayAddress, 0, 1) == 0:
            client.publish("aquarium/pump/on")
    print_status()


# Turn the pump off, then tell the controller we did it
def turn_pump_off():
    print ("Turning pump off")
    global g_relayAddress
    if relayExp.setChannel(g_relayAddress, 0, 0) == 0:
        client.publish("aquarium/pump/off")
    print_status()


# Open the water valve. This just makes it possible to
# get the water out, it does not start the pump
def open_valve():
    print ("Opening valve")
    global g_relayAddress
    if relayExp.setChannel(g_relayAddress, 1, 1) == 0:
        client.publish("aquarium/valve/open")
    print_status()


# Close the valve
# If the pump is on, turn it off first
def close_valve():
    print ("Closing Valve")
    global g_relayAddress
    if relayExp.readChannel(g_relayAddress, 0) == 1:
        turn_pump_off()

    if relayExp.setChannel(g_relayAddress, 1, 1) == 0:
        client.publish("aquarium/valve/close")
    print_status()

def turn_filter_on():
    print ("Turning power strip on")
    value = g_gpioHandler.getValue()
    if (int)(value) == 0:
        g_gpioHandler.setValue(1)
        client.publish("aquarium/power/on")
    print_status()
        
 
def turn_filter_off():
    print ("Turning power strip off")
    value = g_gpioHandler.getValue()
    if (int)(value) == 1:
        g_gpioHandler.setValue(0)
        client.publish("aquarium/power/off")
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
    print_gpio_status()


def print_gpio_status():
    global g_gpioHandler
    oledExp.setCursor(6, 0)
    value = g_gpioHandler.getValue()
    if (int(value)) == 0:
        oledExp.write("Filter: off")
    else:
        oledExp.write("Filter: on")


def print_relay1_status():
    global g_relayAddress
    oledExp.setCursor(4, 0)
    if relayExp.readChannel(g_relayAddress, 0) == 0:
        oledExp.write("Pump  : off")
    else:
        oledExp.write("Pump  : on ")


def print_relay2_status():
    global g_relayAddress
    oledExp.setCursor(5, 0)
    if relayExp.readChannel(g_relayAddress, 1) == 0:
        oledExp.write("Valve : closed")
    else:
        oledExp.write("Valve : open  ")


def return_state():
    global g_pingStarted, g_pingFailCount, g_buttonsConnected, g_gpioHandler
    fields = 0;
    if relayExp.readChannel(g_relayAddress, 0) == 1:
        fields = 1 << 0
    if relayExp.readChannel(g_relayAddress, 1) == 1:
        fields = 1 << 1
    if g_gpioHandler.getValue() == 1:
        fields = 1 << 2
        
    relaystate = str(fields).encode('ascii')
    print("Sending state of " + relaystate)
    client.publish("aquarium/state", relaystate, 1, True)
    g_pingStarted = True
    g_buttonsConnected = True
 

def print_relay_status():
    global g_relayAddress
    bInit = relayExp.checkInit(g_relayAddress)
    oledExp.setCursor(3, 0)
    if bInit == 0:
        oledExp.write("Relay : Disabled")        
    else:
        oledExp.write("Relay : Available")        
        print_relay1_status()
        print_relay2_status()


def on_connect(c, ud, f, rc):
    print("Connected")
    print_status()


def on_disconnect(c, ud, rc):
    global g_relayAddress, g_buttonsConnected
    relayExp.setChannel(g_relayAddress, 0, 0)
    relayExp.setChannel(g_relayAddress, 1, 0)
    g_buttonsConnected = False
    print ("Disconnected")
    print_status()


def on_message(c, ud, message):
    global g_pingSuccess, g_pingFailCount, g_pingStarted, g_buttonsConnected
    print ("Message topic received "  + message.topic)
    if message.topic == "control/pump/on":
        turn_pump_on()

    if message.topic == "control/pump/off":
        turn_pump_off()

    if message.topic == "control/valve/open":
        open_valve()

    if message.topic == "control/valve/close":
        close_valve()

    if message.topic == "control/status":
        return_state()

    if message.topic == "control/power/on":
        turn_filter_on()
        
    if  message.topic == "control/power/off":
        turn_filter_off()
        
    if message.topic == "control/ping":
        client.publish("aquarium/pong", "")
        g_pingSuccess = True
        g_pingFailCount = 0

    if message.topic == "control/stop":
        print("Got a stop message")
        g_pingStarted = False
        g_pingFailCount = 0
        g_buttonsConnected = False
        print_status()


def main(argv):
    global g_relayAddress, g_pingStarted, g_pingSuccess, g_pingFailCount, g_buttonsConnected
    g_relayAddress = int(argv[1])
    get_ip_address()
    print("g_relayAddress is " + str(g_relayAddress))
    oledExp.driverInit()
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(broker)
    oledExp.setDisplayPower(1)
    relayExp.driverInit(g_relayAddress)
    g_gpioHandler.setOutputDirection(0)
 
    try:
        client.subscribe("control/#")
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
                        g_pingStarted = False
                        g_pingFailCount = 0


    except KeyboardInterrupt:
        print("exiting on ctrl-c")
        client.disconnect() #disconnect
        client.loop_stop() #stop loop
        g_buttonsConnected = False
        relayExp.setChannel(g_relayAddress, 0, 0)
        relayExp.setChannel(g_relayAddress, 1, 0)
        time.sleep(2)
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
