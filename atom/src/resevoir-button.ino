/*
 * Project resevoir-button
 * Description:
 * Author:
 * Date:
 */
#include "MQTT.h"
#include "InternetButton.h"
#include "FastLED.h"

#define APP_ID  18
FASTLED_USING_NAMESPACE;

void subCallback(char*, byte*, unsigned int);

MQTT client("172.24.1.10", 1883, subCallback);
InternetButton btn = InternetButton();
bool g_connected;
bool g_pumpOn;
bool g_valveOpen;
bool g_receivedPing;
bool g_relayOn;
unsigned long g_lockout;
int g_missedPingCount;
int g_lastState;
int g_lastLength;
int appId;

#define TEST_FILTER_ON   0x00000001
#define TEST_VALVE_ON    0x00000010
#define TEST_PUMP_ON     0x00000100

void subCallback(char* t, byte* p, unsigned int length)
{
    String topic = String(t);

    if (topic == "aquarium/pump/on") {
        btn.ledOn(3, 0, 255, 0);
        g_pumpOn = true;
    }
    if (topic == "aquarium/pump/off") {
        btn.ledOn(3, 255, 0, 0);
        g_pumpOn = false;
    }
    if (topic == "aquarium/valve/open") {
        btn.ledOn(6, 0, 255, 0);
        g_valveOpen = true;
    }
    if (topic == "aquarium/valve/close") {
        btn.ledOn(6, 255, 0, 0);
        g_valveOpen = false;
    }
    if (topic == "aquarium/filter/on") {
        btn.ledOn(9, 0, 255, 0);
        g_relayOn = true;
    }
    if (topic == "aquarium/filter/off") {
        btn.ledOn(98, 255, 0, 0);
        g_relayOn = false;
    }
    if (topic == "aquarium/state") {
        g_lastState = (int)(*p - 48);
        g_lastLength = length;
        if (g_lastState & TEST_FILTER_ON) {
            g_relayOn = true;
            btn.ledOn(3, 0, 255, 0);
        }
        else {
            g_relayOn = false;
            btn.ledOn(3, 255, 0, 0);
        }
        if (g_lastState & TEST_PUMP_ON) {
            g_pumpOn = true;
            btn.ledOn(6, 0, 255, 0);
        }
        else {
            g_pumpOn = false;
            btn.ledOn(6, 255, 0, 0);
        }
        if (g_lastState & TEST_VALVE_ON) {
            g_valveOpen = true;
            btn.ledOn(9, 0, 255, 0);
        }
        else {
            g_valveOpen = false;
            btn.ledOn(9, 255, 0, 0);
        }
    }
    if (topic == "aquarium/pong") {
        if (g_missedPingCount > 10) {
            btn.allLedsOff();
            client.publish("control/status", "");
        }
        btn.ledOn(1, 0, 100, 100);
        g_receivedPing = true;
        g_missedPingCount = 0;
    }
}

void sendPing()
{
    client.publish("control/ping", "");
}

// setup() runs once, when the device is first turned on.
void setup()
{
    Serial.begin(115200);
    appId = APP_ID;

    g_connected = false;
    g_pumpOn = false;
    g_valveOpen = false;
    g_receivedPing = false;
    g_relayOn - false;
    g_lockout = 0;
    g_missedPingCount = 0;
    g_lastState = 0;

    Particle.variable("appid", appId);
    Particle.variable("MissedPing", g_missedPingCount);
    Particle.variable("lastState", g_lastState);
    Particle.variable("lastLength", g_lastLength);

    btn.begin();

    client.connect("buttons");
    if (client.isConnected()) {
        client.subscribe("aquarium/#");
        btn.allLedsOn(0,100,0);
        delay(3000);
        btn.allLedsOff();
        g_connected = true;
        btn.ledOn(11, 100, 100, 100);
    }
    else {
        btn.allLedsOn(100, 0, 0);
        g_connected = false;
    }

    client.publish("control/status", "");
}

// loop() runs over and over again, as quickly as it can execute.
void loop()
{
    if (client.isConnected()) {
        btn.ledOn(11, 100, 100, 100);
        EVERY_N_MILLISECONDS(1000) {
            sendPing();
            if (!g_receivedPing) {
                g_missedPingCount++;
            }
            if (g_receivedPing)
                g_receivedPing = false;
        }
        client.loop();
    }
    else {
        btn.allLedsOn(100, 0, 0);
        return;
    }

    if (g_lockout != 0) {
        if ((millis() - g_lockout) > 2000) {
            g_lockout = 0;
        }
        else {
            return;
        }
    }

    if (g_missedPingCount > 10) {
        btn.allLedsOn(100, 0, 0);
        return;
    }

    if (btn.buttonOn(1)) {
        g_lockout = millis();
        if (g_relayOn)
            client.publish("control/filter/off", "");
        else
            client.publish("control/filter/on", "");
    }
    if (btn.buttonOn(2)) {
        g_lockout = millis();
        if (g_pumpOn)
            client.publish("control/pump/off", "");
        else
            client.publish("control/pump/on", "");
    }
    if (btn.buttonOn(3)) {
        g_lockout = millis();
        if (g_valveOpen)
            client.publish("control/valve/close", "");
        else
            client.publish("control/valve/open", "");
    }
}
