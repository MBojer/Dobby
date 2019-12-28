
// pdf with can table can be found here: https://123electric.eu/wp-content/uploads/2018/03/SmartBMS_Extended_manual_1.2.pdf

#include <Arduino.h>
#include <mcp_can.h>
#include <SPI.h>

// For some UNEXPLAINABLE reason it seems to be fucking dificulrt
// will skip the lib and code it by hand......!
// #include <ArduinoJson.h>


// it seems that we need to reset the device once in a while, if not the values becomes not correct
// will do it after 300 reads aka 2.5 horus at 30 sec read interval
int Reboot_Counter = 300;

// MQTT
#include <ESP8266WiFi.h>
#include <Ticker.h>
#include <AsyncMqttClient.h>

#define WIFI_SSID "NoInternetHere"
#define WIFI_PASSWORD "NoPassword1!"

#define MQTT_HOST IPAddress(192, 168, 8, 2)
#define MQTT_PORT 1883
#define MQTT_USERNAME "DasBoot"
#define MQTT_PASSWORD "NoSinking"

String MQTT_Base_Topic = "/Boat/BMS/";


long unsigned int rxId;
unsigned char len = 0;
unsigned char rxBuf[8];

#define CAN0_INT D2                              // Set INT to pin 2
MCP_CAN CAN0(D8);                               // Set CS to pin 10

// Converted information from can network
int Battery_SOC;
float Total_Voltage;
float Current_In;
float Current_Out;
#define Cells_Number_Of 4
float Cell_Voltage[Cells_Number_Of];
int Cell_Temperature[Cells_Number_Of];

// Publish
#define Publish_Interval 30000
Ticker Publish_Timer;

// MQTT
AsyncMqttClient mqttClient;
Ticker mqttReconnectTimer;

WiFiEventHandler wifiConnectHandler;
WiFiEventHandler wifiDisconnectHandler;
Ticker wifiReconnectTimer;


void connectToWifi();
void onWifiConnect(const WiFiEventStationModeGotIP& event);
void onWifiDisconnect(const WiFiEventStationModeDisconnected& event);
void connectToMqtt();
void onMqttConnect(bool sessionPresent);
void onMqttDisconnect(AsyncMqttClientDisconnectReason reason);


// ############################################################ getRandomNumber() ############################################################
int getRandomNumber(int startNum, int endNum) {
	randomSeed(ESP.getCycleCount());
	return random(startNum, endNum);
} // getRandomNumber


void connectToWifi() {
  Serial.println("Connecting to Wi-Fi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
}

void onWifiConnect(const WiFiEventStationModeGotIP& event) {
  Serial.println("Connected to Wi-Fi.");
  connectToMqtt();
}

void onWifiDisconnect(const WiFiEventStationModeDisconnected& event) {
  Serial.println("Disconnected from Wi-Fi.");
  mqttReconnectTimer.detach(); // ensure we don't reconnect to MQTT while reconnecting to Wi-Fi
  wifiReconnectTimer.once(2, connectToWifi);
}

void connectToMqtt() {
  Serial.println("Connecting to MQTT...");
  mqttClient.connect();
}

void onMqttConnect(bool sessionPresent) {
  Serial.println("Connected to MQTT.");
}

void onMqttDisconnect(AsyncMqttClientDisconnectReason reason) {
  Serial.println("Disconnected from MQTT.");

  if (WiFi.isConnected()) {
    mqttReconnectTimer.once(2, connectToMqtt);
  }
}


float Big_Endian_To_Float(uint8_t Hight, uint8_t Low, bool Signed)
{
  int result = Hight;
  result = (result << 8) | Low;
  if (Signed == true)
  {
    return (int16_t)result;
  }
  else
  {
    return (uint16_t)result;
  }
}

float Big_Endian_32_To_Float(uint8_t Byte_0, uint8_t Byte_1, uint8_t Byte_2, uint8_t Byte_3, bool Signed)
{
  int result = Byte_0;
  result = (result << 8) | Byte_1;
  result = (result << 16) | Byte_2;
  result = (result << 24) | Byte_3;
  if (Signed == true)
  {
    return (int32_t)result;
  }
  else
  {
    return (uint32_t)result;
  }
}


void Publish() {
  // Print to serial
  Serial.println("Total Voltage: " + String(Total_Voltage));
  Serial.println("Battery SOC: " + String(Battery_SOC));
  Serial.println("Current: " + String(Current_In - Current_Out));
  Serial.println("Current In: " + String(Current_In));
  Serial.println("Current Out: " + String(Current_Out));

  for (byte i = 0; i < Cells_Number_Of; i++)
  {
    Serial.println("Cell Number: " + String(i + 1));
    Serial.println("  Cell Voltage: " + String(Cell_Voltage[i]));
    Serial.println("  Cell Temperature: " + String(Cell_Temperature[i]));
  }
  // Publish to mqtt
  if (mqttClient.connected() == true)
  {
    mqttClient.publish(String(MQTT_Base_Topic + "Battery/Voltage").c_str(), 0, true, String(Total_Voltage).c_str());
    mqttClient.publish(String(MQTT_Base_Topic + "Battery/SOC").c_str(), 0, true, String(Battery_SOC).c_str());
    mqttClient.publish(String(MQTT_Base_Topic + "Battery/Current/In").c_str(), 0, true, String(Current_In).c_str());
    mqttClient.publish(String(MQTT_Base_Topic + "Battery/Current/Out").c_str(), 0, true, String(Current_Out).c_str());
    mqttClient.publish(String(MQTT_Base_Topic + "Battery/Current").c_str(), 0, true, String(Current_In - Current_Out).c_str());
  }

  // Build json for cells

  String Cell_String;
  
  Cell_String = Cell_String + "{";
  // {
  for (byte i = 0; i < Cells_Number_Of; i++)
  {
    Cell_String = Cell_String + "\"" + String(i + 1) + "\": {";
    Cell_String = Cell_String + "\"Voltage\": " + String(Cell_Voltage[i]);
    Cell_String = Cell_String + ", \"Temperature\": " + String(Cell_Temperature[i]);
    if (i != 3)
    {
      Cell_String = Cell_String + "}, ";
    }
    else {
      Cell_String = Cell_String + "}";
    }
    
  }
  Cell_String = Cell_String + "}";

  mqttClient.publish(String(MQTT_Base_Topic + "Cells").c_str(), 0, true, Cell_String.c_str());



  // Subtract one from reboot counter
  Reboot_Counter = Reboot_Counter - 1;
  
  if (Reboot_Counter < 0) {
    Serial.println("Reset..");

    // Disconnect from mqtt so we can connect again after reboot
    mqttClient.disconnect();

    // reset the device
    ESP.restart();
  }



}


void setup()
{
  Serial.begin(115200);
  Serial.println();
  Serial.println();
  Serial.println("Booting 123smartBMS to MQTT");
  
  // Initialize MCP2515 running at 16MHz with a baudrate of 500kb/s and the masks and filters disabled.
  if(CAN0.begin(MCP_ANY, CAN_125KBPS, MCP_16MHZ) == CAN_OK)
    Serial.println("MCP2515 Initialized Successfully!");
  else {
    Serial.println("Error Initializing MCP2515...");

    // Well we are fucked if we cant get the cant module to work
    while (true)
    {
      delay(1337);
    }
  }
  
  CAN0.setMode(MCP_NORMAL);                     // Set operation mode to normal so the MCP2515 sends acks to received data.

  pinMode(CAN0_INT, INPUT_PULLUP);                            // Configuring pin for /INT input
  
  wifiConnectHandler = WiFi.onStationModeGotIP(onWifiConnect);
  wifiDisconnectHandler = WiFi.onStationModeDisconnected(onWifiDisconnect);

  mqttClient.onConnect(onMqttConnect);
  mqttClient.onDisconnect(onMqttDisconnect);
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCredentials(MQTT_USERNAME, MQTT_PASSWORD);
  
  // String MQTT_Hostname = "BMS-" + String(getRandomNumber(10000, 19999));
	// MQTT_Client.setClientId(MQTT_Hostname.c_str());

  // Start the publish ticker
  Publish_Timer.attach_ms(Publish_Interval, Publish);

  connectToWifi();
}

void loop()
{
  if(!digitalRead(CAN0_INT))                         // If CAN0_INT pin is low, read receive buffer
  {
    CAN0.readMsgBuf(&rxId, &len, rxBuf);      // Read data: len = data length, buf = data byte(s)
    
    // Store bms info - Current/Voltage info
    if (rxId == 0)
    {
      Total_Voltage = Big_Endian_To_Float(rxBuf[0], rxBuf[1], false) * 0.1;
      Current_In = Big_Endian_To_Float(rxBuf[2], rxBuf[3], true) * 0.1;
      Current_Out = Big_Endian_To_Float(rxBuf[4], rxBuf[5], true) * 0.1;
    }
    // Save cell info - SOC
    // We only need soc and its one byte
    // so we can just set the var directly
    else if (rxId == 1) Battery_SOC = rxBuf[6];
    
    // Save cell info
    else if (rxId == 7)
    {
      Cell_Voltage[rxBuf[3] - 1] = Big_Endian_To_Float(rxBuf[0], rxBuf[1], true) * 0.001;
      Cell_Temperature[rxBuf[3] - 1] = rxBuf[2];
    }
  }

}