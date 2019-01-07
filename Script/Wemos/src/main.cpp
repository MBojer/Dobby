// Licence:
// Releaed under The GNU General Public License v3.0

// Change log:
// See ChangeLog.txt

// Bug list:
// See BugList.txt


#include <Arduino.h>
extern "C" {
  #include "user_interface.h"
}

// ---------------------------------------- Dobby ----------------------------------------
#define Version 101061
// First didget = Software type 1-Production 2-Beta 3-Alpha
// Secound and third didget = Major version number
// Fourth to sixth = Minor version number


String Hostname = "NotConfigured";
String System_Header = "";
String System_Sub_Header = "";
String Config_ID = "0";

// ------------------------------------------------------------ Misc ------------------------------------------------------------
bool Wire_Avtive = false;

// For smoothing
#include <RunningAverage.h>

bool Boot_Compleate = false;


// -------------------------------- -------- ArduinoOTA_Setup() ----------------------------------------
bool ArduinoOTA_Active = false;


// ---------------------------------------- FS() ----------------------------------------
#include "FS.h"


// ------------------------------------------------------------ WiFi ------------------------------------------------------------
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <Ticker.h>

WiFiClient WiFi_Client;

WiFiEventHandler gotIpEventHandler;
WiFiEventHandler disconnectedEventHandler;

String WiFi_SSID = "";
String WiFi_Password = "";

Ticker wifiReconnectTimer;
#define WiFi_Reconnect_Delay 5000
byte Wifi_State = 0;
// States:
// 0 = Just started not commection attempt maid
// 1 = Connected
// 2 = Disconnected
// 3 = Reconnecting


// ------------------------------------------------------------ FS_Config ------------------------------------------------------------
#include <ArduinoJson.h>

#define Config_Json_Max_Buffer_Size 1024
bool Config_json_Loaded = false;

#define FS_Confing_File_Name "/Dobby.json"

// ------------------------------------------------------------ MQTT ------------------------------------------------------------
#include <AsyncMqttClient.h>

AsyncMqttClient MQTT_Client;
Ticker mqttReconnectTimer;

String MQTT_Broker = "0.0.0.0";
String MQTT_Port = "1883";

String MQTT_Username = "";
String MQTT_Password = "";

String MQTT_Allow_Flash_Password = "60d15n074p455w0rdu53dby4dm1n5";

Ticker MQTT_KeepAlive_Ticker;
unsigned long MQTT_KeepAlive_Interval = 60000;

#define NONE 0
#define PLUS 1
#define HASH 2

#define Topic_Settings 0
#define Topic_Commands 1
#define Topic_All 2
#define Topic_KeepAlive 3
#define Topic_Buzzer 4
#define Topic_DHT 5
#define Topic_Relay 6
#define Topic_Distance 7
#define Topic_Dimmer 8
#define Topic_Log_Error 9
#define Topic_Button 10
#define Topic_Dobby 11
#define Topic_System 12
#define Topic_Config 13
#define Topic_LoadCell 14
#define Topic_DC_Voltmeter 15
#define Topic_Ammeter 16
#define Topic_Switch 17
#define Topic_MPU6050 18
#define Topic_BMP180 19
#define Topic_Log_Warning 20
#define Topic_MQ2 21
#define Topic_Log_Fatal 22
#define Topic_Log_Info 23
#define Topic_Log_Debug 24
#define Topic_RFID 25
#define Topic_PIR 26
#define Topic_LDR 27

#define Topic_Settings_Text "/Settings/"
#define Topic_Config_Text "/Config/"
#define Topic_Commands_Text "/Commands/"
#define Topic_All_Text "/All"
#define Topic_KeepAlive_Text "/KeepAlive/"
#define Topic_Buzzer_Text "/Buzzer/"
#define Topic_DHT_Text "/DHT/"
#define Topic_Relay_Text "/Relay/"
#define Topic_Distance_Text "/Distance/"
#define Topic_Dimmer_Text "/Dimmer/"
#define Topic_Log_Error_Text "/Log/Error/"
#define Topic_Button_Text "/Button/"
#define Topic_Dobby_Text "/Commands/Dobby/"
#define Topic_System_Text "/System/"
#define Topic_LoadCell_Text "/LoadCell/"
#define Topic_DC_Voltmeter_Text "/DC_Voltmeter/"
#define Topic_Ammeter_Text "/Ammeter/"
#define Topic_Switch_Text "/Switch/"
#define Topic_MPU6050_Text "/MPU6050/"
#define Topic_BMP180_Text "/BMP180/"
#define Topic_Log_Warning_Text "/Log/Warning/"
#define Topic_MQ2_Text "/MQ2/"
#define Topic_Log_Fatal_Text "/Log/Fatal/"
#define Topic_Log_Info_Text "/Log/Info/"
#define Topic_Log_Debug_Text "/Log/Debug/"
#define Topic_RFID_Text "/RFID/"
#define Topic_PIR_Text "/PIR/"
#define Topic_LDR_Text "/LDR/"

const byte MQTT_Topic_Number_Of = 28;
String MQTT_Topic[MQTT_Topic_Number_Of] = {
  System_Header + Topic_Settings_Text + Hostname,
  System_Header + Topic_Config_Text + Hostname,
  System_Header + Topic_Commands_Text + Hostname,
  System_Header + Topic_All_Text,
  System_Header + Topic_KeepAlive_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Buzzer_Text + Hostname,
  System_Header + System_Sub_Header + Topic_DHT_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Relay_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Distance_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Dimmer_Text + Hostname,
  System_Header + Topic_Log_Error_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Button_Text + Hostname,
  System_Header + Topic_Dobby_Text,
  System_Header + Topic_System_Text + Hostname,
  System_Header + System_Sub_Header + Topic_LoadCell_Text + Hostname,
  System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Switch_Text + Hostname,
  System_Header + System_Sub_Header + Topic_MPU6050_Text + Hostname,
  System_Header + System_Sub_Header + Topic_BMP180_Text + Hostname,
  System_Header + Topic_Log_Warning_Text + Hostname,
  System_Header + System_Sub_Header + Topic_MQ2_Text + Hostname,
  System_Header + Topic_Log_Fatal_Text + Hostname,
  System_Header + Topic_Log_Info_Text + Hostname,
  System_Header + Topic_Log_Debug_Text + Hostname,
  System_Header + Topic_RFID_Text + Hostname,
  System_Header + Topic_PIR_Text + Hostname,
  System_Header + Topic_LDR_Text + Hostname,
};

bool MQTT_Topic_Subscribe_Active[MQTT_Topic_Number_Of] = {
  false,
  true,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  true,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
  false,
};
byte MQTT_Topic_Subscribe_Subtopic[MQTT_Topic_Number_Of] = {
  HASH,
  HASH,
  NONE,
  NONE,
  NONE,
  PLUS,
  PLUS,
  PLUS,
  PLUS,
  NONE,
  NONE,
  NONE,
  NONE,
  NONE,
  PLUS,
  NONE,
  NONE,
  PLUS,
  PLUS,
  NONE,
  NONE,
  NONE,
  NONE,
  PLUS,
  NONE,
};

bool MQTT_Subscribtion_Active[MQTT_Topic_Number_Of];

#define MQTT_Reconnect_Delay 5 // in secounds

#define MQTT_Boot_Wait_For_Connection 15000

bool MQTT_Config_Requested = false;


// ------------------------------------------------------------ MQTT_Allow_Flash() ------------------------------------------------------------
Ticker MQTT_Allow_Flash_Ticker;
bool Allow_Flash = false;

unsigned long MQTT_Allow_Flash_Delay = 30000;


// ------------------------------------------------------------ ESP_Reboot() ------------------------------------------------------------
Ticker ESP_Power_Ticker;


// ------------------------------------------------------------ Buzzer ------------------------------------------------------------
bool Buzzer_Configured;
byte Buzzer_Pins;
Ticker Buzzer_Ticker;
String Buzzer_Melody;


// ------------------------------------------------------------ DHT ------------------------------------------------------------
#include <SimpleDHT.h>
SimpleDHT22 dht22;

bool DHT_Configured;

#define DHT_Max_Number_Of 6
byte DHT_Pins[DHT_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

unsigned long DHT_Last_Read = 0;            // When the sensor was last read

Ticker DHT_Ticker;

// Do not put this below 2000ms it will make the DHT22 give errors
#define DHT_Refresh_Rate 2500
float DHT_Current_Value_Humidity[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};
float DHT_Current_Value_Temperature[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};
float DHT_Min_Value_Humidity[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};
float DHT_Min_Value_Temperature[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};
float DHT_Max_Value_Humidity[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};
float DHT_Max_Value_Temperature[DHT_Max_Number_Of] = {-1337, -1337, -1337, -1337, -1337, -1337};

#define DHT_Distable_At_Error_Count 10
byte DHT_Error_Counter[DHT_Max_Number_Of] = {0, 0, 0, 0, 0, 0};

// ------------------------------------------------------------ Relay ------------------------------------------------------------
#define Relay_Max_Number_Of 6

bool Relay_Configured = false;

bool Relay_On_State = false;

byte Relay_Pins[Relay_Max_Number_Of] = {255, 255, 255, 255, 255, 255};
bool Relay_Pin_Auto_Off[Relay_Max_Number_Of];
unsigned long Relay_Pin_Auto_Off_Delay[Relay_Max_Number_Of] = {0, 0, 0, 0, 0, 0};

#define OFF 0
#define ON 1
#define FLIP 2


// ------------------------------------------------------------ Relay Auto Off ------------------------------------------------------------
unsigned long Relay_Auto_OFF_At[Relay_Max_Number_Of];
bool Relay_Auto_OFF_Active[Relay_Max_Number_Of];


// ------------------------------------------------------------ Distance ------------------------------------------------------------
#define Distance_Max_Number_Of 3

bool Distance_Configured = false;
byte Distance_Pins_Echo[Distance_Max_Number_Of] = {255, 255, 255};
byte Distance_Pins_Trigger[Distance_Max_Number_Of] = {255, 255, 255};

int Distance_Trigger_At[Distance_Max_Number_Of];

String Distance_Target_ON[Distance_Max_Number_Of];
String Distance_Target_OFF[Distance_Max_Number_Of];

unsigned long Distance_Refresh_Rate[Distance_Max_Number_Of];

Ticker Distance_Refresh_Ticker;

bool Distance_Sensor_State[Distance_Max_Number_Of];

unsigned long Distance_Auto_OFF_At[Distance_Max_Number_Of] = {0, 0, 0};
unsigned long Distance_Auto_OFF_Delay[Distance_Max_Number_Of];
bool Distance_Auto_OFF_Active[Distance_Max_Number_Of];

unsigned long Distnace_Sensor_Read_At[Distance_Max_Number_Of] = {0, 0, 0};

// New
#define Distance_Read_Rate 100
#define Distance_RunningAverage_Length 25
RunningAverage Distance_RA_1(Distance_RunningAverage_Length);
RunningAverage Distance_RA_2(Distance_RunningAverage_Length);
RunningAverage Distance_RA_3(Distance_RunningAverage_Length);
float Distance_Last_Reading[Distance_Max_Number_Of];
byte Distance_Error_Count[Distance_Max_Number_Of];


// ------------------------------------------------------------ Dimmer ------------------------------------------------------------
#define Dimmer_Max_Number_Of 6
bool Dimmer_Configured = false;
byte Dimmer_Pins[Dimmer_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

int Dimmer_State[Dimmer_Max_Number_Of];
byte Dimmer_Procent[Dimmer_Max_Number_Of];

byte Dimmer_Fade_Jump = 20;
byte Dimmer_Fade_Jump_Delay = 40;


// ------------------------------------------------------------ Pin_Monitor ------------------------------------------------------------
// 0 = In Use
#define Pin_In_Use 0
#define Pin_Free 1
#define Pin_SCL 2
#define Pin_SDA 3
#define Pin_Error 255
// Action
#define Reserve_Normal 0
#define Reserve_I2C_SCL 1
#define Reserve_I2C_SDA 2
#define Check_State 3

#define Pin_Monitor_Pins_Number_Of 10
String Pin_Monitor_Pins_Names[Pin_Monitor_Pins_Number_Of] = {"D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "A0"};
byte Pin_Monitor_Pins_List[Pin_Monitor_Pins_Number_Of] = {D0, D1, D2, D3, D4, D5, D6, D7, D8, A0};

byte Pin_Monitor_Pins_Active[Pin_Monitor_Pins_Number_Of] = {1, 1, 1, 1, 1, 1, 1, 1, 1, 1};

String Pin_Monitor_State_Text[4] = {"In Use", "Free", "I2C SCL", "I2C SDA"};



// ------------------------------------------------------------ Button ------------------------------------------------------------
#define Button_Max_Number_Of 6
bool Button_Configured = false;
byte Button_Pins[Button_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

unsigned long Button_Ignore_Input_Untill[Button_Max_Number_Of];
unsigned int Button_Ignore_Input_For = 750; // Time in ms before a butten can triggered again

String Button_Target[Button_Max_Number_Of];


// ------------------------------------------------------------ Indicator_LED() ------------------------------------------------------------
bool Indicator_LED_Configured = true;

Ticker Indicator_LED_Blink_Ticker;
Ticker Indicator_LED_Blink_OFF_Ticker;

bool Indicator_LED_State = true;

unsigned int Indicator_LED_Blink_For = 150;

byte Indicator_LED_Blinks_Active = false;
byte Indicator_LED_Blinks_Left;

#define LED_Number_Of_States 5
#define LED_OFF 0
#define LED_MQTT 1
#define LED_WiFi 2
#define LED_Config 3
#define LED_PIR 4

float Indicator_LED_State_Hertz[LED_Number_Of_States] = {0, 0.5, 1, 2.5, 0.25};
bool Indicator_LED_State_Active[LED_Number_Of_States] = {true, false, false, false, false};


// ------------------------------------------------------------ Update() ------------------------------------------------------------
Ticker Update_Ticker;


// ------------------------------------------------------------ CLI ------------------------------------------------------------
#define Command_List_Length 21
const char* Commands_List[Command_List_Length] = {
  "hostname",
  "wifi ssid",
  "wifi password",
  "mqtt broker",
  "mqtt port",
  "mqtt user",
  "mqtt password",
  "system header",
  "system sub header",
  "list",
  "json",
  "fs list",
  "fs cat",
  "fs format",
  "fs config load",
  "fs config drop",
  "show mac",
  "save",
  "check",
  "reboot",
  "shutdown"};

String CLI_Input_String;
bool CLI_Command_Complate = false;

#define Serial_CLI_Boot_Message_Timeout 3


// ------------------------------------------------------------ Load Cell ------------------------------------------------------------
// #include "HX711.h"
//
// #define Load_Cell_Max_Number_Of 4
// byte LoadCell_Pins_DT[Load_Cell_Max_Number_Of] = {255, 255, 255, 255};
// byte LoadCell_Pins_SCK[Load_Cell_Max_Number_Of] = {255, 255, 255, 255};
//
// HX711 Load_Cell1;
// HX711 Load_Cell2;
// HX711 Load_Cell3;
// HX711 Load_Cell4;
//
// float LoadCell_Calibration[Load_Cell_Max_Number_Of] = {-1337, -1337, -1337, -1337};
//
// bool Load_Cell_Configurated[Load_Cell_Max_Number_Of] = {false, false, false, false};
// bool Load_Cell_Tare_Done[Load_Cell_Max_Number_Of] = {false, false, false, false};
//
// #define LoadCell_RunningAverage_Length 25
// RunningAverage LoadCell_RA_Current1(LoadCell_RunningAverage_Length);
// RunningAverage LoadCell_RA_Current2(LoadCell_RunningAverage_Length);
// RunningAverage LoadCell_RA_Current3(LoadCell_RunningAverage_Length);
// RunningAverage LoadCell_RA_Current4(LoadCell_RunningAverage_Length);
//
// #define LoadCell_Read_Rate 250
// Ticker LoadCell_Refresh_Ticker;

// ------------------------------------------------------------ DC Voltmeter ------------------------------------------------------------
byte DC_Voltmeter_Pins = 255;
float DC_Voltmeter_R1 = 0.0; // 30000.0
float DC_Voltmeter_R2 = 0.0; // 7500.0
float DC_Voltmeter_Curcit_Voltage = 0.0; // 3.3
float DC_Voltmeter_Offset = 0.0;


// ------------------------------------------------------------ Switch ------------------------------------------------------------
bool Switch_Configured = false;

#define Switch_Max_Number_Of 6
byte Switch_Pins[Switch_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

unsigned long Switch_Ignore_Input_Untill;
unsigned long Switch_Refresh_Rate = 250; // ms between checking switch state

bool Switch_Last_State[Switch_Max_Number_Of];

String Switch_Target_ON[Switch_Max_Number_Of];
String Switch_Target_OFF[Switch_Max_Number_Of];


// // ------------------------------------------------------------ MPU6050 ------------------------------------------------------------
// #include "I2Cdev.h"
// #include "Wire.h"
//
// #include "MPU6050_6Axis_MotionApps20.h"
//
// MPU6050 mpu;
//
// byte MPU6050_Pin_SCL = 255;
// byte MPU6050_Pin_SDA = 255;
// byte MPU6050_Pin_Interrupt = 255;
//
// bool MPU6050_Configured = false;
//
// // MPU control/status vars
// bool MPU6050_BMP_Ready = false;  // set true if DMP init was successful
// uint8_t MPU6050_Interrupt_Status;   // holds actual interrupt status byte from MPU
// uint8_t MPU6050_Device_Status;      // return status after each device operation (0 = success, !0 = error)
// uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
// uint16_t fifoCount;     // count of all bytes currently in FIFO
// uint8_t fifoBuffer[1024]; // FIFO storage buffer
//
// // orientation/motion vars
// Quaternion MPU6050_Quaternion;           // [w, x, y, z]         quaternion container
// VectorInt16 MPU6050_Accelerometer;         // [x, y, z]            accel sensor measurements
// VectorInt16 MPU6050_Accelerometer_Real;     // [x, y, z]            gravity-free accel sensor measurements
// VectorInt16 MPU6050_Accelerometer_World;    // [x, y, z]            world-frame accel sensor measurements
// VectorFloat MPU6050_Gravity;    // [x, y, z]            gravity vector
//
// // For Interrupt
// volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high
//
// float MPU6050_Quaternion_W_Min = 1337;
// float MPU6050_Quaternion_W_Max = 1337;
// float MPU6050_Quaternion_X_Min = 1337;
// float MPU6050_Quaternion_X_Max = 1337;
// float MPU6050_Quaternion_Y_Min = 1337;
// float MPU6050_Quaternion_Y_Max = 1337;
// float MPU6050_Quaternion_Z_Min = 1337;
// float MPU6050_Quaternion_Z_Max = 1337;

// ------------------------------------------------------------ BMP180 ------------------------------------------------------------
// URL: https://github.com/adafruit/Adafruit-BMP085-Library
#include <Adafruit_BMP085.h>
#include <Wire.h>

bool BMP180_Configured = false;

Adafruit_BMP085 BMP;

byte BMP180_Pin_SCL = 255;
byte BMP180_Pin_SDA = 255;

float BMP180_Altitude = -1337.0;

#define BMP180_RunningAverage_Length 254
RunningAverage BMP180_RA_Current_Pressure(BMP180_RunningAverage_Length);


// ------------------------------------------------------------ PIR ------------------------------------------------------------
bool PIR_Configured = false;

#define PIR_Max_Number_Of 6
#define PIR_State_Number_Of 3
// State 0 = Disabeled

byte PIR_Pins[PIR_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

String PIR_Topic[PIR_Max_Number_Of];
String PIR_OFF_Payload[PIR_Max_Number_Of];
String PIR_ON_Payload[PIR_State_Number_Of][PIR_Max_Number_Of];

int PIR_OFF_Delay[PIR_Max_Number_Of]; // in sec
unsigned long PIR_OFF_At[PIR_Max_Number_Of];

bool PIR_ON_Send[PIR_Max_Number_Of];

// ON = Light
bool PIR_LDR_ON[PIR_Max_Number_Of];

bool PIR_Disabled[PIR_Max_Number_Of];

byte PIR_Selected_Level[PIR_Max_Number_Of] = {1, 1, 1, 1, 1, 1};




// ------------------------------------------------------------ Log() ------------------------------------------------------------
// http://github.com/MBojer/MB_Queue
#include <MB_Queue.h>
// FIX - Might need to add support for log full handling
#define Log_Max_Queue_Size 100
MB_Queue Log_Queue_Topic(Log_Max_Queue_Size);
MB_Queue Log_Queue_Log_Text(Log_Max_Queue_Size);


// ------------------------------------------------------------ MQ2 ------------------------------------------------------------
bool MQ2_Configured = false;

byte MQ2_Pin_A0 = 255;

int MQ2_Current_Value = -1;
int MQ2_Value_Min = -1;
int MQ2_Value_Max = -1;


Ticker MQ2_Ticker;
#define MQ2_Refresh_Rate 100


// // ------------------------------------------------------------ MFRC522 - RFID ------------------------------------------------------------
// #include "MFRC522.h"
// #include <SPI.h>
//
// bool MFRC522_Configured = false;
//
// #define MFRC522_Max_Number_Of 5
// byte MFRC522_Pins[Switch_Max_Number_Of] = {255, 255, 255, 255, 255};
// #define MFRC522_Pin_RST 0
// #define MFRC522_Pin_SS 1
// #define MFRC522_Pin_MOSI 2
// #define MFRC522_Pin_MIOS 3
// #define MFRC522_Pin_SCK 4
//
// MFRC522 MFRC522_RFID(MFRC522_Pins[1], MFRC522_Pins[0]);	// Create MFRC522 instance


// ------------------------------------------------------------ LDR - Light Dependent Resistor ------------------------------------------------------------
bool LDR_Configured = false;

byte LDR_Pin_A0 = 255;

int LDR_Current_Value = -1;
int LDR_Value_Min = -1;
int LDR_Value_Max = -1;

byte LDR_Dead_Band = 10;

Ticker LDR_Ticker;
#define LDR_Refresh_Rate 100

int LDR_Dark_At = -1;

bool LDR_State = false;
// false = no light
// true = light

String LDR_Target_Topic;


// ############################################################ String_To_IP() ############################################################
IPAddress String_To_IP(String IP_String) {

  for (byte y = 0; y < 2; y++) {
    if (IP_String.indexOf(".") == -1) {
      Serial.println("Invalid ip entered");
      return IPAddress(0, 0, 0, 0);
    }
  }

  byte IP_Part[4];

  byte Dot_Location_Start = 0;
  byte Dot_Location_End = IP_String.indexOf(".");
  IP_Part[0] = IP_String.substring(Dot_Location_Start, Dot_Location_End).toInt();

  Dot_Location_Start = Dot_Location_End + 1;
  Dot_Location_End = IP_String.indexOf(".", Dot_Location_Start);
  IP_Part[1] = IP_String.substring(Dot_Location_Start, Dot_Location_End).toInt();

  Dot_Location_Start = Dot_Location_End + 1;
  Dot_Location_End = IP_String.indexOf(".", Dot_Location_Start);
  IP_Part[2] = IP_String.substring(Dot_Location_Start, Dot_Location_End).toInt();

  Dot_Location_Start = Dot_Location_End + 1;
  IP_Part[3] = IP_String.substring(Dot_Location_Start).toInt();

  for (byte i = 0; i < 4; i++) {
    if (IP_Part[i] > 255) {
      Serial.println("Invalid ip entered");
      return IPAddress(0, 0, 0, 0);
    }
  }

  return IPAddress(IP_Part[0], IP_Part[1], IP_Part[2], IP_Part[3]);
}


// ############################################################ High_Low_String() ############################################################
void Rebuild_MQTT_Topics() {
  MQTT_Topic[Topic_Settings] = System_Header + Topic_Settings_Text + Hostname;
  MQTT_Topic[Topic_Config] = System_Header + Topic_Config_Text + Hostname;
  MQTT_Topic[Topic_Commands] = System_Header + Topic_Commands_Text + Hostname;
  MQTT_Topic[Topic_All] = System_Header + Topic_All_Text;
  MQTT_Topic[Topic_KeepAlive] = System_Header + Topic_KeepAlive_Text + Hostname;
  MQTT_Topic[Topic_Buzzer] = System_Header + System_Sub_Header + Topic_Buzzer_Text + Hostname;
  MQTT_Topic[Topic_DHT] = System_Header + System_Sub_Header + Topic_DHT_Text + Hostname;
  MQTT_Topic[Topic_Relay] = System_Header + System_Sub_Header + Topic_Relay_Text + Hostname;
  MQTT_Topic[Topic_Distance] = System_Header + System_Sub_Header + Topic_Distance_Text + Hostname;
  MQTT_Topic[Topic_Dimmer] = System_Header + System_Sub_Header + Topic_Dimmer_Text + Hostname;
  MQTT_Topic[Topic_Log_Error] = System_Header + Topic_Log_Error_Text + Hostname;
  MQTT_Topic[Topic_Button] = System_Header + System_Sub_Header + Topic_Button_Text + Hostname;
  MQTT_Topic[Topic_Dobby] = System_Header + Topic_Dobby_Text;
  MQTT_Topic[Topic_System] = System_Header + Topic_System_Text + Hostname;
  MQTT_Topic[Topic_LoadCell] = System_Header + System_Sub_Header + Topic_LoadCell_Text + Hostname;
  MQTT_Topic[Topic_DC_Voltmeter] = System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname;
  MQTT_Topic[Topic_Ammeter] = System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname;
  MQTT_Topic[Topic_Switch] = System_Header + System_Sub_Header + Topic_Switch_Text + Hostname;
  MQTT_Topic[Topic_MPU6050] = System_Header + System_Sub_Header + Topic_MPU6050_Text + Hostname;
  MQTT_Topic[Topic_BMP180] = System_Header + System_Sub_Header + Topic_BMP180_Text + Hostname;
  MQTT_Topic[Topic_Log_Warning] = System_Header + Topic_Log_Warning_Text + Hostname;
  MQTT_Topic[Topic_MQ2] = System_Header + System_Sub_Header + Topic_MQ2_Text + Hostname;
  MQTT_Topic[Topic_RFID] = System_Header + System_Sub_Header + Topic_RFID_Text + Hostname;
  MQTT_Topic[Topic_PIR] = System_Header + System_Sub_Header + Topic_PIR_Text + Hostname;
  MQTT_Topic[Topic_LDR] = System_Header + System_Sub_Header + Topic_LDR_Text + Hostname;
}


// ############################################################ High_Low_String() ############################################################
// Returns "HIGH" of 1 and "LOW" if 0
String High_Low_String(int Input) {
  if (Input == 1) return "HIGH";
  else return "LOW";
} // High_Low_String()


// ############################################################ Log() ############################################################
// Writes text to MQTT and Serial
void Log(String Topic, String Log_Text) {

  // Online/Offline check
  // Online
  if (MQTT_Client.connected() == true) {

    // Print log queue
    if (Log_Queue_Topic.Length() > 0) {
      // Send offline being marker
      MQTT_Client.publish(String(MQTT_Topic[Topic_System] + "/Log").c_str(), 0, false, "Offline log begin");
      while (Log_Queue_Topic.Length() > 0) {
        // State message post as retained message
        if (Log_Queue_Topic.Peek().indexOf("/State") != -1) {
          MQTT_Client.publish(Log_Queue_Topic.Pop().c_str(), 0, true, Log_Queue_Log_Text.Pop().c_str());
        }
        // Post as none retained message
        MQTT_Client.publish(Log_Queue_Topic.Pop().c_str(), 0, false, Log_Queue_Log_Text.Pop().c_str());
      }
      // Send offline end marker
      MQTT_Client.publish(String(MQTT_Topic[Topic_System] + "/Log").c_str(), 0, false, "Offline log end");
    }

    // State message post as retained message
    if (Topic.indexOf("/State") != -1) {
      MQTT_Client.publish(Topic.c_str(), 0, true, Log_Text.c_str());
    }
    // Post as none retained message
    else MQTT_Client.publish(Topic.c_str(), 0, false, Log_Text.c_str());
  }

  // Offline
  else {
    // Add to log queue
    Log_Queue_Topic.Push(Topic);
    Log_Queue_Log_Text.Push(Log_Text);
  }

  Serial.println(Topic + " - " + Log_Text);

} // Log()

void Log(String Topic, int Log_Text) {
  Log(Topic, String(Log_Text));
} // Log - Reference only

void Log(String Topic, float Log_Text) {
  Log(Topic, String(Log_Text));
} // Log - Reference only


// ############################################################ Show_Commands() ############################################################
// Writes text to MQTT and Serial
void Show_Commands() {

// FIX ADD ME

} // Show_Commands()

// ############################################################ IPtoString() ############################################################
String IPtoString(IPAddress IP_Address) {

  String Temp_String = String(IP_Address[0]) + "." + String(IP_Address[1]) + "." + String(IP_Address[2]) + "." + String(IP_Address[3]);

  return Temp_String;

} // IPtoString


// ############################################################ IP_Show() ############################################################
// Post the devices IP information
void IP_Show() {

  String IP_String;

  IP_String = "IP Address: " + IPtoString(WiFi.localIP());
  IP_String = IP_String + " Subnetmask: " + IPtoString(WiFi.subnetMask());
  IP_String = IP_String + " Gateway: " + IPtoString(WiFi.gatewayIP());
  IP_String = IP_String + " DNS Server: " + IPtoString(WiFi.dnsIP());
  IP_String = IP_String + " MAC Address: " + WiFi.macAddress();

  Log(MQTT_Topic[Topic_System] + "/IP", IP_String);
} // IP_Show()


// ############################################################ WiFi_Signal() ############################################################
// Post the devices WiFi Signal Strength
void WiFi_Signal() {

  Log(MQTT_Topic[Topic_System] + "/WiFi", "Signal Strength: " + String(WiFi.RSSI()));

} // WiFi_Signal()


// ############################################################ Setting_String() ############################################################
// Writes text to MQTT and Serial
String Setting_String(String Read_String, String Search_String) {

  int BeginIndex = Read_String.indexOf(Search_String);
  BeginIndex = BeginIndex + Search_String.length();

  if (Read_String.indexOf(Search_String) != -1) {
    return Read_String.substring(BeginIndex, Read_String.indexOf("\r\n", BeginIndex));
  }

  return "";
}


// ############################################################ Indicator_LED_Blink_OFF() ############################################################
void Indicator_LED_Blink_OFF () {
  // On Wemos High = Low ... ?
  digitalWrite(D4, HIGH);

  if (Indicator_LED_Blinks_Active == true) {
    if (Indicator_LED_Blinks_Left == 0) {
      Indicator_LED_Blinks_Active = false;
      Indicator_LED_Blink_Ticker.detach();
    }
    else Indicator_LED_Blinks_Left--;
  }
}

// ############################################################ Indicator_LED_Blink() ############################################################
void Indicator_LED_Blink() {

  digitalWrite(D4, LOW); // think is has to be low to be ON
  Indicator_LED_Blink_OFF_Ticker.once_ms(Indicator_LED_Blink_For, Indicator_LED_Blink_OFF);

} // Indicator_LED_Blink()


// ############################################################ Indicator_LED_Blink() ############################################################
void Indicator_LED_Blink(byte Number_Of_Blinks) {

  if (Indicator_LED_Configured == false) {
    Log(MQTT_Topic[Topic_Log_Warning] + "/IndicatorLED", "Indicator LED not configured");
  }

  Log(MQTT_Topic[Topic_System] + "/IndicatorLED", "Blinking " + String(Number_Of_Blinks) + " times");

  Indicator_LED_Blinks_Active = true;
  Indicator_LED_Blinks_Left = Number_Of_Blinks - 1;

  Indicator_LED_Blink(); // for instant reaction then attach the ticket below
  Indicator_LED_Blink_Ticker.attach(1, Indicator_LED_Blink);

} // Indicator_LED_Blink()


/* ############################################################ Indicator_LED() ############################################################
      Blinkes the blue onboard led based on the herts specified in a float
      NOTE: Enabling this will disable pind D4
      0 = Turn OFF
*/

void Indicator_LED(byte LED_State, bool Change_To) {

  if (Indicator_LED_Configured == false) {
    Log(MQTT_Topic[Topic_Log_Warning] + "/IndicatorLED", "Indicator LED not configured");
    return;
  }

  // Set state
  Indicator_LED_State_Active[LED_State] = Change_To;

  // Of another state and LED_OFF is set to true set LED_OFF to false to enable the LED
  if (LED_State != 0 && Change_To == true) {
    Indicator_LED_State_Active[LED_OFF] = false;
  }

  bool State_Active = false;

  // Set indication
  for (byte i = 0; i < LED_Number_Of_States; i++) {
    if (Indicator_LED_State_Active[i] == true) {
      if (i != 0) {
        // Start blinking at first herts to let the most "important" state come first
        Indicator_LED_Blink_Ticker.attach(Indicator_LED_State_Hertz[LED_State], Indicator_LED_Blink);
        State_Active = true;
        // Break the loop to only trigger the first active state
        break;
      }
    }
  }
  // Check if any other then LED_OFF is active if not set LED_OFF to true and disabled blink
  if (State_Active == false) {
    Indicator_LED_State_Active[LED_OFF] = true;
  }

  // Check if led OFF is true
  if (Indicator_LED_State_Active[LED_OFF] == true) {
    // Stop blinking
    Indicator_LED_Blink_Ticker.detach();
    // Turn off LED
    // NOTE: HIGH = OFF
    digitalWrite(D4, HIGH);
  }
} // Indicator_LED()


// ############################################################ MFRC522_Loop() ############################################################
// void MFRC522_Loop() {
//   if (MFRC522_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
//     return;
//   }
//
//   bool test = MFRC522_RFID.PICC_IsNewCardPresent();
//   Serial.println(test);
//   delay(150);
//
//   // Check if new card is present
//   if (MFRC522_RFID.PICC_IsNewCardPresent() == true) {
//     Serial.println("MARKER"); // rm
//     // read card info
//     MFRC522_RFID.PICC_ReadCardSerial();
//     Serial.print(F("Card UID:"));
//
//
//     for (byte i = 0; i < MFRC522_RFID.uid.size; i++) {
//       Serial.print(MFRC522_RFID.uid.uidByte[i] < 0x10 ? " 0" : " ");
//       Serial.print(MFRC522_RFID.uid.uidByte[i], HEX);
//     }
//
//     Serial.println();
//   }
// }


// ############################################################ LDR_Loop() ############################################################
void LDR_Loop() {

  // Do nothing if its not configured
  if (LDR_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false || MQTT_Client.connected() == false) {
    return;
  }

  // // Set currernt value
  LDR_Current_Value = analogRead(LDR_Pin_A0);
  // // Check min/max
  LDR_Value_Min = min(LDR_Current_Value, LDR_Value_Min);
  LDR_Value_Max = max(LDR_Current_Value, LDR_Value_Max);;

  // Check if Dobby PIR Name is set
  if (LDR_Target_Topic != "") {
    // 1024 = dark
    // 0 = light
    bool LDR_New_State = false;
    // Check if ligh level is below of above the trigger
    if (LDR_Dark_At == -1) {
      Log(MQTT_Topic[Topic_Log_Error] + "/LDR", "Disabling LDR, never got a reading from the sensor");
      LDR_Configured = false;
    }
    // Higher than = on
    else if (LDR_Current_Value < LDR_Dark_At && LDR_New_State == false) {
      LDR_New_State = true;
    }
    // else if (LDR_Current_Value - LDR_Dead_Band < LDR_Dark_At) {
    //   // Do nothing withing dead band
    // }
    else {
      LDR_New_State = false;
    }

    // LDR State check
    if (LDR_New_State != LDR_State) {
      LDR_State = LDR_New_State;
      // Publish state to Dobby PIR
      MQTT_Client.publish(LDR_Target_Topic.c_str(), 0, false, String("LDR " + String(LDR_State) + ";").c_str());
    }

  }

}  // LDR_Loop()


// ############################################################ LDR() ############################################################
bool LDR(String Topic, String Payload) {

  // Do nothing if its not configured
  if (LDR_Configured == false) {
    return false;
  }

  // If Values = -1 no readings resived form sensor so disabling it
  else if (LDR_Current_Value == -1) {
    // Disable sensor
    LDR_Configured = false;
    // Log Error
    Log(MQTT_Topic[Topic_Log_Error] + "/LDR", "Never got a readings from the sensor disabling it.");
    // Detatch ticket
    LDR_Ticker.detach();
    // Return
    return false;
  }

  // Check topic
  else if (Topic == MQTT_Topic[Topic_LDR]) {

    // Trim Payload from garbage chars
    Payload = Payload.substring(0, Payload.indexOf(";"));

    // State request
    if (Payload == "?") {
      Log(MQTT_Topic[Topic_LDR] + "/State", String(LDR_Current_Value));
      return true;
    }
    // Min/Max request
    else if (Payload == "json") {

      // Create json buffer
      DynamicJsonBuffer jsonBuffer(80);
      JsonObject& root_LDR = jsonBuffer.createObject();

      // encode json string
      root_LDR.set("Current", LDR_Current_Value);
      root_LDR.set("Min", LDR_Value_Min);
      root_LDR.set("Max", LDR_Value_Max);

      // Reset values
      LDR_Value_Min = LDR_Current_Value;
      LDR_Value_Max = LDR_Current_Value;

      String LDR_String;

      root_LDR.printTo(LDR_String);

      Log(MQTT_Topic[Topic_LDR] + "/json/State", LDR_String);

      return true;
    }
  }

  return false;

} // LDR


// ############################################################ MQ2_Loop() ############################################################
void MQ2_Loop() {

  // Do nothing if its not configured
  if (MQ2_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
    return;
  }

  // // Set currernt value
  MQ2_Current_Value = analogRead(MQ2_Pin_A0);
  // // Check min/max
  MQ2_Value_Min = min(MQ2_Current_Value, MQ2_Value_Min);
  MQ2_Value_Max = max(MQ2_Current_Value, MQ2_Value_Max);;


}  // MQ2_Loop()


// ############################################################ MQ2() ############################################################
bool MQ2(String Topic, String Payload) {

  // Do nothing if its not configured
  if (MQ2_Configured == false) {
    return false;
  }

  // If Values = -1 no readings resived form sensor so disabling it
  else if (MQ2_Current_Value == -1) {
    // Disable sensor
    MQ2_Configured = false;
    // Log Error
    Log(MQTT_Topic[Topic_Log_Error] + "/MQ2", "Never got a readings from the sensor disabling it.");
    // Detatch ticket
    MQ2_Ticker.detach();
    // Return
    return false;
  }

  // Check topic
  else if (Topic == MQTT_Topic[Topic_MQ2]) {

    // Trim Payload from garbage chars
    Payload = Payload.substring(0, Payload.indexOf(";"));

    // State request
    if (Payload == "?") {
      Log(MQTT_Topic[Topic_MQ2] + "/State", String(MQ2_Current_Value));
      return true;
    }
    // Min/Max request
    else if (Payload == "json") {

      // Create json buffer
      DynamicJsonBuffer jsonBuffer(80);
      JsonObject& root_MQ2 = jsonBuffer.createObject();

      // encode json string
      root_MQ2.set("Current", MQ2_Current_Value);
      root_MQ2.set("Min", MQ2_Value_Min);
      root_MQ2.set("Max", MQ2_Value_Max);

      // Reset values
      MQ2_Value_Min = MQ2_Current_Value;
      MQ2_Value_Max = MQ2_Current_Value;

      String MQ2_String;

      root_MQ2.printTo(MQ2_String);

      Log(MQTT_Topic[Topic_MQ2] + "/json/State", MQ2_String);

      return true;
    }
  }

  return false;

} // MQ2


// ############################################################ BMP180_Loop() ############################################################
bool BMP180_Loop() {

  if (BMP180_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
    return false;
  }

  // FIX - check if runnng averidge is full and add the averidge to the list to not just get the averidge of the last 3 sec if you read every 5 min
  BMP180_RA_Current_Pressure.addValue(BMP.readPressure());
  return true;
}

// ############################################################ BMP180_Show() ############################################################
bool BMP180_Show(String Topic, String Payload) {

  if (BMP180_Configured == false) {
    return false;
  }

  // Check topic
  else if (Topic == MQTT_Topic[Topic_BMP180]) {

    if (Payload.length() > 1) Payload = Payload.substring(0, 1); // "Trim" length to avoid some wird error

    // State request
    if (Payload == "?") {
      // Pressure - Current
      Log(MQTT_Topic[Topic_BMP180] + "/Pressure", String(BMP180_RA_Current_Pressure.getAverage()));
      // Pressure - Sea Level NOTE: Calculated- based on BMP180_Altitude
      // FIX - Add support for updated altitude based on GPS location
      Log(MQTT_Topic[Topic_BMP180] + "/PressureSeaLevel", String((int32_t)(BMP180_RA_Current_Pressure.getAverage() / pow(1.0 - BMP180_Altitude / 44330, 5.255))));
      // FEATURE - Add support for calculating altitude based on sealevel presure read from the internet somwwwhare

      return true;
    }
  }


  return false;


}


// // ############################################################ MPU6050_Interrupt() ############################################################
// void ICACHE_RAM_ATTR MPU6050_BMP_DataReady() {
//     mpuInterrupt = true;
// }

// ############################################################ MPU6050_Loop() ############################################################
// void MPU6050_Loop() {
//   // if programming failed, don't try to do anything
//   if (MPU6050_BMP_Ready == false || MPU6050_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
//       return;
//   }
//
//   // To prevent a eternal loop crash
//   int i = 0;
//
//   // wait for MPU interrupt or extra packet(s) available
//   while (!mpuInterrupt && fifoCount < packetSize && i > 50) {
//       // other program behavior stuff here
//       // .
//       // .
//       // .
//       // if you are really paranoid you can frequently test in between other
//       // stuff to see if mpuInterrupt is true, and if so, "break;" from the
//       // while() loop to immediately process the MPU data
//       // .
//       // .
//       // .
//       i = i + 1;
//   }
//
//   if (i >= 49) {
//     // FIX - Add some usefull error message here
//     Serial.println("50 MARKER");
//   }
//
//   // reset interrupt flag and get INT_STATUS byte
//   mpuInterrupt = false;
//   MPU6050_Interrupt_Status = mpu.getIntStatus();
//
//   // get current FIFO count
//   fifoCount = mpu.getFIFOCount();
//
//   // check for overflow (this should never happen unless our code is too inefficient)
//   // if ((MPU6050_Interrupt_Status & 0x10) || fifoCount == 1024) {  // Original
//   if ((MPU6050_Interrupt_Status & 0x10) || fifoCount == 16384) {
//       // reset so we can continue cleanly
//       mpu.resetFIFO();
//
//       Log(MQTT_Topic[Topic_Log_Warning] + "/MPU6050", "FIFO overflow");
//
//   // otherwise, check for DMP data ready interrupt (this should happen frequently)
//   } else if (MPU6050_Interrupt_Status & 0x02) {
//       // wait for correct available data length, should be a VERY short wait
//       while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();
//
//       // read a packet from FIFO
//       mpu.getFIFOBytes(fifoBuffer, packetSize);
//
//       // track FIFO count here in case there is > 1 packet available
//       // (this lets us immediately read more without waiting for an interrupt)
//       fifoCount -= packetSize;
//
//       // Get gyro
//       mpu.dmpGetQuaternion(&MPU6050_Quaternion, fifoBuffer);
//
//       // Save Min/Max
//       // Check if init value or not
//       // init value
//       if (MPU6050_Quaternion_W_Min == 1337) {
//         MPU6050_Quaternion_W_Min = MPU6050_Quaternion.w;
//         MPU6050_Quaternion_W_Max = MPU6050_Quaternion.w;
//         MPU6050_Quaternion_X_Min = MPU6050_Quaternion.x;
//         MPU6050_Quaternion_X_Max = MPU6050_Quaternion.x;
//         MPU6050_Quaternion_Y_Min = MPU6050_Quaternion.y;
//         MPU6050_Quaternion_Y_Max = MPU6050_Quaternion.y;
//         MPU6050_Quaternion_Z_Min = MPU6050_Quaternion.z;
//         MPU6050_Quaternion_Z_Max = MPU6050_Quaternion.z;
//       }
//       // None init value
//       else {
//         MPU6050_Quaternion_W_Min = min(MPU6050_Quaternion_W_Min, MPU6050_Quaternion.w);
//         MPU6050_Quaternion_W_Max = max(MPU6050_Quaternion_W_Max, MPU6050_Quaternion.w);
//         MPU6050_Quaternion_X_Min = min(MPU6050_Quaternion_X_Min, MPU6050_Quaternion.x);
//         MPU6050_Quaternion_X_Max = max(MPU6050_Quaternion_X_Max, MPU6050_Quaternion.x);
//         MPU6050_Quaternion_Y_Min = min(MPU6050_Quaternion_Y_Min, MPU6050_Quaternion.y);
//         MPU6050_Quaternion_Y_Max = max(MPU6050_Quaternion_Y_Max, MPU6050_Quaternion.y);
//         MPU6050_Quaternion_Z_Min = min(MPU6050_Quaternion_Z_Min, MPU6050_Quaternion.z);
//         MPU6050_Quaternion_Z_Max = max(MPU6050_Quaternion_Z_Max, MPU6050_Quaternion.z);
//       }
//
//
//
//       // Get Accelerometer
//       mpu.dmpGetAccel(&MPU6050_Accelerometer, fifoBuffer);
//       mpu.dmpGetGravity(&MPU6050_Gravity, &MPU6050_Quaternion);
//       mpu.dmpGetLinearAccel(&MPU6050_Accelerometer_Real, &MPU6050_Accelerometer, &MPU6050_Gravity);
//       mpu.dmpGetLinearAccelInWorld(&MPU6050_Accelerometer_World, &MPU6050_Accelerometer_Real, &MPU6050_Quaternion);
//   }
// }


// ############################################################ MPU6050_Read_Gyro() ############################################################
// void MPU6050_Read_Gyro() {
//
//   if (MPU6050_Configured == false) {
//     return;
//   }
//
//   Log(MQTT_Topic[Topic_MPU6050] + "/Gyro/W/State", MPU6050_Quaternion.w);
//   Log(MQTT_Topic[Topic_MPU6050] + "/Gyro/X/State", MPU6050_Quaternion.x);
//   Log(MQTT_Topic[Topic_MPU6050] + "/Gyro/Y/State", MPU6050_Quaternion.y);
//   Log(MQTT_Topic[Topic_MPU6050] + "/Gyro/Z/State", MPU6050_Quaternion.z);
// }
//
// // ############################################################ MPU6050_Read_json() ############################################################
// void MPU6050_Read_Gyro_json() {
//
//   if (MPU6050_Configured == false) {
//     return;
//   }
//
//   // Create json buffer
//   DynamicJsonBuffer jsonBuffer(350);
//   JsonObject& root_Gyro = jsonBuffer.createObject();
//
//   // encode json string
//   root_Gyro.set("W", MPU6050_Quaternion.w);
//   root_Gyro.set("W_Min", MPU6050_Quaternion_W_Min);
//   root_Gyro.set("W_Max", MPU6050_Quaternion_W_Max);
//   root_Gyro.set("X", MPU6050_Quaternion.x);
//   root_Gyro.set("X_Min", MPU6050_Quaternion_X_Min);
//   root_Gyro.set("X_Max", MPU6050_Quaternion_X_Max);
//   root_Gyro.set("Y", MPU6050_Quaternion.y);
//   root_Gyro.set("Y_Min", MPU6050_Quaternion_Y_Min);
//   root_Gyro.set("Y_Max", MPU6050_Quaternion_Y_Max);
//   root_Gyro.set("Z", MPU6050_Quaternion.z);
//   root_Gyro.set("Z_Min", MPU6050_Quaternion_Z_Min);
//   root_Gyro.set("Z_Max", MPU6050_Quaternion_Z_Max);
//
//   // Reset values
//   MPU6050_Quaternion_W_Min = MPU6050_Quaternion.w;
//   MPU6050_Quaternion_W_Max = MPU6050_Quaternion.w;
//   MPU6050_Quaternion_X_Min = MPU6050_Quaternion.x;
//   MPU6050_Quaternion_X_Max = MPU6050_Quaternion.x;
//   MPU6050_Quaternion_Y_Min = MPU6050_Quaternion.y;
//   MPU6050_Quaternion_Y_Max = MPU6050_Quaternion.y;
//   MPU6050_Quaternion_Z_Min = MPU6050_Quaternion.z;
//   MPU6050_Quaternion_Z_Max = MPU6050_Quaternion.z;
//
//   String Gyro_String;
//
//   root_Gyro.printTo(Gyro_String);
//
//   Log(MQTT_Topic[Topic_MPU6050] + "/Gyro/json/State", Gyro_String);
//
// }

// ############################################################ MPU6050_Accelerometer_Max() ############################################################
// Logs and resets the Max/Min +/- values
// void MPU6050_Accelerometer_Max() {
  // // Log values
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/X/State/Minus", String(MPU6050_Accelerometer_X_Min + MPU6050_Accelerometer_X_Reset));
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/X/State/Plus", String(MPU6050_Accelerometer_X_Max - MPU6050_Accelerometer_X_Reset));
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/Y/State/Minus", String(MPU6050_Accelerometer_Y_Min + MPU6050_Accelerometer_Y_Reset));
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/Y/State/Plus", String(MPU6050_Accelerometer_Y_Max - MPU6050_Accelerometer_Y_Reset));
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/Z/State/Minus", String(MPU6050_Accelerometer_Z_Min + MPU6050_Accelerometer_Z_Reset));
  // Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/Z/State/Plus", String(MPU6050_Accelerometer_Z_Max - MPU6050_Accelerometer_Z_Reset));
  //
  // // Reset values
  // MPU6050_Accelerometer_X_Reset = MPU6050_AcX;
  // MPU6050_Accelerometer_Y_Reset = MPU6050_AcY;
  // MPU6050_Accelerometer_Z_Reset = MPU6050_AcZ;
  //
  // MPU6050_Accelerometer_X_Min = MPU6050_AcX;
  // MPU6050_Accelerometer_X_Max = MPU6050_AcX;
  // MPU6050_Accelerometer_Y_Min = MPU6050_AcY;
  // MPU6050_Accelerometer_Y_Max = MPU6050_AcY;
  // MPU6050_Accelerometer_Z_Min = MPU6050_AcZ;
  // MPU6050_Accelerometer_Z_Max = MPU6050_AcZ;
// }


// ############################################################ MPU6050_Read_Accelerometer() ############################################################
// Logs and resets the Max/Min +/- values
// void MPU6050_Read_Accelerometer() {
//   // // Log values
//   Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/X/State", String(MPU6050_Accelerometer_World.x));
//   Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/X/State", String(MPU6050_Accelerometer_World.y));
//   Log(MQTT_Topic[Topic_MPU6050] + "/Accelerometer/Y/State", String(MPU6050_Accelerometer_World.z));
//
// }


// ############################################################ MPU6050() ############################################################
// bool MPU6050(String Topic, String Payload) {
//
//   if (MPU6050_Configured == false) {
//     return false;
//   }
//
//   // Trim Topic
//   Topic.replace(MQTT_Topic[Topic_MPU6050] + "/", "");
//
//   // Trim Payload from garbage chars
//   Payload = Payload.substring(0, Payload.indexOf(";"));
//
//   // Check topic - Gyro
//   if (Topic == "Gyro" && Payload == "?") {
//     MPU6050_Read_Gyro();
//   }
//
//   if (Topic == "Gyro" && Payload == "json") {
//     MPU6050_Read_Gyro_json();
//   }
//
//   // Check topic - Accelerometer
//   else if (Topic == "Accelerometer" && Payload == "?") {
//     MPU6050_Read_Accelerometer();
//   }
//
//   // Check topic - Accelerometer Max
//   else if (Topic == "AccelerometerMax" && Payload == "?") {
//     MPU6050_Accelerometer_Max();
//   }
//
//
//   return false;
// }


// ############################################################ Button_Pressed_Check() ############################################################
byte Button_Pressed_Check() {
  for (byte i = 0; i < Button_Max_Number_Of; i++) {
    if (Button_Pins[i] != 255) {
      if (Button_Ignore_Input_Untill[i] < millis()) {
        if (digitalRead(Button_Pins[i]) == LOW) {
          Log(MQTT_Topic[Topic_Button] + "/" + String(i + 1), "Pressed");
          Button_Ignore_Input_Untill[i] = millis() + Button_Ignore_Input_For;
          return i;
        }
      }
    }
  }
  return 254;
} // Button_Pressed_Check()

// ############################################################ Button_Loop() ############################################################
bool Button_Loop() {

  if (Button_Configured == true || ArduinoOTA_Active == true || Boot_Compleate == false) {

    byte Button_Pressed = Button_Pressed_Check();

    if (Button_Pressed == 254 || Button_Pressed == 255) {
      // 255 = Unconfigured Pin
      // 254 = No button pressed
      return false;
    }

    if (Button_Pressed < Button_Max_Number_Of) {

      String Topic = Button_Target[Button_Pressed].substring(0, Button_Target[Button_Pressed].indexOf("&"));
      String Payload = Button_Target[Button_Pressed].substring(Button_Target[Button_Pressed].indexOf("&") + 1, Button_Target[Button_Pressed].length());

      MQTT_Client.publish(Topic.c_str(), 0, false, Payload.c_str());

      return true;
    }
  }

  return false;

} // Button_Loop


// ############################################################ Switch() ############################################################
bool Switch(String Topic, String Payload) {

  if (Switch_Configured == false) {
    return false;
  }

  // Check topic
  else if (Topic.indexOf(MQTT_Topic[Topic_Switch]) != -1) {


    if (Payload.length() > 1) Payload = Payload.substring(0, 1); // "Trim" length to avoid some wird error

    String Switch_String = Topic;
    Switch_String.replace(MQTT_Topic[Topic_Switch] + "/", "");

    byte Selected_Switch = Switch_String.toInt();

    // Ignore all requests thats larger then _Switch_Max_Number_Of
    if (Selected_Switch < Switch_Max_Number_Of) {
      // State request
      if (Payload == "?") {
        String State_String;
        // 0 = ON
        if (digitalRead(Switch_Pins[Selected_Switch - 1]) == 0) State_String += "1";
        else State_String += "0";
        Log(MQTT_Topic[Topic_Switch] + "/" + String(Selected_Switch) + "/State", State_String);
        return true;
      }
    }
  }

  return false;
}

// ############################################################ Switch_Loop() ############################################################
bool Switch_Loop() {

  // Check if switches is configured
  if (Switch_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
    return false;
  }

  // Check if its time to refresh
  if (Switch_Ignore_Input_Untill < millis()) {

    // The Wemos seems to reset if hammered during boot so dont read for the fist 7500 sec
    if (millis() < 7500) {
      return false;
    }

    bool Switch_State;

    for (byte i = 0; i < Switch_Max_Number_Of; i++) {
      // If pin in use
      if (Switch_Pins[i] != 255) {
        // Check if state chenged
        Switch_State = digitalRead(Switch_Pins[i]);

        if (Switch_State != Switch_Last_State[i]) {

          // Set last state
          Switch_Last_State[i] = Switch_State;

          String Topic;
          String Payload;

          // Publish switch state - Flipping output to make it add up tp 1 = ON
          Log(MQTT_Topic[Topic_Switch] + "/" + String(i + 1) + "/State", !Switch_State);

          // OFF
          if (Switch_State == 1) {
            Topic = Switch_Target_OFF[i].substring(0, Switch_Target_OFF[i].indexOf("&"));
            Payload = Switch_Target_OFF[i].substring(Switch_Target_OFF[i].indexOf("&") + 1, Switch_Target_OFF[i].length());

          }
          // ON
          else {
            Topic = Switch_Target_ON[i].substring(0, Switch_Target_ON[i].indexOf("&"));
            Payload = Switch_Target_ON[i].substring(Switch_Target_ON[i].indexOf("&") + 1, Switch_Target_ON[i].length());
          }
          // Publish target message
          MQTT_Client.publish(Topic.c_str(), 0, false, Payload.c_str());

        }
      }
    }
    Switch_Ignore_Input_Untill = millis() + Switch_Refresh_Rate;
  }

  return true;
} // Switch_Loop()


// ############################################################ Pin_Monitor_String() ############################################################
// Will return false if pin is in use or invalid
String Number_To_Pin(byte Pin_Number) {

  if (Pin_Number == 16) return "D0";
  else if (Pin_Number == 5) return "D1";
  else if (Pin_Number == 4) return "D2";
  else if (Pin_Number == 0) return "D3";
  else if (Pin_Number == 2) return "D4";
  else if (Pin_Number == 14) return "D5";
  else if (Pin_Number == 12) return "D6";
  else if (Pin_Number == 13) return "D7";
  else if (Pin_Number == 15) return "D8";
  else if (Pin_Number == 17) return "A0";
  else if (Pin_Number == 255) return "Unconfigured";
  else return "Unknown Pin";

} // Pin_Monitor_String()


byte Pin_To_Number(String Pin_Name) {

  if (Pin_Name == "D0") return 16;
  else if (Pin_Name == "D1") return 5;
  else if (Pin_Name == "D2") return 4;
  else if (Pin_Name == "D3") return 0;
  else if (Pin_Name == "D4") return 2;
  else if (Pin_Name == "D5") return 14;
  else if (Pin_Name == "D6") return 12;
  else if (Pin_Name == "D7") return 13;
  else if (Pin_Name == "D8") return 15;
  else if (Pin_Name == "A0") return 17;
  else if (Pin_Name == "Unconfigured") return 255;
  else return 254;

} // Pin_Monitor_String()


// ############################################################ Pin_Monitor(Reserve_Normal, ) ############################################################
// Will return false if pin is in use or invalid
byte Pin_Monitor(byte Action, byte Pin_Number) {
  // 0 = In Use
  // 1 = Free
  // 2 = Free / In Use - I2C - SCL
  // 3 = Free / In Use - I2C - SDA
  // 255 = Error
  // #define Pin_In_Use 0
  // #define Pin_Free 1
  // #define Pin_SCL 2
  // #define Pin_SDA 3
  // #define Pin_Error 255

  // Pin_Number
  // 0 = Reserve - Normal Pin
  // 1 = Reserve - I2C SCL
  // 2 = Reserve - I2C SDA
  // 3 = State
  // #define Reserve_Normal 0
  // #define Reserve_I2C_SCL 1
  // #define Reserve_I2C_SDA 2
  // #define Check_State 3


  // Check if pin has been set
  if (Pin_Number == 255) {
    Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Pin not set");
    return Pin_Error;
  }


  // Check if pin has been set
  // Pin_to_Number returns 254 if unknown pin name
  if (Pin_Number == 254) {
    Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Unknown Pin Name given");
    return Pin_Error;
  }


  // Find seleced Pin
  byte Selected_Pin = 255;
  for (byte i = 0; i < Pin_Monitor_Pins_Number_Of; i++) {
    if (Pin_Number == Pin_Monitor_Pins_List[i]) {
      Selected_Pin = i;
      break;
    }
  }

  // Known pin check
  if (Selected_Pin == 255) {
    Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Pin number: " + String(Pin_Number) + " Pin Name: " + Number_To_Pin(Pin_Number) + " not on pin list");
    return Pin_Error;
  }

  // Reserve a normal pin
  if (Action == Reserve_Normal) {
    // Check if pin is free
    // Pin is free
    if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_Free) {
      // Reserve pin
      Pin_Monitor_Pins_Active[Selected_Pin] = Pin_In_Use;
      // Log event
      Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");

      // Disable indicator led if pin D4 is used
      if (Number_To_Pin(Pin_Number) == "D4") {
        Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin D4 used, disabling indicator LED");

        // Detatch the tickers
        Indicator_LED_Blink_Ticker.detach();
        Indicator_LED_Blink_OFF_Ticker.detach();
        // Set port low for good mesure, and yes high is low
        digitalWrite(D4, HIGH);
        // Disable indicator LED
        Indicator_LED_Configured = false;
      }

      // Return Pin Free
      return Pin_Free;
    }
    // Pin is use return what it is used by
    else {
      // Log event
      Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is in use");
      // Return state
      return Pin_Monitor_Pins_Active[Selected_Pin];
    }
  }

  // Reserve a I2C SCL Pin
  else if (Action == Reserve_I2C_SCL) {
    // Pin is free
    if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_Free) {
      // Reserve pin
      Pin_Monitor_Pins_Active[Selected_Pin] = Pin_SCL;
      // Log event
      Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");
      // Return state
      return Pin_SCL;
    }
    // Pin already used as I2C SCL
    else if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_SCL) {
      // Log event
      Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " already used as I2C SCL");
      // Return state
      return Pin_SCL;
    }
    // Pin is in use
    else {
      // Log event
      Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is in use");
      // Return state
      return Pin_Monitor_Pins_Active[Selected_Pin];
    }
  }

  // Reserve a I2C SDA Pin
  else if (Action == Reserve_I2C_SDA) {
    // Pin is free
    if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_Free) {
      // Reserve pin
      Pin_Monitor_Pins_Active[Selected_Pin] = Pin_SDA;
      // Log event
      Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");
      // Return state
      return Pin_SDA;
    }
    // Pin already used as I2C SDA
    else if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_SDA) {
      // Log event
      Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " already used as I2C SDA");
      // Return state
      return Pin_SDA;
    }
    // Pin is in use
    else {
      // Log event
      Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is in use");
      // Return state
      return Pin_Monitor_Pins_Active[Selected_Pin];
    }
  }

  // Check pin current state
  else if (Action == Check_State) {
    return Pin_Monitor_Pins_Active[Selected_Pin];
  }

  // FIX - Add error handling for wrong "Action"

  // Some error handling
  Log(MQTT_Topic[Topic_Log_Error] + "/PinMonitor", "Reached end of loop with no hit this should not happen");
  return Pin_Error;
} // Pin_Monitor


// Refferance only - Pin Name
byte Pin_Monitor(byte Action, String Pin_Name) {
  return Pin_Monitor(Action, Pin_To_Number(Pin_Name));
}


// ############################################################ Pin_Monitor_State() ############################################################
void Pin_Monitor_State() {

  String Return_String;

  for (byte i = 0; i < Pin_Monitor_Pins_Number_Of; i++) {
    Return_String = Return_String + Pin_Monitor_Pins_Names[i] + ": " + Pin_Monitor_State_Text[Pin_Monitor_Pins_Active[i]];

    if (i != Pin_Monitor_Pins_Number_Of - 1) {
      Return_String = Return_String + " - ";
    }
  }

  Log(MQTT_Topic[Topic_System] + "PinMonitor/State", Return_String);

}

// ############################################################ Pin_Map() ############################################################
void Pin_Map() {

  String Pin_String =
    "Pin Map: D0=" + String(D0) +
    " D1=" + String(D1) +
    " D2=" + String(D2) +
    " D3=" + String(D3) +
    " D4=" + String(D4) +
    " D5=" + String(D5) +
    " D6=" + String(D6) +
    " D7=" + String(D7) +
    " D8=" + String(D8) +
    " A0=" + String(A0);

    Log(MQTT_Topic[Topic_System], Pin_String);

} // List_Pins()


// ############################################################ FS_cat() ############################################################
bool FS_cat(String File_Path) {

  if (SPIFFS.exists(File_Path)) {

    File f = SPIFFS.open(File_Path, "r");
    if (f && f.size()) {

      String cat_String;

      while (f.available()){
        cat_String += char(f.read());
      }

      f.close();

      Log(MQTT_Topic[Topic_System] + "/FS/cat", cat_String);
      return true;
    }
  }

  return false;
} // FS_cat()


// ############################################################ FS_del() ############################################################
bool FS_del(String File_Path) {

  if (SPIFFS.exists(File_Path)) {
    if (SPIFFS.remove(File_Path) == true) {
      Log(MQTT_Topic[Topic_System] + "/FS/del", File_Path);
      return true;
    }
    else {
      Log(MQTT_Topic[Topic_Log_Error] + "/FS/del", "Unable to delete: " + File_Path);
      return false;
    }
  }
  return false;
} // FS_cat()


// ############################################################ FS_File_Check() ############################################################
bool FS_File_Check(String File_Path, bool Report_Error) {

  if (SPIFFS.exists(File_Path)) return true;

  if (Report_Error == true) {
    Log(MQTT_Topic[Topic_Log_Error] + "/FS/FileCheck", "FS Unable to find file: " + File_Path);
  }
  return false;
} // FS_File_Check()


bool FS_File_Check(String File_Path) {
  return FS_File_Check(File_Path, true);
} // Referance only


// ############################################################ ESP_Reboot() ############################################################
void ESP_Reboot() {

  Log(MQTT_Topic[Topic_System], "Rebooting");
  Serial.flush();

  ESP.restart();

} // ESP_Reboot()


// ############################################################ ESP_Reboot() ############################################################
void ESP_Shutdown() {

  Log(MQTT_Topic[Topic_System], "Shutting down");
  Serial.flush();

  ESP.deepSleep(0);

} // ESP_Reboot()


// ############################################################ Reboot() ############################################################
void Reboot(unsigned long Reboot_In) {

  Log(MQTT_Topic[Topic_System], "Kill command issued, rebooting in " + String(Reboot_In / 1000) + " seconds");

  ESP_Power_Ticker.once_ms(Reboot_In, ESP_Reboot);

} // Reboot()


// ############################################################ Reboot() ############################################################
void Shutdown(unsigned long Shutdown_In) {

  Log(MQTT_Topic[Topic_System], "Kill command issued, shutting down in " + String(Shutdown_In / 1000) + " seconds");

  ESP_Power_Ticker.once_ms(Shutdown_In, ESP_Shutdown);

} // Reboot()


// ############################################################ SPIFFS_List() ############################################################
void FS_List() {
  String str = "";
  Dir dir = SPIFFS.openDir("/");
  while (dir.next()) {
    str += dir.fileName();
    str += " / ";
    str += dir.fileSize();
    str += "\r\n";
  }
  Log(MQTT_Topic[Topic_System] + "/FS/List", str);
} // SPIFFS_List


// ############################################################ SPIFFS_Format() ############################################################
void FS_Format() {
  Log(MQTT_Topic[Topic_System] + "/FS/Format", "SPIFFS Format started ... NOTE: Please wait 30 secs for SPIFFS to be formatted");
  SPIFFS.format();
  Log(MQTT_Topic[Topic_System] + "/FS/Format", "SPIFFS Format compleate");
} // SPIFFS_Format()


// ############################################################ PIR() ############################################################
void PIR_Loop() {

  // The PIR needs 60 seconds to worm up
    if (PIR_Configured == false || millis() < 60000 || ArduinoOTA_Active == true || Boot_Compleate == false) {
    return;
  }

  // Disable PIR Warmup blink
  if (Indicator_LED_Configured == true) Indicator_LED(LED_PIR, false);

  // Check each PIR
  for (byte i = 0; i < PIR_Max_Number_Of; i++) {

    if (PIR_Pins[i] != 255) {

      // If LDR is on aka its brigh or the PIR is desabled then return
      if (PIR_Disabled[i] == true || PIR_LDR_ON[i] == true) {
        if (PIR_ON_Send[i] == true) {
          MQTT_Client.publish(PIR_Topic[i].c_str(), 0, false, String(PIR_OFF_Payload[i] + ";").c_str());
          PIR_ON_Send[i] = false;
        }

        return;
      }

      bool PIR_Current_State = digitalRead(PIR_Pins[i]);

      // Current state check
      // HIGH = Motion detected
      if (PIR_Current_State == HIGH) {
        // Check if timer is running by checking if PIR_OFF_At[i] < millis()
        if (PIR_ON_Send[i] == false) {
          // Publish ON
          MQTT_Client.publish(PIR_Topic[i].c_str(), 0, false, String(PIR_ON_Payload[PIR_Selected_Level[i]][i] + ";").c_str());
          PIR_ON_Send[i] = true;
        }
        // Reset timer
        PIR_OFF_At[i] = millis() + (PIR_OFF_Delay[i] * 1000);
      }

      else {
        // Check if timer have elapsed
        if (millis() < PIR_OFF_At[i]) {
          return;
        }
        if (PIR_ON_Send[i] == true) {
          // Publish OFF
          MQTT_Client.publish(PIR_Topic[i].c_str(), 0, false, String(PIR_OFF_Payload[i] + ";").c_str());
          PIR_ON_Send[i] = false;
        }
      }
    }
  }

} // PIR_Loop()

// ############################################################ Dimmer_Fade() ############################################################
void Dimmer_Fade(byte Selected_Dimmer, byte State_Procent) {

  int State_Current = Dimmer_State[Selected_Dimmer - 1];

  int State_Target = State_Procent;
  float Temp_Float = State_Target * 0.01;
  State_Target = Temp_Float * 1023;
  Dimmer_State[Selected_Dimmer - 1] = State_Target;

  unsigned long Fade_Wait_Till = millis();

  while (State_Current != State_Target) {

    while (millis() < Fade_Wait_Till) {
      delay(1);
    }

    // Last jump +
    if (State_Current < State_Target && State_Target - State_Current <= Dimmer_Fade_Jump) {
      analogWrite(Dimmer_Pins[Selected_Dimmer - 1], State_Target);
      delay(5);
      break;
    }

    // Last jump -
    else if (State_Target < State_Current && State_Current - State_Target <= Dimmer_Fade_Jump) {
      analogWrite(Dimmer_Pins[Selected_Dimmer - 1], State_Target);
      delay(5);
      break;
    }

    // +
    else if (State_Current < State_Target) {
      State_Current += Dimmer_Fade_Jump;
      analogWrite(Dimmer_Pins[Selected_Dimmer - 1], State_Current);
    }

    // -
    else {
      State_Current -= Dimmer_Fade_Jump;
      analogWrite(Dimmer_Pins[Selected_Dimmer - 1], State_Current);
    }

    Fade_Wait_Till = millis() + Dimmer_Fade_Jump_Delay;
  } // while

  Dimmer_Procent[Selected_Dimmer - 1] = State_Procent;
  Log(String(MQTT_Topic[Topic_Dimmer]) + "/" + String(Selected_Dimmer) + "/State", Dimmer_Procent[Selected_Dimmer - 1]);

} // Dimmer_Fade()


// ############################################################ Dimmer() ############################################################
bool Dimmer(String Topic, String Payload) {

  if (Dimmer_Configured == false) {
    return false;
  }

  // /{Topic_Header}/Dimmer/"Hostname"
  if (Topic.indexOf(MQTT_Topic[Topic_Dimmer]) != -1) {

    Topic.replace(MQTT_Topic[Topic_Dimmer] + "/", "");

    byte Selected_Dimmer = Topic.toInt();

    // Ignore all requests thats larger then Dimmer_Max_Number_Of
    if (Selected_Dimmer <= Dimmer_Max_Number_Of) {
      // State request
      if (Payload.indexOf("?") != -1) {

        int State_Current = Dimmer_State[Selected_Dimmer - 1];
        float Temp_Float = State_Current * 0.01;
        State_Current = Temp_Float * 1023;

        Log(MQTT_Topic[Topic_Dimmer] + "/" + String(Selected_Dimmer) + "/State", State_Current);
      }

      else {
        int State_Target = Payload.toInt();

        // if value = current state turn off
        if (Dimmer_Procent[Selected_Dimmer - 1] == State_Target) {
          Dimmer_Fade(Selected_Dimmer, 0);
          return true;
        }

        if (Dimmer_State[Selected_Dimmer - 1] != State_Target) {
          Dimmer_Fade(Selected_Dimmer, State_Target);
          return true;
        }

      }
    }
  }
  return false;
} // Dimmer()


// ############################################################ LoadCell_Loop() ############################################################
// void LoadCell_Loop() {
//
//   if (Load_Cell_Configurated[0] == true) {
//     LoadCell_RA_Current1.addValue(Load_Cell1.get_units(1));
//   }
//   if (Load_Cell_Configurated[1] == true) {
//     LoadCell_RA_Current1.addValue(Load_Cell2.get_units(1));
//   }
//   if (Load_Cell_Configurated[2] == true) {
//     LoadCell_RA_Current1.addValue(Load_Cell3.get_units(1));
//   }
//   if (Load_Cell_Configurated[3] == true) {
//     LoadCell_RA_Current1.addValue(Load_Cell4.get_units(1));
//   }
// }

// ############################################################ LoadCell() ############################################################
// bool LoadCell(String Topic, String Payload) {
//
//   if (Load_Cell_Configurated == false) {
//     return false;
//   }
//
//   String LoadCell_String = Topic;
//   LoadCell_String.replace(MQTT_Topic[Topic_LoadCell] + "/", "");
//
//   byte Selected_LoadCell = LoadCell_String.toInt();
//
//   if (Topic.indexOf(MQTT_Topic[Topic_LoadCell]) != -1) {
//     if (Payload.indexOf("?") != -1) {
//
//       if (Selected_LoadCell == 1) {
//         Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/State", String(Load_Cell1.get_units(1)));
//       }
//       else if (Selected_LoadCell == 2) {
//         Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/State", String(Load_Cell2.get_units(1)));
//       }
//       else if (Selected_LoadCell == 3) {
//         Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/State", String(Load_Cell3.get_units(1)));
//       }
//       else if (Selected_LoadCell == 4) {
//         Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/State", String(Load_Cell4.get_units(1)));
//       }
//
//     }
//
//     else if (Payload.indexOf("Tare") != -1) {
//       Log(MQTT_Topic[Topic_System] + "/LoadCell", "Tare Started");
//       Load_Cell1.tare(25);
//       Log(MQTT_Topic[Topic_System] + "/LoadCell", "Tare Compleate");
//     }
//
//     else if (Payload.indexOf("Calibration") != -1) {
//       // Payload = Payload.substring(Payload.indexOf("Calibration "));
//       // Log(MQTT_Topic[Topic_System] + "/LoadCell", "Calibration set to: " + Payload);
//       // Load_Cell.set_scale(Payload.toFloat());
//     }
//     else if (Payload.indexOf("json") != -1) {
//
//       // Create json buffer
//       DynamicJsonBuffer jsonBuffer(400);
//       JsonObject& root_LoadCell = jsonBuffer.createObject();
//
//       // encode json string
//       root_LoadCell.set("Scale: 1", LoadCell_RA_Current1.getAverage());
//       // root_LoadCell.set("Scale: 1", LoadCell_Current_Value_Humidity[Selected_LoadCell]);
//       // root_LoadCell.set("Scale: ", LoadCell_Current_Value_Temperature[Selected_LoadCell]);
//       // root_LoadCell.set("Scale: ", LoadCell_Min_Value_Humidity[Selected_LoadCell]);
//       // root_LoadCell.set("Scale: ", LoadCell_Max_Value_Humidity[Selected_LoadCell]);
//       // root_LoadCell.set("Scale: ", LoadCell_Min_Value_Temperature[Selected_LoadCell]);
//       // root_LoadCell.set("Scale: ", LoadCell_Max_Value_Temperature[Selected_LoadCell]);
//
//       String LoadCell_String;
//
//       // Build json
//       root_LoadCell.printTo(LoadCell_String);
//
//       Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/json/State", LoadCell_String);
//
//       // Reset Min/Max
//       // LoadCell_Min_Value_Temperature[Selected_LoadCell] = LoadCell_Current_Value_Temperature[Selected_LoadCell];
//       // LoadCell_Max_Value_Temperature[Selected_LoadCell] = LoadCell_Current_Value_Temperature[Selected_LoadCell];
//       // LoadCell_Min_Value_Humidity[Selected_LoadCell] = LoadCell_Current_Value_Humidity[Selected_LoadCell];
//       // LoadCell_Max_Value_Humidity[Selected_LoadCell] = LoadCell_Current_Value_Humidity[Selected_LoadCell];
//
//       return true;
//
//
//       // Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/RA/State", String(LoadCell_RA_Current1.getAverage()));
//       // Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/RA/State", String(LoadCell_RA_Current2.getAverage()));
//       // Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/RA/State", String(LoadCell_RA_Current3.getAverage()));
//       // Log(MQTT_Topic[Topic_LoadCell] + "/" + String(Selected_LoadCell) + "/RA/State", String(LoadCell_RA_Current4.getAverage()));
//     }
//     return true;
//   }
//
//   return false;
// }


// ############################################################ DC_Voltmeter() ############################################################
bool DC_Voltmeter(String Topic, String Payload) {

  if (Topic.indexOf(MQTT_Topic[Topic_DC_Voltmeter]) != -1) {
    if (Payload.indexOf("?") != -1) {

      // read the value at analog input
      int value = analogRead(DC_Voltmeter_Pins);
      float vout = (value * DC_Voltmeter_Curcit_Voltage) / 1023.0;
      float vin = vout / (DC_Voltmeter_R2 / (DC_Voltmeter_R1 + DC_Voltmeter_R2));
      vin = vin + DC_Voltmeter_Offset;

      Log(MQTT_Topic[Topic_DC_Voltmeter] + "/State", String(vin));
      return true;
    }
  }

  return false;
}


// ############################################################ Echo() ############################################################
// Reads the distance
float Echo(byte Echo_Pin_Trigger, byte Echo_Pin_Echo) {

  // Clears the Echo_Pin_Trigger
  digitalWrite(Echo_Pin_Trigger, LOW);
  delayMicroseconds(2);

  // Sets the Echo_Pin_Trigger on HIGH state for 10 micro seconds
  digitalWrite(Echo_Pin_Trigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(Echo_Pin_Trigger, LOW);

  // Reads the Echo_Pin_Echo, returns the sound wave travel time in microseconds
  unsigned long Duration = pulseIn(Echo_Pin_Echo, HIGH, 75000);

  // Calculating the distance
  float Distance = (Duration / 2) * 0.0343;

  return Distance;


} // Echo


// ############################################################ Distance_Loop() ############################################################
void Distance_Loop() {

  if (Distance_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false) {
    return;
  }

  for (byte i = 0; i < Distance_Max_Number_Of; i++) {

    // Check if both pns is set
    if (Distance_Pins_Trigger[i] != 255 || Distance_Pins_Echo[i] != 255) {

      // Read distance
      Distance_Last_Reading[i] = Echo(Distance_Pins_Trigger[i], Distance_Pins_Echo[i]);

      if (i == 0) Distance_RA_1.addValue(Distance_Last_Reading[i]);
      if (i == 1) Distance_RA_2.addValue(Distance_Last_Reading[i]);
      if (i == 2) Distance_RA_3.addValue(Distance_Last_Reading[i]);
    }
  }
}

// ############################################################ Distance() ############################################################
// Handles MQTT Read request
bool Distance(String Topic, String Payload) {

  if (Topic.indexOf(MQTT_Topic[Topic_Distance]) != -1) {
    // Ignore state publish from localhost
    if (Topic.indexOf("/State") == -1)  {

      Topic.replace(MQTT_Topic[Topic_Distance] + "/", "");

      if (Topic.toInt() <= 0 || Topic.toInt() > Distance_Max_Number_Of) {
        Log(MQTT_Topic[Topic_Log_Error] + "/Distance", "Distance Sensor " + Topic + " is not a valid distance sensor");
        return true;
      }

      if (Distance_Pins_Trigger[Topic.toInt() - 1] == 255 || Distance_Pins_Echo[Topic.toInt() - 1] == 255) {
        Log(MQTT_Topic[Topic_Log_Error] + "/Distance", "Distance Sensor " + Topic + " is not configured");
        return true;
      }

      // Returns RunningAveridge
      if (Payload.indexOf("?") != -1) {
        float Distance = 0;

        if (Topic.toInt() == 1) Distance = Distance_RA_1.getAverage();
        else if (Topic.toInt() == 2) Distance = Distance_RA_2.getAverage();
        else if (Topic.toInt() == 3) Distance = Distance_RA_3.getAverage();

        Log(MQTT_Topic[Topic_Distance] + "/" + Topic + "/State", String(Distance));
        return true;
      }
      // Returns only last reading
      else if (Payload.indexOf("Raw") != -1) {
        Log(MQTT_Topic[Topic_Distance] + "/" + Topic + "/Raw/State", String(Distance_Last_Reading[Topic.toInt() - 1]));
        return true;
      }
    }
  }

  return false;
} // Distance()


// ############################################################ Distance_OFF() ############################################################
void Distance_Sensor_Auto_OFF() {

  for (byte i = 0; i < Distance_Max_Number_Of; i++) {
    if (Distance_Auto_OFF_At[i] < millis() && Distance_Auto_OFF_Active[i] == true) {

      if (Distance_Sensor_State[i] != false) {

        String Topic = Distance_Target_OFF[i].substring(0, Distance_Target_OFF[i].indexOf("&"));
        String Payload = Distance_Target_OFF[i].substring(Distance_Target_OFF[i].indexOf("&") + 1, Distance_Target_OFF[i].length());

        Log(Topic, Payload);

        Distance_Sensor_State[i] = false;

        String Publish_String = "'Distance Sensor' " + String(i + 1) + " Auto OFF Triggered";

        Log(MQTT_Topic[Topic_Distance], Publish_String.c_str());
      }
    }
  }
} // Distance_Sensor_Auto_OFF


// ############################################################ Distance_Sensor() ############################################################
void Distance_Sensor() {

  for (byte i = 0; i < Distance_Max_Number_Of; i++) {

    if (Distnace_Sensor_Read_At[i] < millis() && Distance_Refresh_Rate[i] != 0) {

      float Distance;

      if (i == 0) Distance = Distance_RA_1.getAverage();
      else if (i == 1) Distance = Distance_RA_2.getAverage();
      else if (i == 2) Distance = Distance_RA_3.getAverage();

      if (Distance == -1) {
        Log(MQTT_Topic[Topic_Log_Error] + "/Distance", "Distance Sensor - Echo mesure off");
        if (Distance_Auto_OFF_Active[i]) Distance_Auto_OFF_At[i] = Distance_Auto_OFF_Delay[i] + millis(); // TESTING Assuming masurement off is = person in room
        Distnace_Sensor_Read_At[i] = millis() + Distance_Refresh_Rate[i];
        return;
      }

      // Trigger check - ON
      else if (Distance < Distance_Trigger_At[i]) {

        if (Distance_Sensor_State[i] != true) {

          String Topic = Distance_Target_ON[i].substring(0, Distance_Target_ON[i].indexOf("&"));
          String Payload = Distance_Target_ON[i].substring(Distance_Target_ON[i].indexOf("&") + 1, Distance_Target_ON[i].length());

          Distance_Sensor_State[i] = true;

          Log(Topic, Payload);

          String Publish_String = "'Distance Sensor' " + String(i + 1) + " Triggered ON at: " + String(Distance);

          Log(MQTT_Topic[Topic_Distance] + "/State", Publish_String);

          if (Distance_Auto_OFF_Active[i]) Distance_Auto_OFF_At[i] = Distance_Auto_OFF_Delay[i] + millis();
        } // Trigger check - ON

        if (Distance_Sensor_State[i] == true) {
          if (Distance_Auto_OFF_Active[i]) Distance_Auto_OFF_At[i] = Distance_Auto_OFF_Delay[i] + millis();
        }

        // Trigger check - OFF
        else if (Distance > Distance_Trigger_At[i] && Distance_Auto_OFF_Active[i] == false) {

          if (Distance_Sensor_State[i] != false) {

            String Topic = Distance_Target_OFF[i].substring(0, Distance_Target_OFF[i].indexOf("&"));
            String Payload = Distance_Target_OFF[i].substring(Distance_Target_OFF[i].indexOf("&") + 1, Distance_Target_OFF[i].length());

            Distance_Sensor_State[i] = false;

            Log(Topic, Payload);

            String Publish_String = "'Distance Sensor' " + String(i + 1) + " Triggered OFF at: " + String(Distance);

            Log(MQTT_Topic[Topic_Distance] + "/State", Publish_String);
          }
        } // Trigger check - OFF

      }
      Distnace_Sensor_Read_At[i] = millis() + Distance_Refresh_Rate[i];
    } // if (Distnace_Sensor_Read_At[i] < millis())
  }
} // The_Bat()


// ############################################################ MQTT_Subscribe() ############################################################
void MQTT_Subscribe(String Topic, bool Activate_Topic, byte SubTopics) {

  byte Topic_Number = 0;

  for (byte i = 0; i < MQTT_Topic_Number_Of; i++) {
    if (Topic == MQTT_Topic[i]) {
      Topic_Number = i;
      break;
    }
  }

  MQTT_Topic_Subscribe_Active[Topic_Number] = Activate_Topic;
  MQTT_Topic_Subscribe_Subtopic[Topic_Number] = SubTopics;

  String Subscribe_String = MQTT_Topic[Topic_Number];

  if (MQTT_Subscribtion_Active[Topic_Number] == false && MQTT_Topic_Subscribe_Active[Topic_Number] == true) {

    if (MQTT_Topic_Subscribe_Subtopic[Topic_Number] == 1) Subscribe_String = Subscribe_String + "/+";
    else if (MQTT_Topic_Subscribe_Subtopic[Topic_Number] == 2) Subscribe_String = Subscribe_String + "/#";

    if (MQTT_Client.subscribe(Subscribe_String.c_str(), 0)) {
      Log(MQTT_Topic[Topic_System] + "/MQTT", "Subscribing to Topic: " + Subscribe_String + "  ... OK");
    }
    else {
      if (MQTT_Config_Requested == true) {
        Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Subscribing to Topic: " + Subscribe_String + "  ... FAILED");
      }
    }

    if (MQTT_Subscribtion_Active[Topic_Number] == true && MQTT_Topic_Subscribe_Active[Topic_Number] == true) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/MQTT", "Already subscribed to Topic: " + Subscribe_String);
    }
  }
}


// ############################################################ isValidNumber() ############################################################
bool isValidNumber(String str) {
  for(byte i=0;i<str.length();i++)
  {
    if(isDigit(str.charAt(i))) return true;
  }
  return false;
} // isValidNumber()


// ############################################################ Relay_Auto_OFF_Check() ############################################################
void Relay_Auto_OFF_Check(byte Selected_Relay) {

  if (Relay_Pin_Auto_Off_Delay[Selected_Relay - 1] != false) {
    Relay_Auto_OFF_At[Selected_Relay - 1] = millis() + Relay_Pin_Auto_Off_Delay[Selected_Relay - 1];
    Relay_Auto_OFF_Active[Selected_Relay - 1] = true;
  }
} // _Relay_Auto_OFF_Check()


// ############################################################ Relay() ############################################################
void Relay(String Topic, String Payload) {

  if (Payload.length() > 1) Payload = Payload.substring(0, 1); // "Trim" length to avoid some wird error

  String Relay_String = Topic;
  Relay_String.replace(MQTT_Topic[Topic_Relay] + "/", "");

  byte Selected_Relay = Relay_String.toInt();

  // Ignore all requests thats larger then _Relay_Max_Number_Of
  if (Selected_Relay < Relay_Max_Number_Of) {
    // State request
    if (Payload == "?") {
      String State_String;
      if (digitalRead(Relay_Pins[Selected_Relay - 1]) == Relay_On_State) State_String += "1";
      else State_String += "0";
      Log(MQTT_Topic[Topic_Relay] + "/" + String(Selected_Relay) + "/State", State_String);
      return;
    }

    else if(isValidNumber(Payload) == true) {
      byte State = Payload.toInt();

      if (State > 2) {
        Log(MQTT_Topic[Topic_Log_Error] + "/Relay", "Relay - Invalid command entered");
        return;
      }

      bool State_Digital = false;
      if (State == ON) State_Digital = Relay_On_State;
      else if (State == OFF) State_Digital = !Relay_On_State;
      else if (State == FLIP) State_Digital = !digitalRead(Relay_Pins[Selected_Relay - 1]);

      if (Selected_Relay <= Relay_Max_Number_Of && digitalRead(Relay_Pins[Selected_Relay - 1]) != State_Digital) {
        digitalWrite(Relay_Pins[Selected_Relay - 1], State_Digital);
        if (State_Digital == Relay_On_State) {
          Log(MQTT_Topic[Topic_Relay] + "/" + String(Selected_Relay) + "/State", String(ON));
          Relay_Auto_OFF_Check(Selected_Relay);
        }
        else {
          Log(MQTT_Topic[Topic_Relay] + "/" + String(Selected_Relay) + "/State", String(OFF));
        }
      }
    }
  }
} // Relay()


// ############################################################ Relay_Auto_OFF_Loop() ############################################################
void Relay_Auto_OFF_Loop() {

  for (byte i = 0; i < Relay_Max_Number_Of; i++) {

    if (Relay_Auto_OFF_Active[i] == true && Relay_Pin_Auto_Off_Delay != 0) {
      if (Relay_Auto_OFF_At[i] < millis()) {

        if (digitalRead(Relay_Pins[i]) == Relay_On_State) {
          digitalWrite(Relay_Pins[i], !Relay_On_State);
          Log(MQTT_Topic[Topic_Relay] + "/" + String(i + 1) + "/State", "Relay " + String(i + 1) + " Auto OFF");
          Log(MQTT_Topic[Topic_Relay] + "/" + String(i + 1) + "/State", String(OFF));
        }

        Relay_Auto_OFF_Active[i] = false;
      }
    }
  }
} // Relay_Auto_OFF()


// ############################################################ Relay_Auto_OFF() ############################################################
void Relay_Auto_OFF(byte Relay_Number) {
    if (digitalRead(Relay_Pins[Relay_Number - 1]) == Relay_On_State) {
      digitalWrite(Relay_Pins[Relay_Number - 1], !Relay_On_State);

      Log(MQTT_Topic[Topic_Relay] + "/" + String(Relay_Number + 1) + "/State", String(OFF));
    }
  } // _Relay_Auto_OFF()


// ############################################################ DHT_Loop() ############################################################
void DHT_Loop() {

  if (DHT_Configured == false || ArduinoOTA_Active == true || Boot_Compleate == false || MQTT_Config_Requested == false) {
    return;
  }

  for (byte Sensor_Number = 0; Sensor_Number < DHT_Max_Number_Of; Sensor_Number++) {
    if (DHT_Pins[Sensor_Number] != 255) {

      unsigned long DHT_Current_Read = millis();

      // Check if its ok to read from the sensor
      if (DHT_Current_Read - DHT_Last_Read >= DHT_Refresh_Rate) {

        int Error_Code = SimpleDHTErrSuccess;
        // Read sensors values
        Error_Code = dht22.read2(DHT_Pins[Sensor_Number], &DHT_Current_Value_Temperature[Sensor_Number], &DHT_Current_Value_Humidity[Sensor_Number], NULL);

        // Error check
        if (Error_Code != SimpleDHTErrSuccess) {
          // Error count check
          if (DHT_Error_Counter[Sensor_Number] > DHT_Distable_At_Error_Count) {
            // Log Error
            Log(MQTT_Topic[Topic_Log_Error] + "/DHT/" + String(Sensor_Number + 1), "Disabling DHT " + String(Sensor_Number + 1) + " due to excessive errors. Error count: " + String(DHT_Error_Counter[Sensor_Number]) + " Threshold: " + String(DHT_Distable_At_Error_Count));
            // Disable sensor pin
            DHT_Pins[Sensor_Number] = 255;

            bool DHT_Still_Active = false;

            // Check if any workind DHT sensors left
            for (byte ii = 0; ii < DHT_Max_Number_Of; ii++) {
              if (DHT_Pins[ii] != 255) {
                DHT_Still_Active = true;
              }
            }

            // If no sensors left disable DHT
            if (DHT_Still_Active == false) {
              DHT_Configured = false;
              Log(MQTT_Topic[Topic_Log_Error] + "/DHT", "No DHT22 sensors enabled, disabling DHT");
            }
          }
          else {
            Log(MQTT_Topic[Topic_Log_Warning] + "/DHT/" + String(Sensor_Number + 1), "Read DHT22 failed, Error: " + String(Error_Code, HEX));
            DHT_Error_Counter[Sensor_Number] = DHT_Error_Counter[Sensor_Number] + 1;
          }
        }
        // All ok
        else {
          // Reset error counter
          DHT_Error_Counter[Sensor_Number] = 0;
          // Reset default - Testing only one value assuming reast is default as well
          if (DHT_Min_Value_Temperature[Sensor_Number] == -1337) {
            DHT_Min_Value_Temperature[Sensor_Number] = DHT_Current_Value_Temperature[Sensor_Number];
            DHT_Max_Value_Temperature[Sensor_Number] = DHT_Current_Value_Temperature[Sensor_Number];
            DHT_Min_Value_Humidity[Sensor_Number] = DHT_Current_Value_Humidity[Sensor_Number];
            DHT_Max_Value_Humidity[Sensor_Number] = DHT_Current_Value_Humidity[Sensor_Number];
          }
          // Save Min/Max
          else {
            DHT_Min_Value_Temperature[Sensor_Number] = min(DHT_Min_Value_Temperature[Sensor_Number], DHT_Current_Value_Temperature[Sensor_Number]);
            DHT_Max_Value_Temperature[Sensor_Number] = max(DHT_Max_Value_Temperature[Sensor_Number], DHT_Current_Value_Temperature[Sensor_Number]);
            DHT_Min_Value_Humidity[Sensor_Number] = min(DHT_Min_Value_Humidity[Sensor_Number], DHT_Current_Value_Humidity[Sensor_Number]);
            DHT_Max_Value_Humidity[Sensor_Number] = max(DHT_Max_Value_Humidity[Sensor_Number], DHT_Current_Value_Humidity[Sensor_Number]);
          }
        }

        // Save the last time you read the sensor
        DHT_Last_Read = millis();
      }
    }
  }

} // DHT_Loop()


// ############################################################ DHT() ############################################################
bool DHT(String Topic, String Payload) {

  if (DHT_Configured == false) {
    return false;
  }

  if (Topic.indexOf(MQTT_Topic[Topic_DHT]) != -1) {

    Topic.replace(MQTT_Topic[Topic_DHT] + "/", "");

    byte Selected_DHT = Topic.toInt() - 1;

    if (Topic.toInt() <= DHT_Max_Number_Of) {

      Payload = Payload.substring(0, Payload.indexOf(";"));

      if (Payload == "?") {
        Log(MQTT_Topic[Topic_DHT] + "/" + String(Selected_DHT + 1) + "/Humidity", String(DHT_Current_Value_Humidity[Selected_DHT]));
        Log(MQTT_Topic[Topic_DHT] + "/" + String(Selected_DHT + 1) + "/Temperature", String(DHT_Current_Value_Temperature[Selected_DHT]));
        return true;
      }

      else if (Payload == "json") {

        // Create json buffer
        DynamicJsonBuffer jsonBuffer(80);
        JsonObject& root_DHT = jsonBuffer.createObject();

        // encode json string
        root_DHT.set("Current Humidity", DHT_Current_Value_Humidity[Selected_DHT]);
        root_DHT.set("Current Temperature", DHT_Current_Value_Temperature[Selected_DHT]);
        root_DHT.set("Min Humidity", DHT_Min_Value_Humidity[Selected_DHT]);
        root_DHT.set("Max Humidity", DHT_Max_Value_Humidity[Selected_DHT]);
        root_DHT.set("Min Temperature", DHT_Min_Value_Temperature[Selected_DHT]);
        root_DHT.set("Max Temperature", DHT_Max_Value_Temperature[Selected_DHT]);

        String DHT_String;

        // Build json
        root_DHT.printTo(DHT_String);

        Log(MQTT_Topic[Topic_DHT] + "/" + String(Topic.toInt()) + "/json/State", DHT_String);

        // Reset Min/Max
        DHT_Min_Value_Temperature[Selected_DHT] = DHT_Current_Value_Temperature[Selected_DHT];
        DHT_Max_Value_Temperature[Selected_DHT] = DHT_Current_Value_Temperature[Selected_DHT];
        DHT_Min_Value_Humidity[Selected_DHT] = DHT_Current_Value_Humidity[Selected_DHT];
        DHT_Max_Value_Humidity[Selected_DHT] = DHT_Current_Value_Humidity[Selected_DHT];

        return true;
      }

    }
  }
  return false;
} // DHT


// ############################################################ PIR() ############################################################
bool PIR(String Topic, String Payload) {

  if (PIR_Configured == false) {
    return false;
  }

  if (Topic.indexOf(MQTT_Topic[Topic_PIR]) != -1) {

    Topic.replace(MQTT_Topic[Topic_PIR] + "/", "");

    byte Selected_PIR = Topic.toInt() - 1;

    if (Topic.toInt() <= PIR_Max_Number_Of) {

      Payload = Payload.substring(0, Payload.indexOf(";"));

      // Find current PIR state
      String PIR_State;

      // PIR is on if millis() < PIR_OFF_At[i] aka timer running
      // ON
      if (millis() < PIR_OFF_At[Selected_PIR]) {
        PIR_State = "1";
      }
      // OFF
      else {
        PIR_State = "0";
      }

      if (Payload == "?") {
        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/State", PIR_State);
        return true;
      }

      else if (Payload.indexOf("LDR ") != -1) {

        Payload.replace("LDR ", "");

        PIR_LDR_ON[Selected_PIR] = Payload.toInt();

        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/LDR/State", PIR_LDR_ON[Selected_PIR]);
        return true;
      }

      else if (Payload.indexOf("Level ") != -1) {
        // Get selection
        Payload.replace("Level ", "");

        PIR_Selected_Level[Selected_PIR] = Payload.toInt();

        // FIX - Add level check has to be = to max level

        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/Level/State", Payload);
        return true;
      }

      else if (Payload == "Enable") {
        PIR_Disabled[Selected_PIR] = false;
        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/Disabled/State", false);
        return true;
      }
      else if (Payload == "Disable") {
        PIR_Disabled[Selected_PIR] = true;
        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/Disabled/State", true);
        return true;
      }

      else if (Payload == "json") {
        // Create json buffer
        DynamicJsonBuffer jsonBuffer(190);
        JsonObject& root_PIR = jsonBuffer.createObject();

        // encode json string
        root_PIR.set("State", PIR_State);
        root_PIR.set("Level", PIR_Selected_Level[Selected_PIR]);
        root_PIR.set("Level Value", PIR_ON_Payload[PIR_Selected_Level[Selected_PIR] - 1][Selected_PIR]);
        root_PIR.set("LDR", PIR_LDR_ON[Selected_PIR]);
        root_PIR.set("Disabled", PIR_Disabled[Selected_PIR]);

        String PIR_String;

        root_PIR.printTo(PIR_String);

        Log(MQTT_Topic[Topic_PIR] + "/" + String(Selected_PIR + 1) + "/json/State", PIR_String);

        return true;
      }

    }
  }


  return false;
}


// ############################################################ Buzzer_Play() ############################################################
void Buzzer_Play() {

  // Delay
  if (Buzzer_Melody.substring(0, 1) == "-") {

    noTone(Buzzer_Pins);

    // Remove "-"
    Buzzer_Melody = Buzzer_Melody.substring(1, Buzzer_Melody.length());

    int Tone_Delay = Buzzer_Melody.substring(0, Buzzer_Melody.indexOf("-")).toInt();

    Buzzer_Melody = Buzzer_Melody.substring(Buzzer_Melody.indexOf("-") + 1, Buzzer_Melody.length());

    Buzzer_Ticker.once_ms(Tone_Delay, Buzzer_Play);
  } // Delay


  // Play
  else if (Buzzer_Melody.indexOf(",") != -1) {
    int Tone = Buzzer_Melody.substring(0, Buzzer_Melody.indexOf(",")).toInt();
    unsigned long Tone_Time = Buzzer_Melody.substring(Buzzer_Melody.indexOf(",") + 1, Buzzer_Melody.length()).toInt();

    Serial.println("Buzzer_Pins: " + String(Buzzer_Pins));
    Serial.println("Tone: " + String(Tone));
    Serial.println("Tone_Time: " + String(Tone_Time));

    Buzzer_Melody = Buzzer_Melody.substring(Buzzer_Melody.indexOf(String(Tone_Time)) + String(Tone_Time).length(), Buzzer_Melody.length());

    tone(Buzzer_Pins, Tone, Tone_Time);

    if (Buzzer_Melody != "") {
      Buzzer_Ticker.once_ms(Tone_Time, Buzzer_Play);
    } // Play
  }

} // Buzzer_Play()


// ############################################################ Buzzer() ############################################################
bool Buzzer(String Topic, String Payload) {
  if (Topic.indexOf(MQTT_Topic[Topic_Buzzer]) != -1) {
    Buzzer_Melody = Payload;
    Buzzer_Play();
    return true;
  }

  else return false;
} // Buzzer()


// ############################################################ MQTT_Allow_Flash() ############################################################
void MQTT_Allow_Flash() {

  if (Allow_Flash == false) {
    Allow_Flash = true;
    MQTT_Allow_Flash_Ticker.once_ms(MQTT_Allow_Flash_Delay, MQTT_Allow_Flash);
    Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "OTA flash enabled for " + String(MQTT_Allow_Flash_Delay / 1000) + " seconds");
  }

  else {
    Allow_Flash = false;
    MQTT_Allow_Flash_Ticker.detach();
    Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "OTA flash disabled");
  }

} // MQTT_Allow_Flash()


// ############################################################ OTA_Handler() ############################################################
void OTA_Handler() {

  if (ArduinoOTA_Active == true) {
    ArduinoOTA.handle();
  }

  else if (Allow_Flash == true) {
    ArduinoOTA.handle();
  }

  else if (MQTT_Allow_Flash_Password == "-1") {
    ArduinoOTA.handle();
  }

} // OTA_Handler()


// ############################################################ UpTime_String() ############################################################
String Uptime_String() {

  unsigned long Uptime_Now = millis();

  unsigned long Uptime_Weeks = Uptime_Now / 604800000000;
  if (Uptime_Weeks != 0) Uptime_Now -= Uptime_Weeks * 604800000000;

  unsigned long Uptime_Days = Uptime_Now / 86400000;
  if (Uptime_Days != 0) Uptime_Now -= Uptime_Days * 86400000;

  unsigned long Uptime_Hours = Uptime_Now / 3600000;
  if (Uptime_Hours != 0) Uptime_Now -= Uptime_Hours * 3600000;

  unsigned long Uptime_Minutes = Uptime_Now / 60000;
  if (Uptime_Minutes != 0) Uptime_Now -= Uptime_Minutes * 60000;

  unsigned long Uptime_Seconds = Uptime_Now / 1000;
  if (Uptime_Seconds != 0) Uptime_Now -= Uptime_Seconds * 1000;

  String Uptime_String = "Up for: ";

  if (Uptime_Weeks != 0) {
    if (Uptime_Weeks == 1) Uptime_String += String(Uptime_Weeks) + " week ";
    else Uptime_String += String(Uptime_Weeks) + " weeks ";
  }

  if (Uptime_Days != 0) {
    if (Uptime_Days == 1) Uptime_String += String(Uptime_Days) + " day ";
    else Uptime_String += String(Uptime_Days) + " days ";
  }

  if (Uptime_Hours != 0) {
    if (Uptime_Hours == 1) Uptime_String += String(Uptime_Hours) + " hour ";
    else Uptime_String += String(Uptime_Hours) + " hours ";
  }

  if (Uptime_Minutes != 0) Uptime_String += String(Uptime_Minutes) + " min ";
  if (Uptime_Seconds != 0) Uptime_String += String(Uptime_Seconds) + " sec ";
  if (Uptime_Now != 0) Uptime_String += String(Uptime_Now) + " ms ";

  if (Uptime_String.substring(Uptime_String.length(), Uptime_String.length() - 1) == " ") {
    Uptime_String = Uptime_String.substring(0, Uptime_String.length() - 1);
  }

  return Uptime_String;

} // Uptime_String()


// ############################################################ connectToWifi() ############################################################
void connectToWifi() {

  // Disable interrupts for the system not to chast when wifi is trying to connect
  // noInterrupts();

  if (WiFi.status() == WL_CONNECTED) {
    Wifi_State = 3;
  }

  if (Wifi_State != 3) {
    Log(MQTT_Topic[Topic_System] + "/WiFi", "Starting WiFi ...");

    WiFi.begin(WiFi_SSID.c_str(), WiFi_Password.c_str());

    Wifi_State = 3;
  }
}


// ############################################################ MQTT_KeepAlive() ############################################################
void MQTT_KeepAlive() {

  // If the MQTT Client is not connected no reason to send try to send a keepalive
  // Dont send keepalives during updates
  if (MQTT_Client.connected() == false && ArduinoOTA_Active == true) return;

  // Create json buffer
  DynamicJsonBuffer jsonBuffer(220);
  JsonObject& root_KL = jsonBuffer.createObject();

  // encode json string
  root_KL.set("Hostname", Hostname);
  root_KL.set("IP", IPtoString(WiFi.localIP()));
  root_KL.set("Uptime", millis());
  root_KL.set("FreeMemory", system_get_free_heap_size());
  root_KL.set("Software", Version);
  root_KL.set("IP", IPtoString(WiFi.localIP()));
  root_KL.set("RSSI", WiFi.RSSI());

  String KeepAlive_String;

  root_KL.printTo(KeepAlive_String);

  Log(MQTT_Topic[Topic_KeepAlive], KeepAlive_String);

} // MQTT_KeepAlive()


// ############################################################ onMqttConnect() ############################################################
void onMqttConnect(bool sessionPresent) {
  Log(MQTT_Topic[Topic_System] + "/MQTT", "Connected to Broker: '" + MQTT_Broker + "'");

  Indicator_LED(LED_MQTT, false);

  // ------------------------------ MQTT KeepAlive ------------------------------
  MQTT_KeepAlive_Ticker.attach_ms(MQTT_KeepAlive_Interval, MQTT_KeepAlive);

  for (byte i = 0; i < MQTT_Topic_Number_Of; i++) {
    MQTT_Subscribe(MQTT_Topic[i], MQTT_Topic_Subscribe_Active[i], MQTT_Topic_Subscribe_Subtopic[i]);
  }

  if (MQTT_Config_Requested == false) {
    // boot message
    Log(MQTT_Topic[Topic_System], "Booting Dobby version: " + String(Version) + " Free Memory: " + String(system_get_free_heap_size()));

    // Request config
    Log(MQTT_Topic[Topic_Dobby] + "Config", Hostname + "," + Config_ID); // Request config

    MQTT_Config_Requested = true;
  }

  // Enable interrupts again after mqtt is connected
  // interrupts();

} // onMqttConnect()


// ############################################################ connectToMqtt() ############################################################
void connectToMqtt() {
  Log(MQTT_Topic[Topic_System] + "/MQTT", "Connecting to Broker: '" + MQTT_Broker + "' ...");
  MQTT_Client.connect();
}


// ############################################################ onMqttDisconnect() ############################################################
void onMqttDisconnect(AsyncMqttClientDisconnectReason reason) {

  Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Disconnected from Broker: '" + MQTT_Broker + "'");

  if (Indicator_LED_Configured == true) Indicator_LED(LED_MQTT, true);

  for (byte i = 0; i < MQTT_Topic_Number_Of; i++) MQTT_Subscribtion_Active[i] = false;

  MQTT_KeepAlive_Ticker.detach();

  if (WiFi.isConnected()) {
    mqttReconnectTimer.once(MQTT_Reconnect_Delay, connectToMqtt);
  }
}


// ############################################################ MQTT_Settings_Set(String Array) ############################################################
bool MQTT_Settings_Set(String String_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Find number and set variable
    String_Array[i] = Payload_String.substring(0, Payload_String.indexOf(","));

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

    String Publish_String = "'" + Log_Text + "' changed to: ";

    // Publish String - Pins
    if (Log_Text.indexOf(" Pins") != -1) {
      for (byte i = 0; i < Devices_Max; i++) {
        Publish_String = Publish_String + String(i + 1) + "=" + Number_To_Pin(String_Array[i].toInt());
        if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
      }
    }

    // Publish String - Anything else
    else {
      for (byte i = 0; i < Devices_Max; i++) {
        Publish_String = Publish_String + String(i + 1) + "=" + String_Array[i];
        if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
      }
    }

  Log(MQTT_Target, Publish_String);
  return true;

} // MQTT_Settings_Set()

// ############################################################ MQTT_Settings_Set(Integer Array) ############################################################
bool MQTT_Settings_Set(int Integer_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Find number and set variable
    Integer_Array[i] = Payload_String.substring(0, Payload_String.indexOf(",")).toInt();

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

  String Publish_String = "'" + Log_Text + "' changed to: ";

  // Publish String - Pins
  if (Log_Text.indexOf(" Pins") != -1) {
    for (byte i = 0; i < Devices_Max; i++) {
      Publish_String = Publish_String + String(i + 1) + "=" + Number_To_Pin(Integer_Array[i]);
      if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
    }
  }

  // Publish String - Anything else
  else {
    for (byte i = 0; i < Devices_Max; i++) {
      Publish_String = Publish_String + String(i + 1) + "=" + Integer_Array[i];
      if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
    }
  }

  Log(MQTT_Target, Publish_String);
  return true;

} // MQTT_Settings_Set()


// ############################################################ MQTT_Settings_Set(Float Array) ############################################################
bool MQTT_Settings_Set(float Float_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Find number and set variable
    Float_Array[i] = Payload_String.substring(0, Payload_String.indexOf(",")).toFloat();

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

  String Publish_String = "'" + Log_Text + "' changed to: ";

  for (byte i = 0; i < Devices_Max; i++) {
    Publish_String = Publish_String + String(i + 1) + "=" + Float_Array[i];
    if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
  }

  Log(MQTT_Target, Publish_String);

  return true;

} // MQTT_Settings_Set()


// ############################################################ MQTT_Settings_Set(Byte Array) ############################################################
bool MQTT_Settings_Set(byte Byte_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Get value
    String Pin_String = Payload_String.substring(0, Payload_String.indexOf(","));

    // Check if number of pin name
    // Pin Nname
    if (Pin_String.indexOf("D") != -1) {
      Byte_Array[i] = Pin_To_Number(Payload_String.substring(0, Payload_String.indexOf(",")));
    }
    // Pin Number
    else {
      Byte_Array[i] = Payload_String.substring(0, Payload_String.indexOf(",")).toInt();
    }

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

  String Publish_String = "'" + Log_Text + "' changed to: ";

  // Publish String - Pins
  if (Log_Text.indexOf(" Pins") != -1) {
    for (byte i = 0; i < Devices_Max; i++) {
      Publish_String = Publish_String + String(i + 1) + "=" + Number_To_Pin(Byte_Array[i]);
      if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
    }
  }

  // Publish String - Anything else
  else {
    for (byte i = 0; i < Devices_Max; i++) {
      Publish_String = Publish_String + String(i + 1) + "=" + Byte_Array[i];
      if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
    }
  }


  Log(MQTT_Target, Publish_String);
  return true;


} // MQTT_Settings_Set()

// ############################################################ MQTT_Settings_Set(Unsigned Long Array) ############################################################
bool MQTT_Settings_Set(unsigned long Unsigned_Long_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Find number and set variable
    Unsigned_Long_Array[i] = Payload_String.substring(0, Payload_String.indexOf(",")).toInt();

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

  // Publish String
  String Publish_String = "'" + Log_Text + "' changed to: ";
  for (byte i = 0; i < Devices_Max; i++) {
    Publish_String = Publish_String + String(i + 1) + "=" + Unsigned_Long_Array[i];
    if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
  }


  Log(MQTT_Target, Publish_String);
  return true;


} // MQTT_Settings_Set()

// ############################################################ MQTT_Settings_Set(Boolian Array) ############################################################
bool MQTT_Settings_Set(bool Boolian_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

  String Payload_String = Payload + ","; // adding "," to make for loop add up

  for (byte i = 0; i < Devices_Max; i++) {

    // Find number and set variable
    Boolian_Array[i] = Payload_String.substring(0, Payload_String.indexOf(",")).toInt();

    // Remove the value
    Payload_String = Payload_String.substring(Payload_String.indexOf(",") + 1, Payload_String.length());

    if (Payload_String.indexOf(",") == -1) break; // No more pins in string
  }

  // Publish String
  String Publish_String = "'" + Log_Text + "' changed to: ";
  for (byte i = 0; i < Devices_Max; i++) {
    Publish_String = Publish_String + String(i + 1) + "=" + Boolian_Array[i];
    if (i != Devices_Max - 1) Publish_String = Publish_String + " ";
  }


  Log(MQTT_Target, Publish_String);
  return true;


} // MQTT_Settings_Set()



// ################################### FS_Commands() ###################################
bool FS_Commands(String Payload) {

  if (Payload == "Format") {
    FS_Format();
    return true;
  }
  else if (Payload == "List") {
    FS_List();
    return true;
  }
  else if (Payload.indexOf("cat /") != -1) {
    FS_cat(Payload.substring(String("cat ").length(), Payload.length()));
    return true;
  }
  else if (Payload.indexOf("del /") != -1) {
    FS_del(Payload.substring(String("del ").length(), Payload.length()));
    return true;
  }

  return false;
}


// #################################### byte ArrayToString() ####################################
String Byte_ArrayToString(byte Byte_Array[]) {
  String Return_String;
  for (size_t i = 0; i < 255; i++) {
    if (Byte_Array[i] == 255) break;
    Return_String = Return_String + String(Byte_Array[i]) + ",";
  }
  return Return_String.substring(0, Return_String.length() - 1);
} // ArrayToString

String String_ArrayToString(String String_Array[]) {
  String Return_String;
  for (size_t i = 0; i < 255; i++) {
    if (String_Array[i] == "") break;
    Return_String = Return_String + String(String_Array[i]) + ",";
  }
  return Return_String.substring(0, Return_String.length() - 1);
} // ArrayToString

String ul_ArrayToString(unsigned long ul_Array[]) {
  String Return_String;
  for (size_t i = 0; i < 255; i++) {
    if (ul_Array[i] == 0) break;
    Return_String = Return_String + String(ul_Array[i]) + ",";
  }
  return Return_String.substring(0, Return_String.length() - 1);
} // ArrayToString

String Bool_ArrayToString(bool bool_Array[]) {
  String Return_String;
  for (size_t i = 0; i < 255; i++) {
    if (bool_Array[i] == false) break;
    Return_String = Return_String + String(bool_Array[i]) + ",";
  }
  return Return_String.substring(0, Return_String.length() - 1);
} // ArrayToString

String int_ArrayToString(int int_Array[]) {
  String Return_String;
  for (size_t i = 0; i < 255; i++) {
    if (int_Array[i] == false) break;
    Return_String = Return_String + String(int_Array[i]) + ",";
  }
  return Return_String.substring(0, Return_String.length() - 1);
} // ArrayToString


// #################################### FS_Config_Build() ####################################
String FS_Config_Build() {

  DynamicJsonBuffer jsonBuffer(Config_Json_Max_Buffer_Size);
  JsonObject& root_Config = jsonBuffer.createObject();

  // System
  if (Hostname != "") root_Config.set("Hostname", Hostname);
  root_Config.set("System_Header", System_Header);
  root_Config.set("System_Sub_Header", System_Sub_Header);
  root_Config.set("Config_ID", Config_ID);
  if (WiFi_SSID != "") root_Config.set("WiFi_SSID", WiFi_SSID);
  if (WiFi_Password != "") root_Config.set("WiFi_Password", WiFi_Password);
  if (MQTT_Broker != "") root_Config.set("MQTT_Broker", MQTT_Broker);
  if (MQTT_Port != "") root_Config.set("MQTT_Port", MQTT_Port);
  root_Config.set("MQTT_Username", MQTT_Username);
  root_Config.set("MQTT_Password", MQTT_Password);
  root_Config.set("MQTT_Allow_Flash_Password", MQTT_Allow_Flash_Password);
  root_Config.set("MQTT_KeepAlive_Interval", MQTT_KeepAlive_Interval);

  //Relay
  if (Relay_Configured == true) {
    root_Config.set("Relay_On_State", Relay_On_State);
    root_Config.set("Relay_Pins", Byte_ArrayToString(Relay_Pins));
    root_Config.set("Relay_Pin_Auto_Off", Bool_ArrayToString(Relay_Pin_Auto_Off));
    root_Config.set("Relay_Pin_Auto_Off_Delay", ul_ArrayToString(Relay_Pin_Auto_Off_Delay));
  }

  // Byzzer
  if (Buzzer_Configured == true) {
    root_Config.set("Buzzer_Pins", Buzzer_Pins);
  }

  if (DHT_Configured == true) {
    root_Config.set("DHT_Pins", Byte_ArrayToString(DHT_Pins));
  }

  if (Distance_Configured == true) {
    root_Config.set("Distance_Pins_Trigger", Byte_ArrayToString(Distance_Pins_Trigger));
    root_Config.set("Distance_Pins_Echo", Byte_ArrayToString(Distance_Pins_Echo));
    root_Config.set("Distance_Trigger_At", Distance_Trigger_At);
    root_Config.set("Distance_Target_ON", Distance_Target_ON);
    root_Config.set("Distance_Target_OFF", Distance_Target_OFF);
    root_Config.set("Distance_Refresh_Rate", Distance_Refresh_Rate);
    root_Config.set("Distance_Auto_OFF_Delay", Distance_Auto_OFF_Delay);
    root_Config.set("Distance_Auto_OFF_Active", Distance_Auto_OFF_Active);
  }

  if (Dimmer_Configured == true) {
    root_Config.set("Dimmer_Pins", Byte_ArrayToString(Dimmer_Pins));
  }

  if (Button_Configured == true) {
    root_Config.set("Button_Pins", Byte_ArrayToString(Button_Pins));
    root_Config.set("Button_Target", Button_Target);
  }


  String Return_String;
  root_Config.printTo(Return_String);
  return Return_String;

} // FS_Config_Build()



// #################################### FS_Config_Save() ####################################
bool FS_Config_Save() {

  SPIFFS.begin();

  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");

  if (!configFile) {
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file for writing");
    return false;
  }

  configFile.print(FS_Config_Build());
  configFile.close();

  SPIFFS.end();

  Log(MQTT_Topic[Topic_System] + "/FSConfig", "Saved to SPIFFS");

  return true;
}


// ############################################################ CLI_Print() ############################################################
void CLI_Print(String Print_String) {

  Serial.println(Print_String);
  Serial.print(Hostname + ": ");
}


// ############################################################ Get_Serial_Input() ############################################################
bool Get_Serial_Input() {

  if (Serial.available() > 0) {
    String Incomming_String = Serial.readString();
    Serial.print(Incomming_String);
    CLI_Input_String = CLI_Input_String + Incomming_String;
  }


  if (CLI_Input_String.indexOf("\n") != -1) {
    CLI_Input_String.replace("\r", "");
    CLI_Input_String.replace("\n", "");

    CLI_Input_String.trim();

    CLI_Command_Complate = true;
    return true;
  }

  return false;
}


// ############################################################ Wait_For_Serial_Input() ############################################################
void Wait_For_Serial_Input(String Wait_String) {
  CLI_Input_String = "";

  Serial.println();
  Serial.print("Please enter new " + Wait_String + ": ");

  while (Get_Serial_Input() == false) delay(1);
}


// ############################################################ CLI_Config_Check() ############################################################
String CLI_Config_Check() {

  if (Hostname == "NotConfigured") {
    return "Failed - Hostname not configured";
  }
  else if (WiFi_SSID == "") {
    return "Failed - WiFi SSID not configured";
  }
  else if (WiFi_Password == "") {
    return "Failed - WiFi Password not configured";
  }
  else if (MQTT_Broker == "") {
    return "Failed - MQTT Broker not configured";
  }
  else if (MQTT_Port == "") {
    return "Failed - MQTT Port not configured";
  }
  else if (MQTT_Username == "") {
    return "Failed - MQTT Username not configured";
  }
  else if (MQTT_Password == "") {
    return "Failed - MQTT Password not configured";
  }
  else if (System_Header == "") {
    return "Failed - System Header not configured";
  }

  return "Passed";
}

// #################################### FS_Config_Save() ####################################
void FS_Config_Drop() {

  // Create json string to store base config
  const size_t bufferSize = JSON_ARRAY_SIZE(9) + 60;
  DynamicJsonBuffer jsonBuffer(bufferSize);
  JsonObject& root = jsonBuffer.createObject();

  // Generate json
  root.set("Hostname", Hostname);
  root.set("System_Header", System_Header);
  root.set("System_Sub_Header", System_Sub_Header);
  root.set("WiFi_SSID", WiFi_SSID);
  root.set("WiFi_Password", WiFi_Password);
  root.set("MQTT_Broker", MQTT_Broker);
  root.set("MQTT_Port", MQTT_Port);
  root.set("MQTT_Username", MQTT_Username);
  root.set("MQTT_Password", MQTT_Password);
  root.set("MQTT_Allow_Flash_Password", MQTT_Allow_Flash_Password);
  root.set("Config_ID", Config_ID);

  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");
  if (!configFile) {
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file for writing");
    return;
  }

  root.printTo(configFile);
  configFile.close();

  Log(MQTT_Topic[Topic_System] + "/FSConfig", "Config droped clean config saved to SPIFFS");

  return;
}


// ############################################################ FS_Config() ############################################################
bool FS_Config_Load() {

  Log(MQTT_Topic[Topic_System] + "/Dobby", "Loading FS Config");

  // Open file
  File configFile = SPIFFS.open(FS_Confing_File_Name, "r");

  // File check
  if (!configFile) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file");
    configFile.close();
    return false;
  }

  size_t size = configFile.size();
  if (size > Config_Json_Max_Buffer_Size) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Config file size is too large");
    configFile.close();
    return false;
  }

  // Parrse json
  DynamicJsonBuffer jsonBuffer(size + 100);
  JsonObject& root = jsonBuffer.parseObject(configFile);

  // Close file
  configFile.close();

  // FIX ADD error handling below

  // Load config into variables
  // ############### System ###############
  Hostname = root.get<String>("Hostname");
  System_Header = root.get<String>("System_Header");
  System_Sub_Header = root.get<String>("System_Sub_Header");
  Config_ID = root.get<String>("Config_ID");
  Rebuild_MQTT_Topics();

  WiFi_SSID = root.get<String>("WiFi_SSID");
  WiFi_Password = root.get<String>("WiFi_Password");
  MQTT_Broker = root.get<String>("MQTT_Broker");
  MQTT_Port = root.get<String>("MQTT_Port");
  MQTT_Username = root.get<String>("MQTT_Username");
  MQTT_Password = root.get<String>("MQTT_Password");
  MQTT_Allow_Flash_Password = root.get<String>("MQTT_Allow_Flash_Password");

  // Remember to convert to sec to ms
  MQTT_KeepAlive_Interval = root.get<unsigned long>("MQTT_KeepAlive_Interval") * 1000;
  MQTT_KeepAlive_Ticker.detach();
  MQTT_KeepAlive_Ticker.attach_ms(MQTT_KeepAlive_Interval, MQTT_KeepAlive);

  // // ############### Buzzer ###############
  if (root.get<String>("Buzzer_Pins") != "") {
    Buzzer_Pins = root.get<byte>("Buzzer_Pins");
    if (Pin_Monitor(Reserve_Normal, Buzzer_Pins) == Pin_Free) {
      pinMode(Buzzer_Pins, OUTPUT);
      MQTT_Subscribe(MQTT_Topic[Topic_Buzzer], true, NONE);
      Buzzer_Configured = true;
    }
  }

  // ############### DHT ###############
  if (root.get<String>("DHT_Pins") != "") {
    // Fill variables
    Log(MQTT_Topic[Topic_System] + "/Distance", "Configuring");
    MQTT_Settings_Set(DHT_Pins, DHT_Max_Number_Of, root.get<String>("DHT_Pins"), MQTT_Topic[Topic_System] + "/DHT", "DHT Pins");

    // Check pins
    for (byte i = 0; i < DHT_Max_Number_Of; i++) {
      if (DHT_Pins[i] != 255 && Pin_Monitor(Reserve_Normal, DHT_Pins[i]) == Pin_Free) {
        // Subscribe
        MQTT_Subscribe(MQTT_Topic[Topic_DHT], true, PLUS);
        // Enable configuration
        DHT_Configured = true;
      }
    }
    Log(MQTT_Topic[Topic_System] + "/Distance", "Configuration compleate");
  }


  // ############### Relay ###############
  if (root.get<String>("Relay_On_State") != "") {
    Relay_On_State = root.get<bool>("Relay_On_State");

    // Relay pins
    MQTT_Settings_Set(Relay_Pins, Relay_Max_Number_Of, root.get<String>("Relay_Pins"), MQTT_Topic[Topic_System] + "/Relay", "Relay Pins");
    for (byte i = 0; i < Relay_Max_Number_Of; i++) {
      if (Relay_Pins[i] != 255 && Pin_Monitor(Reserve_Normal, Relay_Pins[i]) == Pin_Free) {
        pinMode(Relay_Pins[i], OUTPUT);
        digitalWrite(Relay_Pins[i], !Relay_On_State);
      }
    }

    MQTT_Settings_Set(Relay_Pin_Auto_Off, Relay_Max_Number_Of, root.get<String>("Relay_Pin_Auto_Off"), MQTT_Topic[Topic_System] + "/Relay", "Relay Pins Auto Off");
    MQTT_Settings_Set(Relay_Pin_Auto_Off_Delay, Relay_Max_Number_Of, root.get<String>("Relay_Pin_Auto_Off_Delay"), MQTT_Topic[Topic_System] + "/Relay", "Relay Pins Auto Off Delay");


    MQTT_Subscribe(MQTT_Topic[Topic_Relay], true, PLUS);
    Relay_Configured = true;
  }


  // ############### Distance ###############
  // FIX - Pretty up below
  if (root.get<String>("Distance_Pins_Trigger") != "") {
    Log(MQTT_Topic[Topic_System] + "/Distance", "Configuring");
    MQTT_Settings_Set(Distance_Pins_Trigger, Distance_Max_Number_Of, root.get<String>("Distance_Pins_Trigger"), MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Trigger");
    // Set pinMode
    for (byte i = 0; i < Distance_Max_Number_Of; i++) {
      if (Distance_Pins_Trigger[i] != 255 && Pin_Monitor(Reserve_Normal, Distance_Pins_Trigger[i]) == Pin_Free) {
        pinMode(Distance_Pins_Trigger[i], OUTPUT);
        Distance_Configured = true;
      }
    }

    if (root.get<String>("Distance_Pins_Echo") != "") {
      MQTT_Settings_Set(Distance_Pins_Echo, Distance_Max_Number_Of, root.get<String>("Distance_Pins_Echo"), MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Echo");
      // Set pinMode
      for (byte i = 0; i < Distance_Max_Number_Of; i++) {
        if (Distance_Pins_Echo[i] != 255 && Pin_Monitor(Reserve_Normal, Distance_Pins_Echo[i]) == Pin_Free) {
          pinMode(Distance_Pins_Echo[i], INPUT);
        }
      }
    }

    if (root.get<String>("Distance_Trigger_At") != "") {
      MQTT_Settings_Set(Distance_Trigger_At, Distance_Max_Number_Of, root.get<String>("Distance_Trigger_At"), MQTT_Topic[Topic_System] + "/Distance", "Distance Trigger At");
    }
    if (root.get<String>("Distance_Target_ON") != "") {
      MQTT_Settings_Set(Distance_Target_ON, Distance_Max_Number_Of, root.get<String>("Distance_Target_ON"), MQTT_Topic[Topic_System] + "/Distance", "Distance Target ON");
    }
    if (root.get<String>("Distance_Target_OFF") != "") {
      MQTT_Settings_Set(Distance_Target_OFF, Distance_Max_Number_Of, root.get<String>("Distance_Target_OFF"), MQTT_Topic[Topic_System] + "/Distance", "Distance Target OFF");
    }
    if (root.get<String>("Distance_Refresh_Rate") != "") {
      MQTT_Settings_Set(Distance_Refresh_Rate, Distance_Max_Number_Of, root.get<String>("Distance_Refresh_Rate"), MQTT_Topic[Topic_System] + "/Distance", "Distance Refresh Rate");
    }
    if (root.get<String>("Distance_Auto_OFF_Delay") != "") {
      MQTT_Settings_Set(Distance_Auto_OFF_Delay, Distance_Max_Number_Of, root.get<String>("Distance_Auto_OFF_Delay"), MQTT_Topic[Topic_System] + "/Distance", "Distance Auto OFF Delay");
    }
    if (root.get<String>("Distance_Auto_OFF_Active") != "") {
      MQTT_Settings_Set(Distance_Auto_OFF_Active, Distance_Max_Number_Of, root.get<String>("Distance_Auto_OFF_Active"), MQTT_Topic[Topic_System] + "/Distance", "Distance Auto OFF Active");
    }

    // Atach the ticket to start reading the distance sensor
    Distance_Refresh_Ticker.attach_ms(Distance_Read_Rate, Distance_Loop);

    // Subscribe to topic
    MQTT_Subscribe(MQTT_Topic[Topic_Distance], true, PLUS);
    Log(MQTT_Topic[Topic_System] + "/Distance", "Configuration compleate");
  }

  // ############### Dimmer ###############
  if (root.get<String>("Dimmer_Pins") != "") {
    MQTT_Subscribe(MQTT_Topic[Topic_Dimmer], true, PLUS);
    MQTT_Settings_Set(Dimmer_Pins, Dimmer_Max_Number_Of, root.get<String>("Dimmer_Pins"), MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Pins");
    // Set pinMode
    for (byte i = 0; i < Dimmer_Max_Number_Of; i++) {
      if (Dimmer_Pins[i] != 255) {
        if (Pin_Monitor(Reserve_Normal, Dimmer_Pins[i]) == Pin_Free) {
          pinMode(Dimmer_Pins[i], OUTPUT);
          analogWrite(Dimmer_Pins[i], 0);
          Dimmer_State[i] = 0;
          Dimmer_Configured = true;
        }
      }
    }
  }


  // ############### Load_Cell ###############
  // if (root.get<String>("LoadCell_Pins_DT") != "") {
  //
  //   Log(MQTT_Topic[Topic_System] + "/LoadCell", "Configuring");
  //
  //   Log(MQTT_Topic[Topic_System] + "/LoadCell", "Setting DT Pins variables");
  //   MQTT_Settings_Set(LoadCell_Pins_DT, Load_Cell_Max_Number_Of, root.get<String>("LoadCell_Pins_DT"), MQTT_Topic[Topic_System] + "/LoadCell", "LoadCell DT Pins");
  //
  //   Log(MQTT_Topic[Topic_System] + "/LoadCell", "Setting SCK Pins variables");
  //   if (root.get<String>("LoadCell_Pins_SCK") != "") {
  //     MQTT_Settings_Set(LoadCell_Pins_SCK, Load_Cell_Max_Number_Of, root.get<String>("LoadCell_Pins_SCK"), MQTT_Topic[Topic_System] + "/LoadCell", "LoadCell SCK Pins");
  //   }
  //
  //   Log(MQTT_Topic[Topic_System] + "/LoadCell", "Setting Calibration variables");
  //   if (root.get<String>("LoadCell_Calibration") != "") {
  //     MQTT_Settings_Set(LoadCell_Calibration, Load_Cell_Max_Number_Of, root.get<String>("LoadCell_Calibration"), MQTT_Topic[Topic_System] + "/LoadCell", "LoadCell Calibration");
  //   }
  //
  //
  //   // Setup the LoadCell if both pins is configured
  //   for (byte i = 0; i < Load_Cell_Max_Number_Of; i++) {
  //     if (LoadCell_Pins_DT[i] != 255 && LoadCell_Pins_SCK[i] != 255 && LoadCell_Calibration[i] != -1337) {
  //       Log(MQTT_Topic[Topic_System] + "/LoadCell", "Setting up Scale: " + String(i + 1));
  //
  //       // Reserve pins
  //       if (Pin_Monitor(Reserve_Normal, LoadCell_Pins_DT[i]) != Pin_Free) {
  //         Log(MQTT_Topic[Topic_Log_Error] + "/LoadCell", "Pin: " + Number_To_Pin(LoadCell_Pins_DT[i]) + " usd for DT not free disabling Scale: " + String(i + 1));
  //         continue;
  //       }
  //       else if (Pin_Monitor(Reserve_Normal, LoadCell_Pins_SCK[i]) != Pin_Free) {
  //         Log(MQTT_Topic[Topic_Log_Error] + "/LoadCell", "Pin: " + Number_To_Pin(LoadCell_Pins_DT[i]) + " used for SCL not free disabling Scale: " + String(i + 1));
  //         continue;
  //       }
  //
  //       // DT Warningss
  //       if (LoadCell_Pins_DT[i] == Pin_To_Number("D3")) {
  //         Log(MQTT_Topic[Topic_Log_Warning] + "/LoadCell", "If DT is not connected to D3 during boot it will cause a reboot loop");
  //       }
  //       else if (LoadCell_Pins_DT[i] == Pin_To_Number("D5")) {
  //         Log(MQTT_Topic[Topic_Log_Warning] + "/LoadCell", "If DT is not connected to D5 during boot it will cause a reboot loop");
  //       }
  //       else if (LoadCell_Pins_DT[i] == Pin_To_Number("D7")) {
  //         Log(MQTT_Topic[Topic_Log_Warning] + "/LoadCell", "If DT is not connected to D7 during boot it will cause a reboot loop");
  //       }
  //       // SCK Warningss
  //       if (LoadCell_Pins_SCK[i] == Pin_To_Number("D3")) {
  //         Log(MQTT_Topic[Topic_Log_Warning] + "/LoadCell", "If SCK is not connected to D3 during boot it will cause a reboot loop");
  //       }
  //
  //       MQTT_Subscribe(MQTT_Topic[Topic_LoadCell], true, PLUS);
  //
  //       // Log event
  //       Log(MQTT_Topic[Topic_System] + "/LoadCell", "Starting Scale: " + String(i + 1) + " on pin DT: " + Number_To_Pin(LoadCell_Pins_DT[i]) + " SCK: " + Number_To_Pin(LoadCell_Pins_SCK[i]));
  //
  //       // Enable Scales
  //       // NOTE: Do not tare during setup til will cause a reboot loop
  //       if (i == 0) {
  //         // Set Calibration
  //         // this value is obtained by calibrating the scale with known weights
  //         Load_Cell1.set_scale(LoadCell_Calibration[i]);
  //         // Start the scale
  //         Load_Cell1.begin(LoadCell_Pins_DT[i], LoadCell_Pins_SCK[i]);
  //         // Enable Configuration
  //         Load_Cell_Configurated[i] = true;
  //         // Atach the ticket to start reading the distance sensor
  //         LoadCell_Refresh_Ticker.attach_ms(LoadCell_Read_Rate, LoadCell_Loop);
  //       }
  //       else if (i == 1) {
  //         // Set Calibration
  //         // this value is obtained by calibrating the scale with known weights
  //         Load_Cell2.set_scale(LoadCell_Calibration[i]);
  //         // Start the scale
  //         Load_Cell2.begin(LoadCell_Pins_DT[i], LoadCell_Pins_SCK[i]);
  //         // Enable Configuration
  //         Load_Cell_Configurated[i] = true;
  //       }
  //       else if (i == 2) {
  //         // Set Calibration
  //         // this value is obtained by calibrating the scale with known weights
  //         Load_Cell3.set_scale(LoadCell_Calibration[i]);
  //         // Start the scale
  //         Load_Cell3.begin(LoadCell_Pins_DT[i], LoadCell_Pins_SCK[i]);
  //         // Enable Configuration
  //         Load_Cell_Configurated[i] = true;
  //       }
  //       else if (i == 3) {
  //         // Set Calibration
  //         // this value is obtained by calibrating the scale with known weights
  //         Load_Cell4.set_scale(LoadCell_Calibration[i]);
  //         // Start the scale
  //         Load_Cell4.begin(LoadCell_Pins_DT[i], LoadCell_Pins_SCK[i]);
  //         // Enable Configuration
  //         Load_Cell_Configurated[i] = true;
  //       }
  //
  //
  //     }
  //     else {
  //       if (LoadCell_Pins_SCK[i] != 255 && LoadCell_Calibration[i] != -1337) {
  //         Log(MQTT_Topic[Topic_Log_Error] + "/LoadCell", "Failed to setup Scale: " + String(i + 1) + " Missing: LoadCell_Pins_DT");
  //       }
  //       else if (LoadCell_Pins_DT[i] != 255 && LoadCell_Pins_SCK[i] != 255) {
  //         Log(MQTT_Topic[Topic_Log_Error] + "/LoadCell", "Failed to setup Scale: " + String(i + 1) + " Missing: LoadCell_Calibration");
  //       }
  //       else if (LoadCell_Pins_DT[i] != 255 && LoadCell_Calibration[i] != -1337) {
  //         Log(MQTT_Topic[Topic_Log_Error] + "/LoadCell", "Failed to setup Scale: " + String(i + 1) + " Missing: LoadCell_Pins_SCK");
  //       }
  //     }
  //   }
  //   Log(MQTT_Topic[Topic_System] + "/LoadCell", "Configuration compleate");
  // }


  // ############### DC_Voltmeter ###############
  if (root.get<String>("DC_Voltmeter_Pins") != "") {
    DC_Voltmeter_Pins = Pin_To_Number(root.get<String>("DC_Voltmeter_Pins"));

    // Check to see if pin is free
    if (Pin_Monitor(Reserve_Normal, DC_Voltmeter_Pins) == Pin_Free) {
      pinMode(DC_Voltmeter_Pins, INPUT);
      MQTT_Subscribe(MQTT_Topic[Topic_DC_Voltmeter], true, NONE);
    }
  }

  if (root.get<String>("DC_Voltmeter_R1") != "") {
    DC_Voltmeter_R1 = root.get<float>("DC_Voltmeter_R1");
  }

  if (root.get<String>("DC_Voltmeter_R2") != "") {
    DC_Voltmeter_R2 = root.get<float>("DC_Voltmeter_R2");
  }

  if (root.get<String>("DC_Voltmeter_Curcit_Voltage") != "") {
    DC_Voltmeter_Curcit_Voltage = root.get<float>("DC_Voltmeter_Curcit_Voltage");
  }

  if (root.get<String>("DC_Voltmeter_Offset") != "") {
    DC_Voltmeter_Offset = root.get<float>("DC_Voltmeter_Offset");
  }


  // ############### Button ###############
  if (root.get<String>("Button_Pins") != "") {
    // MQTT_Subscribe(MQTT_Topic[Topic_Button], true, PLUS);
    MQTT_Settings_Set(Button_Pins, Button_Max_Number_Of, root.get<String>("Button_Pins"), MQTT_Topic[Topic_System] + "/Button", "Button Pins");
    Button_Configured = true;
    // Set pinMode
    for (byte i = 0; i < Button_Max_Number_Of; i++) {
      if (Button_Pins[i] != 255) {
        if (Pin_Monitor(Reserve_Normal, Button_Pins[i]) == Pin_Free) {
          pinMode(Button_Pins[i], INPUT_PULLUP);
        }
      }
    }
  }

  if (root.get<String>("Button_Target") != "") {
    MQTT_Settings_Set(Button_Target, Button_Max_Number_Of, root.get<String>("Button_Target"), MQTT_Topic[Topic_System] + "/Button", "Button Target");
  }


  // ############### Switch ###############
  if (root.get<String>("Switch_Pins") != "") {
    MQTT_Subscribe(MQTT_Topic[Topic_Switch], true, PLUS);
    MQTT_Settings_Set(Switch_Pins, Switch_Max_Number_Of, root.get<String>("Switch_Pins"), MQTT_Topic[Topic_System] + "/Switch", "Switch Pins");

    Switch_Configured = true;
    // Set pinMode
    for (byte i = 0; i < Switch_Max_Number_Of; i++) {
      if (Switch_Pins[i] != 255) {
        if (Pin_Monitor(Reserve_Normal, Switch_Pins[i]) == Pin_Free) {
          pinMode(Switch_Pins[i], INPUT_PULLUP);
          // Read current state
          Switch_Last_State[i] = digitalRead(Switch_Pins[i]);
        }
      }
    }

    if (root.get<String>("Switch_Target_ON") != "") {
      MQTT_Settings_Set(Switch_Target_ON, Switch_Max_Number_Of, root.get<String>("Switch_Target_ON"), MQTT_Topic[Topic_System] + "/Switch", "Switch Target ON");
    }

    if (root.get<String>("Switch_Target_OFF") != "") {
      MQTT_Settings_Set(Switch_Target_OFF, Switch_Max_Number_Of, root.get<String>("Switch_Target_OFF"), MQTT_Topic[Topic_System] + "/Switch", "Switch Target OFF");
    }
  }


  // ############### MPU6050 ###############
  // if (root.get<String>("MPU6050_Pin_SCL") != "") {
  //   Log(MQTT_Topic[Topic_System] + "/MPU6050", "Configuring");
  //   if (Pin_Monitor(Reserve_I2C_SCL, root.get<String>("MPU6050_Pin_SCL")) == Pin_SCL) {
  //     MPU6050_Pin_SCL = Pin_To_Number(root.get<String>("MPU6050_Pin_SCL"));
  //   }
  //   // Set SDA
  //   if (Pin_Monitor(Reserve_I2C_SDA, root.get<String>("MPU6050_Pin_SDA")) == Pin_SDA) {
  //     MPU6050_Pin_SDA = Pin_To_Number(root.get<String>("MPU6050_Pin_SDA"));
  //   }
  //   // Set Interrupt
  //   if (Pin_Monitor(Reserve_Normal, root.get<String>("MPU6050_Pin_Interrupt")) == Pin_Free) {
  //     MPU6050_Pin_Interrupt = Pin_To_Number(root.get<String>("MPU6050_Pin_Interrupt"));
  //   }
  //
  //   // Check needed pins
  //   if (MPU6050_Pin_SCL != 255 && MPU6050_Pin_SDA != 255 && MPU6050_Pin_Interrupt != 255) {
  //     Log(MQTT_Topic[Topic_System] + "/MPU6050", "All required pins set");
  //
  //     // Reserve pins
  //     if (MPU6050_Pin_SCL != 255 && MPU6050_Pin_SDA != 255 && MPU6050_Pin_Interrupt != 255) {
  //       // Set pinmode for Interrupt
  //       pinMode(MPU6050_Pin_Interrupt, INPUT);
  //
  //       Log(MQTT_Topic[Topic_System] + "/MPU6050", "Pins set to SDA: " + Number_To_Pin(MPU6050_Pin_SDA) + " SCL: " + Number_To_Pin(MPU6050_Pin_SCL) + " Interrupt: " + Number_To_Pin(MPU6050_Pin_Interrupt));
  //       MQTT_Subscribe(MQTT_Topic[Topic_MPU6050], true, PLUS);
  //       MPU6050_Configured = true;
  //     }
  //     // Report error
  //     else {
  //       Log(MQTT_Topic[Topic_Log_Error] + "/MPU6050", "Unable to set pins, SDA: " + Number_To_Pin(MPU6050_Pin_SDA) + " SCL: " + Number_To_Pin(MPU6050_Pin_SCL) + " Interrupt: " + Number_To_Pin(MPU6050_Pin_Interrupt));
  //     }
  //   }
  //
  //   // Report missing pin
  //   else {
  //     Log(MQTT_Topic[Topic_Log_Error] + "/MPU6050", "All required pins not set, got SDA: " + Number_To_Pin(MPU6050_Pin_SDA) + " SCL: " + Number_To_Pin(MPU6050_Pin_SCL) + " Interrupt: " + Number_To_Pin(MPU6050_Pin_Interrupt));
  //   }
  //
  //   Log(MQTT_Topic[Topic_System] + "/MPU6050", "Configuration compleate");
  // }

  // ############### BMP180 ###############
  if (root.get<String>("BMP180_Pin_SCL") != "") {
    Log(MQTT_Topic[Topic_System] + "/BMP180", "Configuring");

    // If pin D5, D6 is used then the BMP180 lib fails to init
    // FIX - Find out WTF
    if (Pin_Monitor(Check_State, "D5") != Pin_Free) {
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Pin D5 in use, this makes the BMP180 library fail");
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Disabling BMP180");
      BMP180_Configured = false;
    }
    else if (Pin_Monitor(Check_State, "D6") != Pin_Free) {
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Pin D6 in use, this makes the BMP180 library fail");
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Disabling BMP180");
      BMP180_Configured = false;
    }

    // Pin D5, D6 not used
    else {
      // Set SCL
      if (Pin_Monitor(Reserve_I2C_SCL, root.get<String>("BMP180_Pin_SCL")) == Pin_SCL) {
        BMP180_Pin_SCL = Pin_To_Number(root.get<String>("BMP180_Pin_SCL"));
      }
      // Set SDA
      if (Pin_Monitor(Reserve_I2C_SDA, root.get<String>("BMP180_Pin_SDA")) == Pin_SDA) {
        BMP180_Pin_SDA = Pin_To_Number(root.get<String>("BMP180_Pin_SDA"));
      }

      if (root.get<String>("BMP180_Altitude") != "") {
        BMP180_Altitude = root.get<float>("BMP180_Altitude");
      }

      // Check if requred configuration got done
      if (BMP180_Pin_SCL != 255 && BMP180_Pin_SDA != 255 && BMP180_Altitude != -1337.0) {
        // Log it all went ok
        Log(MQTT_Topic[Topic_System] + "/BMP180", "Pins SDA: " + Number_To_Pin(BMP180_Pin_SDA) + " SCL: " + Number_To_Pin(BMP180_Pin_SCL) + " Altiture: " + String(BMP180_Altitude));
        // Subscripbe to topic
        MQTT_Subscribe(MQTT_Topic[Topic_BMP180], true, NONE);

        // Clear Runnins Averidge
        BMP180_RA_Current_Pressure.clear();

        BMP180_Configured = true;
      }
      else {
        String Log_Text;

        if (BMP180_Pin_SCL == 255) {
          Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "BMP180_Pin_SCL not set");
        }
        if (BMP180_Pin_SDA == 255) {
          Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "BMP180_Pin_SDA not set");
        }
        if (BMP180_Altitude == -1337.0) {
          Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "BMP180_Altitude not set");
        }

        Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Disabling BMP180");
      }
    }

    Log(MQTT_Topic[Topic_System] + "/BMP180", "Configuration compleate");
  }


  // ############### MQ2 ###############
  if (root.get<String>("MQ2_Pin_A0") != "") {
    Log(MQTT_Topic[Topic_System] + "/MQ2", "Configuring");

    // Check if pin is free
    if (Pin_Monitor(Reserve_Normal, root.get<String>("MQ2_Pin_A0")) == Pin_Free) {
        // Set variable
        MQ2_Pin_A0 = Pin_To_Number(root.get<String>("MQ2_Pin_A0"));
        // Set pinmode
        pinMode(MQ2_Pin_A0, INPUT);
        // Subscribe to topic
        MQTT_Subscribe(MQTT_Topic[Topic_MQ2], true, NONE);
        // Set configured to true
        MQ2_Configured = true;
        // Read once to set Min/Max referance
        MQ2_Loop();
        // Set min max to current
        MQ2_Value_Min = MQ2_Current_Value;
        MQ2_Value_Max = MQ2_Current_Value;
        // Start ticker
        MQ2_Ticker.attach_ms(MQ2_Refresh_Rate, MQ2_Loop);
        // Log configuration compleate
        Log(MQTT_Topic[Topic_MQ2] + "/MQ2", "Configuration compleate");
      }
      else {
        Log(MQTT_Topic[Topic_Log_Error] + "/MQ2", "Configuration failed pin in use");
      }
  }

  // ############### MFRC522 - RFID ###############
  // if (root.get<String>("MFRC522_Pins") != "") {
  //   Log(MQTT_Topic[Topic_System] + "/RFID", "Configuring");
  //
  //   MQTT_Settings_Set(MFRC522_Pins, MFRC522_Max_Number_Of, root.get<String>("MFRC522_Pins"), MQTT_Topic[Topic_System] + "/RFID", "MFRD522 (RFID) Pins");
  //
  //   bool Missing_Pins = false;
  //
  //   // Reserve pins
  //   for (byte i = 0; i < MFRC522_Max_Number_Of; i++) {
  //     if (MFRC522_Pins[i] == 255) {
  //       Missing_Pins = true;
  //       break;
  //     }
  //     if (Pin_Monitor(Reserve_Normal, MFRC522_Pins[i]) == Pin_Free) {
  //
  //     }
  //   }

    // Check if all needed pins is set
    // All pins set
  //   if (Missing_Pins == false) {
  //     SPI.begin();	         // Init SPI bus
  //     MFRC522_RFID.PCD_Init(MFRC522_Pins[1], MFRC522_Pins[0]);    // Init MFRC522
  //     // Connection check
  //     // Connection failed
  //     if (MFRC522_RFID.PCD_PerformSelfTest() == true) {
  //       // No need to subscribe i think
  //       // MQTT_Subscribe(MQTT_Topic[Topic_RFID], true, NONE);
  //       // Enable config
  //       MFRC522_Configured = true;
  //       // Log event
  //       Log(MQTT_Topic[Topic_System] + "/RFID", "Selftest: Passed");
  //     }
  //     // Device connected
  //     else {
  //       Log(MQTT_Topic[Topic_Log_Error] + "/RFID", "Selftest: Failed - Disabling RFID");
  //     }
  //   }
  //   // Missing pins
  //   else {
  //     Log(MQTT_Topic[Topic_Log_Error] + "/RFID", "All required pins not set, got RST:" + Number_To_Pin(MFRC522_Pin_RST) + "SS:" + Number_To_Pin(MFRC522_Pin_SS) + "MOSI:" + Number_To_Pin(MFRC522_Pin_MOSI) + "MIOS:" + Number_To_Pin(MFRC522_Pin_MIOS) + "SCK:" + Number_To_Pin(MFRC522_Pin_SCK));
  //   }
  //
  //   Log(MQTT_Topic[Topic_System] + "/RFID", "Configuration compleate");
  // }

  // ############### PIR ###############
  if (root.get<String>("PIR_Pins") != "") {
    Log(MQTT_Topic[Topic_System] + "/PIR", "Configuring PIR");

    // Set pin variables
    MQTT_Settings_Set(PIR_Pins, PIR_Max_Number_Of, root.get<String>("PIR_Pins"), MQTT_Topic[Topic_System] + "/PIR", "PIR Pins");

    // Set Target ON variables
    if (root.get<String>("PIR_Topic") != "") {
      MQTT_Settings_Set(PIR_Topic, PIR_Max_Number_Of, root.get<String>("PIR_Topic"), MQTT_Topic[Topic_System] + "/PIR", "PIR ON Topic");
    }

    if (root.get<String>("PIR_OFF_Payload") != "") {
      MQTT_Settings_Set(PIR_OFF_Payload, PIR_Max_Number_Of, root.get<String>("PIR_OFF_Payload"), MQTT_Topic[Topic_System] + "/PIR", "PIR OFF Payload");
    }
    if (root.get<String>("PIR_ON_Payload_1") != "") {
      MQTT_Settings_Set(PIR_ON_Payload[0], PIR_Max_Number_Of, root.get<String>("PIR_ON_Payload_1"), MQTT_Topic[Topic_System] + "/PIR", "PIR ON Payload State 1");
    }
    if (root.get<String>("PIR_ON_Payload_2") != "") {
      MQTT_Settings_Set(PIR_ON_Payload[1], PIR_Max_Number_Of, root.get<String>("PIR_ON_Payload_2"), MQTT_Topic[Topic_System] + "/PIR", "PIR ON Payload State 2");
    }
    if (root.get<String>("PIR_ON_Payload_3") != "") {
      MQTT_Settings_Set(PIR_ON_Payload[2], PIR_Max_Number_Of, root.get<String>("PIR_ON_Payload_3"), MQTT_Topic[Topic_System] + "/PIR", "PIR ON Payload State 3");
    }

    // Set OFF Delay variables
    if (root.get<String>("PIR_OFF_Delay") != "") {
      MQTT_Settings_Set(PIR_OFF_Delay, PIR_Max_Number_Of, root.get<String>("PIR_OFF_Delay"), MQTT_Topic[Topic_System] + "/PIR", "PIR OFF Delay");
    }

    // Set pinMode
    for (byte i = 0; i < PIR_Max_Number_Of; i++) {
      if (PIR_Pins[i] != 255 && PIR_Topic[i] != "" && PIR_ON_Payload[0][i] != "" && PIR_OFF_Payload[i] != "" && PIR_OFF_Delay[i] != 0) {
        if (Pin_Monitor(Reserve_Normal, PIR_Pins[i]) == Pin_Free) {
          pinMode(Switch_Pins[i], INPUT);
        }
      }
      // Flash indicator LED if configured to indicate wormup
      if (Indicator_LED_Configured == true) Indicator_LED(LED_PIR, true);

      // Subscrib to topic
      MQTT_Subscribe(MQTT_Topic[Topic_PIR], true, PLUS);
      // Enable Configuration
      PIR_Configured = true;
    }
  }

  // ############### LDR ###############
  if (root.get<String>("LDR_Pin_A0") != "") {
    Log(MQTT_Topic[Topic_System] + "/LDR", "Configuring");

    if (root.get<String>("LDR_Target_Topic") != "") {
      LDR_Target_Topic = root.get<String>("LDR_Target_Topic");
    }

    if (root.get<String>("LDR_Dark_At") != "") {
      LDR_Dark_At = root.get<int>("LDR_Dark_At");
    }

    if (LDR_Target_Topic == "" || LDR_Dark_At == -1) {
      Log(MQTT_Topic[Topic_Log_Error] + "/LDR", "Disabling Dobby PIR missing setting got. LDR_Target_Topic: " + String(LDR_Target_Topic) + " LDR_Dark_At: " + String(LDR_Dark_At));
      LDR_Target_Topic = "";
      LDR_Dark_At = -1;
    }


    // Check if pin is free
    if (Pin_Monitor(Reserve_Normal, root.get<String>("LDR_Pin_A0")) == Pin_Free) {
      // Set variable
      LDR_Pin_A0 = Pin_To_Number(root.get<String>("LDR_Pin_A0"));
      // Set pinmode
      pinMode(LDR_Pin_A0, INPUT);
      // Subscribe to topic
      MQTT_Subscribe(MQTT_Topic[Topic_LDR], true, NONE);
      // Set configured to true
      LDR_Configured = true;
      // Read once to set Min/Max referance
      LDR_Current_Value = analogRead(LDR_Pin_A0);
      // // Check min/max
      LDR_Value_Min = LDR_Current_Value;
      LDR_Value_Max = LDR_Current_Value;
      // Start ticker
      LDR_Ticker.attach_ms(LDR_Refresh_Rate, LDR_Loop);
      // Log configuration compleate
      Log(MQTT_Topic[Topic_LDR] + "/LDR", "Configuration compleate");
    }
    else {
      Log(MQTT_Topic[Topic_Log_Error] + "/LDR", "Configuration failed pin in use");
    }
  }

  return true;
}


// ############################################################ Serial_CLI_Command_Check() ############################################################
void Serial_CLI_Command_Check() {

  if (CLI_Command_Complate == false) {
    return;
  }

  CLI_Input_String.toLowerCase();

  // WiFi
  if (CLI_Input_String == "wifi ssid") {
    Wait_For_Serial_Input("wifi ssid");
    WiFi_SSID = CLI_Input_String;
    Serial.println("wifi ssid set to: " + WiFi_SSID);

  }
  else if (CLI_Input_String == "wifi password") {
    Wait_For_Serial_Input("wifi password");
    WiFi_Password = CLI_Input_String;
    Serial.println("wifi password set to: " + WiFi_Password);
  }

  // MQTT
  else if (CLI_Input_String == "mqtt broker") {
    Wait_For_Serial_Input("mqtt broker");
    MQTT_Broker = CLI_Input_String;
    Serial.println("mqtt broker set to: " + MQTT_Broker);
  }
  else if (CLI_Input_String == "mqtt port") {
    Wait_For_Serial_Input("mqtt port");
    MQTT_Port = CLI_Input_String;
    Serial.println("mqtt port set to: " + MQTT_Port);
  }
  else if (CLI_Input_String == "mqtt user") {
    Wait_For_Serial_Input("mqtt user");
    MQTT_Username = CLI_Input_String;
    Serial.println("mqtt user set to: " + MQTT_Username);
  }
  else if (CLI_Input_String == "mqtt password") {
    Wait_For_Serial_Input("mqtt password");
    MQTT_Password = CLI_Input_String;
    Serial.println("mqtt password set to: " + MQTT_Password);
  }
  else if (CLI_Input_String == "system header") {
    Wait_For_Serial_Input("system header");
    System_Header = CLI_Input_String;
    Serial.println("system header set to: " + System_Header);
  }
  else if (CLI_Input_String == "system sub header") {
    Wait_For_Serial_Input("system sub header");
    System_Sub_Header = CLI_Input_String;
    Serial.println("system sub header set to: " + System_Sub_Header);
  }

  // JSON Config
  else if (CLI_Input_String == "json") {
    Wait_For_Serial_Input("json config string");

    DynamicJsonBuffer jsonBuffer(CLI_Input_String.length() + 100);
    JsonObject& root_CLI = jsonBuffer.parseObject(CLI_Input_String);

    if (root_CLI.containsKey("Hostname")) Hostname = root_CLI.get<String>("Hostname");
    if (root_CLI.containsKey("WiFi_SSID")) WiFi_SSID = root_CLI.get<String>("WiFi_SSID");
    if (root_CLI.containsKey("WiFi_Password")) WiFi_Password = root_CLI.get<String>("WiFi_Password");
    if (root_CLI.containsKey("MQTT_Broker")) MQTT_Broker = root_CLI.get<String>("MQTT_Broker");
    if (root_CLI.containsKey("MQTT_Port")) MQTT_Port = root_CLI.get<unsigned long>("MQTT_Port");
    if (root_CLI.containsKey("MQTT_Username")) MQTT_Username = root_CLI.get<String>("MQTT_Username");
    if (root_CLI.containsKey("MQTT_Password")) MQTT_Password = root_CLI.get<String>("MQTT_Password");
    if (root_CLI.containsKey("System_Header")) System_Header = root_CLI.get<String>("System_Header");
    if (root_CLI.containsKey("System_Sub_Header")) System_Sub_Header = root_CLI.get<String>("System_Sub_Header");
  }

  // Misc
  else if (CLI_Input_String == "hostname") {
    Wait_For_Serial_Input("hostname");
    Hostname = CLI_Input_String;
  }

  else if (CLI_Input_String == "help") {

    Serial.println("Avalible commands:");
    Serial.println("");

    for (int i = 0; i < Command_List_Length; i++) {
      Serial.println("\t" + String(Commands_List[i]));
      Serial.flush();
    }
  }

  else if (CLI_Input_String == "save" || CLI_Input_String == "write") {

    if (CLI_Config_Check() != "Passed") {
      Serial.println("\tConfig check failed, please run 'check' for details");
      Serial.println("\tConfiguration NOT saved to FS");
    }

    else {
      FS_Config_Save();

      Serial.println("Config saved to FS");
    }
  }

  else if (CLI_Input_String == "list") {
    Serial.println("");
    Serial.println("Settings List:");
    Serial.println("\t" + String(Commands_List[0]) + ": " + Hostname);
    Serial.println("\t" + String(Commands_List[1]) + ": " + WiFi_SSID);
    Serial.println("\t" + String(Commands_List[2]) + ": " + WiFi_Password);
    Serial.println("\t" + String(Commands_List[3]) + ": " + MQTT_Broker);
    Serial.println("\t" + String(Commands_List[4]) + ": " + MQTT_Port);
    Serial.println("\t" + String(Commands_List[5]) + ": " + MQTT_Username);
    Serial.println("\t" + String(Commands_List[6]) + ": " + MQTT_Password);
    Serial.println("\t" + String(Commands_List[7]) + ": " + System_Header);
    Serial.println("\t" + String(Commands_List[8]) + ": " + System_Sub_Header);
    Serial.flush();
  }


  else if (CLI_Input_String == "fs list") {
    String str = "";
    Dir dir = SPIFFS.openDir("/");
    while (dir.next()) {
      str += "\t";
      str += dir.fileName();
      str += " / ";
      str += dir.fileSize();
      str += "\r\n";
    }
    Serial.println("");
    Serial.println("\tFS File List:");
    Serial.println(str);
  }

  else if (CLI_Input_String == "fs cat") {
    Wait_For_Serial_Input("file name");
    String File_Path = CLI_Input_String;

    if (SPIFFS.exists(File_Path)) {

      File f = SPIFFS.open(File_Path, "r");
      if (f && f.size()) {

        String cat_String;

        while (f.available()){
          cat_String += char(f.read());
        }

        f.close();

        Serial.println("");
        Serial.println("cat " + File_Path + ":");
        Serial.print(cat_String);
      }
    }
  }

  else if (CLI_Input_String == "fs config load") {
    FS_Config_Load();
  }

  else if (CLI_Input_String == "fs config drop") {
    FS_Config_Drop();
  }

  else if (CLI_Input_String == "fs format") {
    FS_Format();
  }

  else if (CLI_Input_String == "check") {
    Serial.println("Config Check: " + CLI_Config_Check());
  }

  else if (CLI_Input_String == "reboot") {
    Serial.println("");
    for (byte i = 3; i > 0; i--) {
      Serial.printf("\tRebooting in: %i\r", i);
      delay(1000);
    }
    Log(MQTT_Topic[Topic_System], "Rebooting");

    delay(500);
    ESP.restart();
  }

  else if (CLI_Input_String == "shutdown") {
    Serial.println("");
    for (byte i = 3; i > 0; i--) {
      Serial.printf("\tShutting down in: %i\r", i);
      delay(1000);
    }
    Log(MQTT_Topic[Topic_System], "Shutdown, bye bye :-(");

    delay(500);
    ESP.deepSleep(0);
  }

  else if (CLI_Input_String == "show mac") {
    Serial.println("MAC Address: " + WiFi.macAddress());
  }

  else {
    if (CLI_Input_String != "") Log(MQTT_Topic[Topic_System] + "/CLI", "Unknown command: " + CLI_Input_String);
  }

  if (CLI_Input_String != "") CLI_Print("");
  CLI_Input_String = "";
  CLI_Command_Complate = false;
}


// ############################################################ Serial_CLI() ############################################################
void Serial_CLI() {

  if (Indicator_LED_Configured == true) Indicator_LED(LED_Config, true);

  Serial.println("");
  Serial.println("");
  if (CLI_Config_Check() != "Passed") Serial.println("Device not configured please do so, type help to list avalible commands");
  else Serial.println("############################## SERIAL CLI ##############################");
  CLI_Print("");

  // Eternal loop for Serial CLi
  while (true) {
    Get_Serial_Input();
    Serial_CLI_Command_Check();
    delay(1);
  }
}


// ############################################################ Serial_CLI_Boot_Message() ############################################################
void Serial_CLI_Boot_Message(unsigned int Timeout) {
  for (byte i = Timeout; i > 0; i--) {
    Serial.printf("\tPress any key to enter Serial CLI, timeout in: %i \r", i);
    delay(1000);
    if (Get_Serial_Input() == true) {
      Serial_CLI();
    }
  }
  byte i = 0;
  Serial.printf("\tPress any key to enter Serial CLI, timeout in: %i \r", i);
  Serial.println("");
}


// #################################### FS_Config_Show() ####################################
void FS_Config_Show() {
  String Payload;

  File configFile = SPIFFS.open(FS_Confing_File_Name, "r");

  if (!configFile) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file");
    configFile.close();
    return;
  }

  size_t size = configFile.size();
  if (size > Config_Json_Max_Buffer_Size) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Config file size is too large");
    configFile.close();
    return;
  }

  DynamicJsonBuffer jsonBuffer(size + 100);
  JsonObject& root = jsonBuffer.parseObject(configFile);

  root.printTo(Payload);

  configFile.close();

  Log(MQTT_Topic[Topic_System] + "/FSConfig", Payload);
}


// ############################################################ FS_Config_Set() ############################################################
bool FS_Config_Set(String Topic, String Payload) {

  Payload = Payload.substring(0, Payload.indexOf(";"));


  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");

  if (!configFile) {
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file for writing");
    return false;
  }

  configFile.print(Payload);
  configFile.close();

  Log(MQTT_Topic[Topic_System] + "/FSConfig", "Saved to SPIFFS");

  Log(MQTT_Topic[Topic_System] + "/FSConfig", "Config changed reboot required, rebooting in 2 seconds");
  Reboot(2000);

  return true;

} // FS_Config_Set


// ################################### Version_Show() ###################################
bool Version_Show() {
  Log(MQTT_Topic[Topic_System] + "/Version", "Running Dubby v" + String(Version));
  return true;
} // Version_Show()


// ################################### Version_Update() ###################################
void Version_Update() {
  Log(MQTT_Topic[Topic_System] + "/Version", "Checking for updates ... Running Dobby v" + String(Version) + " My IP: " + IPtoString(WiFi.localIP()));
} // Version_Update()


// ################################### MQTT_Commands() ###################################
bool MQTT_Commands(String Topic, String Payload) {

  // Ignore none commands
  if (Topic.indexOf(MQTT_Topic[Topic_Commands]) == -1) {
    return false;
  }

  // Ignore commands send to Dobby
  if (Topic.indexOf(MQTT_Topic[Topic_Dobby]) != -1) {
    return false;
  }

  Payload = Payload.substring(0, Payload.indexOf(";"));
  Topic.replace(MQTT_Topic[Topic_Commands] + "/", "");

  if (Topic == "Power") {
    if (Payload.indexOf("Reboot") != -1) {
      Reboot(10000);
    }
    else if (Payload.indexOf("Shutdown") != -1) {
      Shutdown(10000);
    }
  }

  else if (Topic == "Flash" && Payload.indexOf(MQTT_Allow_Flash_Password) != -1) {
    MQTT_Allow_Flash();
  }

  else if (Topic == "FS") {
    if (FS_Commands(Payload) == true) return true;
  }

  else if (Topic == "Pins" && Payload == "Map") {
    Pin_Map();
  }

  else if (Topic == "Blink") {
    Indicator_LED_Blink(Payload.toInt());
  }

  else if (Topic == "Hostname") {
    Hostname = Payload;
    FS_Config_Drop();
    Log(MQTT_Topic[Topic_System] + "/DeviceConfig", "Reboot required rebooting in 2 seconds");
    Reboot(2000);
  }

  else if (Topic == "Version") {
    if (Payload == "Show") Version_Show();
    if (Payload == "Update") Version_Update();
  }

  else if (Topic == "IP") {
    if (Payload == "Show") IP_Show();
  }

  else if (Topic == "Dimmer/FadeJump") {
    Dimmer_Fade_Jump = Payload.toInt();
    Log(MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Fade Jump changed to: " + String(Dimmer_Fade_Jump));
  }

  else if (Topic == "Dimmer/FadeJumpDelay") {
    Dimmer_Fade_Jump_Delay = Payload.toInt();
    Log(MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Fade Jump Delay changed to: " + String(Dimmer_Fade_Jump_Delay));
  } // Dimmer


  else if (Topic == "FSConfig") {
    if (Payload == "Save") FS_Config_Save();
    else if (Payload == "Show") FS_Config_Show();
    else if (Payload == "Drop") FS_Config_Drop();
  }

  else if (Topic == "FSConfig/Set") {
    FS_Config_Set(Topic, Payload);
  }


  else if (Topic == "PinMonitor") {
    if (Payload == "State") Pin_Monitor_State();
  }


  else if (Topic == "WiFi") {
    if (Payload == "Signal") WiFi_Signal();
  }


  else if (Topic == "Test") {

    Log("/Test", "MARKER");
    // String Test_STR;
    // WiFi.printDiag(Test_STR);


  } // Test

  else {
    Log(MQTT_Topic[Topic_System] + "/Commands", "Unknown command. " + Topic + " - " + Payload);
  }

  return true;

} // MQTT_Commands()


// ################################### MQTT_All() ###################################
bool MQTT_All(String Topic, String Payload) {

  if (Topic == MQTT_Topic[Topic_All]) {

    Payload = Payload.substring(0, Payload.indexOf(";"));

    if (Payload == "KillKillMultiKill") {
      Log(MQTT_Topic[Topic_System], "Someone went on a killing spree, let the panic begin ...");
      Reboot(10000 + random(15000));
      return true;
    }

    else if (Payload == "Dimmer-OFF" && Dimmer_Configured == true) {
      Log(MQTT_Topic[Topic_Dimmer] + "/0", "All OFF");
      for (int i = 0; i < Dimmer_Max_Number_Of; i++) {
        if (Dimmer_Pins[i] != 255) {
          if (Dimmer_State[i] != 0) Dimmer_Fade(i + 1, 0);
          Log(MQTT_Topic[Topic_Dimmer] + "/" + String(i + 1) + "/State", "0");
        }
      }
      return true;
    } // Dimmer-OFF

    else if (Payload == "Relay-OFF" && Relay_Configured == true) {
      Log(MQTT_Topic[Topic_Relay] + "/0", "All OFF");
      for (int i = 0; i < Relay_Max_Number_Of; i++) {
        if (Relay_Pins[i] != 255) {
          if (digitalRead(Relay_Pins[i]) == Relay_On_State) {
            digitalWrite(Relay_Pins[i], !Relay_On_State);
            Log(MQTT_Topic[Topic_Relay] + "/" + String(i + 1) + "/State", String(OFF));
          }
        }
        return true;
      }
    } // Update
    else if (Payload == "Update") {
      int Update_Delay = 5000 + random(15000);
      Log(MQTT_Topic[Topic_System] + "/Version", "Mass update triggered, updating in " + String(Update_Delay) + " ms. Lets dance");
      Update_Ticker.once_ms(Update_Delay, Version_Update);

      return true;
    } // Update
  }

  return false;
} // MQTT_All()


// ################################### onMqttMessage() ###################################
void onMqttMessage(char* topic, char* payload, AsyncMqttClientMessageProperties properties, size_t len, size_t index, size_t total) {

  Serial.println("MARKER BEGIN ON MESSAGE");

  if (ArduinoOTA_Active == true);

  else if (String(topic).indexOf(MQTT_Topic[Topic_Buzzer]) != -1) {
    Buzzer(topic, payload);
  }

  // else if (DHT(topic, payload)) return;
  //
  else if (Relay_Configured == true) {
    if (String(topic).indexOf(MQTT_Topic[Topic_Relay]) != -1) {
      Relay(topic, payload);
    }
  }

  else if (Dimmer_Configured == true) {
    if (String(topic).indexOf(MQTT_Topic[Topic_Dimmer]) != -1) {
      Dimmer(topic, payload);
    }
  }

  the problem seems to be that the loop is to long might look at disabling watchdog for a sec or so or it might
  be issues with string comparison that gies issues

  else if (String(topic) == MQTT_Topic[Topic_Config]) {
      FS_Config_Set(topic, payload);
    }

  // else if (Distance(topic, payload)) return;
  //
  // // else if (LoadCell(topic, payload)) return;
  //
  // else if (DC_Voltmeter(topic, payload)) return;
  //
  // else if (Switch(topic, payload)) return;
  //
  // // else if (MPU6050(topic, payload)) return;
  //
  // else if (BMP180_Show(topic, payload)) return;
  //
  // else if (PIR(topic, payload)) return;
  //
  // else if (MQ2(topic, payload)) return;
  //
  // else if (LDR(topic, payload)) return;
  //
  // // else if (FS_Config_Set(topic, payload)) return;
  //
  // else if (MQTT_Commands(topic, payload)) return;

  // else if (MQTT_All(topic, payload)) return;

  Serial.println("MARKER END ON MESSAGE");

} // MQTT_Settings


// ############################################################ ArduinoOTA_Setup() ############################################################
void ArduinoOTA_Setup() {

  ArduinoOTA.setHostname(Hostname.c_str());
  ArduinoOTA.setPassword("StillNotSinking");

  ArduinoOTA.onStart([]() {
    Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "ArduinoOTA ... Started");
    ArduinoOTA_Active = true;
    MQTT_KeepAlive_Ticker.detach();
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else { // U_SPIFFS
      type = "filesystem";
    }

    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    SPIFFS.end();
    Serial.println("Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "ArduinoOTA ... End");
    ArduinoOTA_Active = false;
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    ArduinoOTA_Active = false;
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "End Failed");
    }
  });

  ArduinoOTA.begin();

} // ArduinoOTA_Setup()


// ############################################################ Base_Config_Check() ############################################################
void Base_Config_Check() {

  if (Hostname == "") {
    Serial_CLI();
  }

  if (WiFi_SSID == "") {
    Serial_CLI();
  }

  else if (WiFi_Password == "") {
    Serial_CLI();
  }

  else if (MQTT_Broker == "") {
    Serial_CLI();
  }

  else if (MQTT_Port == "") {
    Serial_CLI();
  }

  else if (MQTT_Username == "") {
    Serial_CLI();
  }

  else if (MQTT_Password == "") {
    Serial_CLI();
  }

  else if (System_Header == "") {
    Serial_CLI();
  }

  else {
    Log(MQTT_Topic[Topic_System] + "/Dobby", "Base config check done, all OK");
    return;
  }
}


// ############################################################ setup() ############################################################
// FIX - ADD log messages below
void setup() {

  // Disable interrupts during setup
  // noInterrupts();

  // ------------------------------ Serial ------------------------------
  Serial.setTimeout(100);
  Serial.begin(115200);
  Serial.println();


  // ------------------------------ Indicator_LED ------------------------------
  if (Indicator_LED_Configured == true) {
    pinMode(D4, OUTPUT);
  }
  if (Indicator_LED_Configured == true) Indicator_LED(LED_Config, true);

  // ------------------------------ FS ------------------------------
  SPIFFS.begin();

  Serial_CLI_Boot_Message(Serial_CLI_Boot_Message_Timeout);

  FS_Config_Load();

  Base_Config_Check();

  SPIFFS.end();

  // ------------------------------ Random Seed ------------------------------
  randomSeed(analogRead(0));


  // ------------------------------ MQTT ------------------------------
  MQTT_Client.onConnect(onMqttConnect);
  MQTT_Client.onDisconnect(onMqttDisconnect);
  MQTT_Client.onMessage(onMqttMessage);

  MQTT_Client.setServer(String_To_IP(MQTT_Broker), MQTT_Port.toInt());
  MQTT_Client.setCredentials(MQTT_Username.c_str(), MQTT_Password.c_str());
  MQTT_Client.setClientId(Hostname.c_str());
  // MQTT_Client.setWill("/Test/Will", 0, false, "Will Test");



  // ------------------------------ WiFi ------------------------------
  Log(MQTT_Topic[Topic_System] + "/WiFi", "SSID set to: " + WiFi_SSID);

  WiFi.disconnect();

  WiFi.mode(WIFI_STA);
  WiFi.hostname(Hostname);

  gotIpEventHandler = WiFi.onStationModeGotIP([](const WiFiEventStationModeGotIP& event) {
    Wifi_State = 1;
    wifiReconnectTimer.detach();
    Log(MQTT_Topic[Topic_System] + "/WiFi", "Connected to SSID: '" + WiFi_SSID + "' - IP: '" + IPtoString(WiFi.localIP()) + "' - MAC Address: '" + WiFi.macAddress() + "'");
    if (Indicator_LED_Configured == true) Indicator_LED(LED_WiFi, false);
    // OTA
    ArduinoOTA_Setup();
    // MQTT
    connectToMqtt();
  });

  disconnectedEventHandler = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected& event) {
    if (Wifi_State == 3) {
      Log(MQTT_Topic[Topic_System] + "/WiFi", "Connecting to SSID: " + WiFi_SSID);
    }

    else if (Wifi_State != 2) {
      Log(MQTT_Topic[Topic_System] + "/WiFi", "Disconnected from SSID: " + WiFi_SSID);
      if (Indicator_LED_Configured == true) Indicator_LED(LED_WiFi, true);
      wifiReconnectTimer.attach_ms(WiFi_Reconnect_Delay, connectToWifi);
      Wifi_State = 2;
    }
    // MQTT
    mqttReconnectTimer.detach(); // ensure we don't reconnect to MQTT while reconnecting to WiFi
  });


  // ------------------------------ MPU6050 ------------------------------
  // if (MPU6050_Configured == true) {
  //   Log(MQTT_Topic[Topic_System] + "/MPU6050", "Initializing");
  //
  //   if (Wire_Avtive == false) {
  //     Wire.begin(MPU6050_Pin_SDA, MPU6050_Pin_SCL);
  //     Wire_Avtive = true;
  //   }
  //
  //   mpu.initialize();
  //
  //
  //   Log(MQTT_Topic[Topic_System] + "/MPU6050", "Testing device connections ...");
  //   if (mpu.testConnection() == true) {
  //     Log(MQTT_Topic[Topic_System] + "/MPU6050", "Connection OK");
  //
  //     // load and configure the DMP
  //     Log(MQTT_Topic[Topic_System] + "/MPU6050", "Initializing BMP");
  //     MPU6050_Device_Status = mpu.dmpInitialize();
  //
  //     // Set offset
  //     // FIX - Add below funtion
  //     // mpu.setXGyroOffset(220);
  //     // mpu.setYGyroOffset(76);
  //     // mpu.setZGyroOffset(-85);
  //     // mpu.setZAccelOffset(1788); // 1688 factory default for my test chip
  //
  //     // make sure it worked (returns 0 if so)
  //     if (MPU6050_Device_Status == 0) {
  //         // turn on the DMP, now that it's ready
  //         Log(MQTT_Topic[Topic_System] + "/MPU6050", "Enabling BMP");
  //         mpu.setDMPEnabled(true);
  //
  //         // enable interrupt detection
  //         Log(MQTT_Topic[Topic_System] + "/MPU6050", "Enabling interrupt on pin: " + Number_To_Pin(MPU6050_Pin_Interrupt));
  //         attachInterrupt(digitalPinToInterrupt(MPU6050_Pin_Interrupt), MPU6050_BMP_DataReady, RISING);
  //         MPU6050_Interrupt_Status = mpu.getIntStatus();
  //
  //         MPU6050_BMP_Ready = true;
  //
  //         // get expected DMP packet size for later comparison
  //         packetSize = mpu.dmpGetFIFOPacketSize();
  //
  //         Log(MQTT_Topic[Topic_System] + "/MPU6050", "Initialization complete");
  //     } else {
  //         // ERROR!
  //         // 1 = initial memory load failed
  //         // 2 = DMP configuration updates failed
  //         // (if it's going to break, usually the code will be 1)
  //         Log(MQTT_Topic[Topic_Log_Error] + "/MPU6050", "DMP Initialization failed with code: " + String(MPU6050_Device_Status));
  //       }
  //
  //   }
  //   else {
  //     Log(MQTT_Topic[Topic_Log_Error] + "/MPU6050", "Connection failed, disabling MPU6050");
  //     // Disable mpu config
  //     MPU6050_Configured = false;
  //   }
  // }


  // ------------------------------ BMP180 ------------------------------
  if(BMP180_Configured == true) {
    Log(MQTT_Topic[Topic_System] + "/BMP180", "Initializing");

    if (Wire_Avtive == false) {
      Wire.begin(BMP180_Pin_SDA, BMP180_Pin_SCL);
      Wire_Avtive = true;
    }

    // Check connection to BMP
    // Connection OK
    if (BMP.begin() == true) {
      Log(MQTT_Topic[Topic_System] + "/BMP180", "Initialization compleate");
    }

    // Connection Failed
    else {
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Unable to find BMP180 on I2C bus");
      Log(MQTT_Topic[Topic_Log_Error] + "/BMP180", "Disabling BMP");
      BMP180_Configured = false;
    }
  }


  // Start wifi connection
  connectToWifi();

  if (Indicator_LED_Configured == true) Indicator_LED(LED_Config, false);

  Boot_Compleate = true;

} // setup()


// ############################################################ loop() ############################################################
void loop() {

  OTA_Handler();

  Relay_Auto_OFF_Loop();

  Distance_Sensor();

  Distance_Sensor_Auto_OFF();

  Button_Loop();

  Switch_Loop();

  // MPU6050_Loop();

  BMP180_Loop();

  DHT_Loop();

  // RFID
  // MFRC522_Loop();

  PIR_Loop();

} // loop()