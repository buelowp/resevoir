/*
 * Project resevoir-button
 * Description:
 * Author:
 * Date:
 */
#include "MQTT.h"
#include "InternetButton.h"

#define APP_ID  10

void subCallback(char*, byte*, unsigned int);

MQTT client("172.24.1.10", 1883, subCallback);
InternetButton btn = InternetButton();
bool g_connected;
bool g_pumpOn;
bool g_valveOpen;
unsigned long g_lockout;

void subCallback(char* t, byte* p, unsigned int length)
{
    String topic = String(t);

    if (topic == "control/pump/on") {
        btn.ledOn(3, 0, 100, 0);
        g_pumpOn = true;
    }
    if (topic == "control/pump/off") {
        btn.ledOn(3, 100, 0, 0);
        g_pumpOn = false;
    }
    if (topic == "control/valve/open") {
        btn.ledOn(9, 0, 100, 0);
        g_valveOpen = true;
    }
    if (topic == "control/valve/close") {
        btn.ledOn(9, 100, 0, 0);
        g_valveOpen = false;
    }
    if (topic == "control/state") {
        g_pumpOn = false;
        g_valveOpen = false;
        btn.ledOn(3, 100, 0, 0);
        btn.ledOn(9, 100, 0, 0);
        if (p[0] == '1') {
            g_pumpOn = true;
            btn.ledOn(3, 0, 100, 0);
        }
        if (p[1] == '1') {
            g_valveOpen = true;
            btn.ledOn(9, 0, 100, 0);
        }
    }
}

// setup() runs once, when the device is first turned on.
void setup()
{
    int appId = APP_ID;

    g_connected = false;
    g_pumpOn = false;
    g_valveOpen = false;
    g_lockout = 0;

    Particle.variable("appid", appId);

    btn.begin();

    client.connect("buttons");
    if (client.isConnected()) {
        client.subscribe("control/#");
        client.publish("resevoir/state", "");
        btn.allLedsOn(0,100,0);
        delay(3000);
        btn.allLedsOff();
        g_connected = true;
    }
    else {
        btn.allLedsOn(100, 0, 0);
        g_connected = false;
    }
}

// loop() runs over and over again, as quickly as it can execute.
void loop()
{
    if (client.isConnected())
        client.loop();
    else {
        btn.allLedsOn(100, 0, 0);
    }

    if (g_lockout != 0) {
        if ((millis() - g_lockout) > 2000) {
            g_lockout = 0;
        }
        else {
            return;
        }
    }

    if (btn.buttonOn(2)) {
        g_lockout = millis();
        if (!g_pumpOn)
            client.publish("resevoir/pump/on", "");
        else
            client.publish("resevoir/pump/off", "");
    }
    if (btn.buttonOn(4)) {
        g_lockout = millis();
        if (!g_valveOpen)
            client.publish("resevoir/valve/open", "");
        else
            client.publish("resevoir/valve/close", "");
    }
}
