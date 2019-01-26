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
#define Version 102008
// First didget = Software type 1-Production 2-Beta 3-Alpha
// Secound and third didget = Major version number
// Fourth to sixth = Minor version number

String Hostname = "/NotConfigured";
String System_Header = "/Dobby";
String System_Sub_Header = "";
String Config_ID = "0";


// ------------------------------------------------------------ WiFi ------------------------------------------------------------
#include <ESP8266WiFi.h>
#include <Ticker.h>

WiFiClient WiFi_Client;

WiFiEventHandler gotIpEventHandler;
WiFiEventHandler disconnectedEventHandler;

String WiFi_SSID;
String WiFi_Password;

bool WiFi_Disconnect_Message_Send = true;

// ------------------------------------------------------------ MQTT ------------------------------------------------------------
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <MB_Queue.h>

String MQTT_Broker;
String MQTT_Port;

String MQTT_Username;
String MQTT_Password;

// If the buffer size is not set then they system will not work propperly
PubSubClient MQTT_Client(WiFi_Client);

#define MQTT_RX_Queue_Max_Size 100
MB_Queue MQTT_RX_Queue_Topic(MQTT_RX_Queue_Max_Size);
MB_Queue MQTT_RX_Queue_Payload(MQTT_RX_Queue_Max_Size);

#define MQTT_Reconnect_Interval 2000
unsigned long MQTT_Reconnect_At = 1000;

Ticker MQTT_KeepAlive_Ticker;
unsigned long MQTT_KeepAlive_Interval = 60;

#define MQTT_State_Init 0
#define MQTT_State_Connecting 1
#define MQTT_State_Connected 2
#define MQTT_State_Disconnecting 3
#define MQTT_State_Disconnected 4
#define MQTT_State_Error 5
byte MQTT_State = MQTT_State_Init;

int MQTT_Last_Error;

bool MQTT_Subscrive_Compleate = false;

#define NONE 0
#define PLUS 1
#define HASH 2

const byte MQTT_Topic_Number_Of = 21;

// System
#define Topic_Config 0
#define Topic_Commands 1
#define Topic_All 2
#define Topic_KeepAlive 3
#define Topic_Dobby 4
// Log
#define Topic_Log_Debug 5
#define Topic_Log_Info 6
#define Topic_Log_Warning 7
#define Topic_Log_Error 8
#define Topic_Log_Fatal 9
// Devices
#define Topic_Ammeter 10
#define Topic_Button 11
#define Topic_DHT 12
#define Topic_DC_Voltmeter 13
#define Topic_Dimmer 14
#define Topic_Distance 15
#define Topic_MQ 16
#define Topic_Relay 17
#define Topic_PIR 18
#define Topic_MAX31855 19
#define Topic_Switch 20

// System
#define Topic_Config_Text "/Config/"
#define Topic_Commands_Text "/Commands/"
#define Topic_All_Text "/All"
#define Topic_KeepAlive_Text "/KeepAlive/"
#define Topic_Dobby_Text "/Commands/Dobby/"
// Log
#define Topic_Log_Debug_Text "/Debug"
#define Topic_Log_Info_Text "/Info"
#define Topic_Log_Warning_Text "/Warning"
#define Topic_Log_Error_Text "/Error"
#define Topic_Log_Fatal_Text "/Fatal"
// Devices
#define Topic_Ammeter_Text "/Ammeter/"
#define Topic_Button_Text "/Button/"
#define Topic_DHT_Text "/DHT/"
#define Topic_DC_Voltmeter_Text "/DC_Voltmeter/"
#define Topic_Dimmer_Text "/Dimmer/"
#define Topic_Distance_Text "/Distance/"
#define Topic_MQ_Text "/MQ/"
#define Topic_Relay_Text "/Relay/"
#define Topic_PIR_Text "/PIR/"
#define Topic_MAX31855_Text "/MAX31855/"
#define Topic_Switch_Text "/Switch/"

String MQTT_Topic[MQTT_Topic_Number_Of] = {
  // System
  System_Header + Topic_Config_Text + Hostname,
  System_Header + Topic_Commands_Text + Hostname,
  System_Header + Topic_All_Text,
  System_Header + Topic_KeepAlive_Text + Hostname,
  System_Header + Topic_Dobby_Text,
  // Log
  System_Header + Topic_Log_Debug_Text + Hostname,
  System_Header + Topic_Log_Info_Text + Hostname,
  System_Header + Topic_Log_Warning_Text + Hostname,
  System_Header + Topic_Log_Error_Text + Hostname,
  System_Header + Topic_Log_Fatal_Text + Hostname,
  // Devices
  System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Button_Text + Hostname,
  System_Header + System_Sub_Header + Topic_DHT_Text + Hostname,
  System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Dimmer_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Distance_Text + Hostname,
  System_Header + System_Sub_Header + Topic_MQ_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Relay_Text + Hostname,
  System_Header + System_Sub_Header + Topic_PIR_Text + Hostname,
  System_Header + System_Sub_Header + Topic_MAX31855_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Switch_Text + Hostname,
};

bool MQTT_Topic_Subscribe_Active[MQTT_Topic_Number_Of] = {
  // System
  false,
  true,
  true,
  false,
  false,
  // Log
  false,
  false,
  false,
  false,
  false,
  // Devices
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
  // System
  NONE,
  HASH,
  HASH,
  NONE,
  NONE,
  // Log
  NONE,
  NONE,
  NONE,
  NONE,
  NONE,
  // Devices
  NONE,
  PLUS,
  PLUS,
  NONE,
  PLUS,
  PLUS,
  NONE,
  PLUS,
  PLUS,
  NONE,
  NONE,
};

bool MQTT_Subscribtion_Active[MQTT_Topic_Number_Of];


// ---------------------------------------- ArduinoOTA_Setup() ----------------------------------------
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <WiFiUdp.h>
#include <ArduinoOTA.h>
#include <SPI.h>

bool ArduinoOTA_Active = false;


// ---------------------------------------- FTP Server ----------------------------------------
#include <ESP8266FtpServer.h>

// Set #define FTP_DEBUG in ESP8266FtpServer.h to see ftp verbose on serial
FtpServer FTP_Server;


// ------------------------------------------------------------ Log() ------------------------------------------------------------
// http://github.com/MBojer/MB_Queue
#include <MB_Queue.h>
// FIX - Might need to add support for log full handling
#define Log_Max_Queue_Size 100
MB_Queue Log_Queue_Topic(Log_Max_Queue_Size);
MB_Queue Log_Queue_Log_Text(Log_Max_Queue_Size);

#define Log_Level_Debug 0
#define Log_Level_Info 1
#define Log_Level_Warning 2
#define Log_Level_Error 3
#define Log_Level_Fatal 4

byte Log_Level_Device = Log_Level_Debug;


// ---------------------------------------- SPIFFS() ----------------------------------------
#include "FS.h"


// ------------------------------------------------------------ CLI ------------------------------------------------------------
#define Command_List_Length 22
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
  "show wifi",
  "save",
  "check",
  "reboot",
  "shutdown"};

String CLI_Input_String;
bool CLI_Command_Complate = false;

#define Serial_CLI_Boot_Message_Timeout 3


// ------------------------------------------------------------ ESP_Reboot() ------------------------------------------------------------
Ticker ESP_Power_Ticker;


// ------------------------------------------------------------ FS_Config ------------------------------------------------------------
#include <ArduinoJson.h>

#define Config_Json_Max_Buffer_Size 2048
bool Config_json_Loaded = false;

#define FS_Confing_File_Name "/Dobby.json"


// ------------------------------------------------------------ FS_Config_UDP ------------------------------------------------------------
#include <WiFiUdp.h>

WiFiUDP UDP_Client;

#define FS_Config_UDP_Port 8050
#define FS_Config_UDP_Buffer_Size 512
char FS_Config_UDP_Buffer[FS_Config_UDP_Buffer_Size];

bool Config_Requested = false;


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

byte Pin_Monitor_Pins_Active[Pin_Monitor_Pins_Number_Of] = {Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free, Pin_Free};

String Pin_Monitor_State_Text[4] = {"In Use", "Free", "I2C SCL", "I2C SDA"};


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


// ------------------------------------------------------------ Dimmer ------------------------------------------------------------
#define Dimmer_Max_Number_Of 6
bool Dimmer_Configured = false;
byte Dimmer_Pins[Dimmer_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

int Dimmer_State[Dimmer_Max_Number_Of];
byte Dimmer_Procent[Dimmer_Max_Number_Of];

byte Dimmer_Fade_Jump = 20;
byte Dimmer_Fade_Jump_Delay = 40;


// ------------------------------------------------------------ Button ------------------------------------------------------------
#define Button_Max_Number_Of 6
bool Button_Configured = false;
byte Button_Pins[Button_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

unsigned long Button_Ignore_Input_Untill[Button_Max_Number_Of];
unsigned int Button_Ignore_Input_For = 750; // Time in ms before a butten can triggered again

String Button_Target[Button_Max_Number_Of];


// ------------------------------------------------------------ Switch ------------------------------------------------------------
bool Switch_Configured = false;

#define Switch_Max_Number_Of 6
byte Switch_Pins[Switch_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

unsigned long Switch_Ignore_Input_Untill;
unsigned long Switch_Refresh_Rate = 250; // ms between checking switch state

bool Switch_Last_State[Switch_Max_Number_Of];

String Switch_Target_ON[Switch_Max_Number_Of];
String Switch_Target_OFF[Switch_Max_Number_Of];


// ------------------------------------------------------------ MQ ------------------------------------------------------------
bool MQ_Configured = false;

byte MQ_Pin_A0 = 255;

int MQ_Current_Value = -1;
int MQ_Value_Min = -1;
int MQ_Value_Max = -1;


Ticker MQ_Ticker;
#define MQ_Refresh_Rate 100



// ############################################################ Headers ############################################################
// ############################################################ Headers ############################################################
// ############################################################ Headers ############################################################

void MQTT_Connect();
void MQTT_Subscribe(String Topic, bool Activate_Topic, byte SubTopics);
void Rebuild_MQTT_Topics();

bool Is_Valid_Number(String str);

String FS_Config_Build();
bool FS_Config_Save();
void FS_Config_Drop();
bool FS_Config_Load();
void FS_Format();

byte Pin_Monitor(byte Action, byte Pin_Number);
String Number_To_Pin(byte Pin_Number);
byte Pin_To_Number(String Pin_Name);

bool Relay(String &Topic, String &Payload);
bool Dimmer(String &Topic, String &Payload);
bool Switch(String &Topic, String &Payload);

void MQ_Loop();


// ############################################################ Functions ############################################################
// ############################################################ Functions ############################################################
// ############################################################ Functions ############################################################


// ############################################################ Is_Valid_Number() ############################################################
bool Is_Valid_Number(String str) {
  for(byte i=0;i<str.length();i++)
  {
    if(isDigit(str.charAt(i))) return true;
  }
  return false;
} // Is_Valid_Number()


// ############################################################ IP_To_String() ############################################################
String IP_To_String(IPAddress IP_Address) {

  String Temp_String = String(IP_Address[0]) + "." + String(IP_Address[1]) + "." + String(IP_Address[2]) + "." + String(IP_Address[3]);

  return Temp_String;

} // IP_To_String
 

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


// ############################################################ Log() ############################################################
// Writes text to MQTT and Serial

// Writes text to MQTT and Serial
void Log(String Topic, String Log_Text) {

  // Log level check
  // No reason to check debug, if log level is set to debug then everything gets posted  
  if (Log_Level_Device == Log_Level_Debug) {
    // Publish the message
  }
  else if (Topic.indexOf(System_Header + "/Log/" + Hostname + "/Info") != -1) {
    if (Log_Level_Device > Log_Level_Info) {
      return;
    }
  }
  else if (Topic.indexOf(System_Header + "/Log/" + Hostname + "/Warning") != -1) {
    if (Log_Level_Device > Log_Level_Warning) {
      return;
    }
  }
  else if (Topic.indexOf(System_Header + "/Log/" + Hostname + "/Error") != -1) {
    if (Log_Level_Device > Log_Level_Error) {
      return;
    }
  }
  else if (Topic.indexOf(System_Header + "/Log/" + Hostname + "/Fatal") != -1) {
    if (Log_Level_Device > Log_Level_Fatal) {
      return;
    }
  }

  // Online/Offline check
  // Online
  if (MQTT_Client.connected() == true) {

    // Print log queue
    if (Log_Queue_Topic.Length() > 0) {
      // Send offline being marker
      MQTT_Client.publish(String(MQTT_Topic[Topic_Log_Debug] + "/Log").c_str(), "Offline log begin");
      while (Log_Queue_Topic.Length() > 0) {
        // State message post as retained message
        if (Log_Queue_Topic.Peek().indexOf("/State") != -1) {
          MQTT_Client.publish(Log_Queue_Topic.Pop().c_str(), Log_Queue_Log_Text.Pop().c_str(), true);
        }
        // Post as none retained message
        MQTT_Client.publish(Log_Queue_Topic.Pop().c_str(), Log_Queue_Log_Text.Pop().c_str());
      }
      // Send offline end marker
      MQTT_Client.publish(String(MQTT_Topic[Topic_Log_Debug] + "/Log").c_str(), "Offline log end");
    }

    // State message post as retained message
    if (Topic.indexOf("/State") != -1) {
      MQTT_Client.publish(Topic.c_str(), Log_Text.c_str(), true);
    }
    // Post as none retained message
    else MQTT_Client.publish(Topic.c_str(), Log_Text.c_str());
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

  Log(MQTT_Topic[Topic_Log_Info] + "/IndicatorLED", "Blinking " + String(Number_Of_Blinks) + " times");

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
    Log(MQTT_Topic[Topic_Log_Debug] + "/IndicatorLED", "Indicator LED not configured");
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


// ############################################################ ESP_Reboot() ############################################################
void ESP_Reboot() {

  Log(MQTT_Topic[Topic_Log_Info], "Rebooting");
  MQTT_Client.disconnect();
  Serial.flush();

  ESP.restart();

} // ESP_Reboot()


// ############################################################ ESP_Shutdown() ############################################################
void ESP_Shutdown() {

  Log(MQTT_Topic[Topic_Log_Warning], "Shutting down");
  MQTT_Client.disconnect();
  Serial.flush();

  ESP.deepSleep(0);

} // ESP_Shutdown()



// ############################################################ Reboot() ############################################################
void Reboot(unsigned long Reboot_In) {

  Log(MQTT_Topic[Topic_Log_Info], "Kill command issued, rebooting in " + String(Reboot_In / 1000) + " seconds");

  MQTT_Client.disconnect();

  ESP_Power_Ticker.once_ms(Reboot_In, ESP_Reboot);

} // Reboot()


// ############################################################ Shutdown() ############################################################
void Shutdown(unsigned long Shutdown_In) {

  Log(MQTT_Topic[Topic_Log_Warning], "Kill command issued, shutting down in " + String(Shutdown_In / 1000) + " seconds");

  ESP_Power_Ticker.once_ms(Shutdown_In, ESP_Shutdown);

} // Shutdown()


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
    Log(MQTT_Topic[Topic_Log_Info], "Rebooting");

    delay(500);
    ESP.restart();
  }

  else if (CLI_Input_String == "shutdown") {
    Serial.println("");
    for (byte i = 3; i > 0; i--) {
      Serial.printf("\tShutting down in: %i\r", i);
      delay(1000);
    }
    Log(MQTT_Topic[Topic_Log_Warning], "Shutdown, bye bye :-(");

    delay(500);
    ESP.deepSleep(0);
  }

  else if (CLI_Input_String == "show mac") {
    Serial.println("MAC Address: " + WiFi.macAddress());
  }
  
  else if (CLI_Input_String == "show wifi") {
    Serial.println("Connected to SSID: '" + WiFi_SSID + "' - IP: '" + IP_To_String(WiFi.localIP()) + "' - MAC Address: '" + WiFi.macAddress() + "'");
  }

  else {
    if (CLI_Input_String != "") Log(MQTT_Topic[Topic_Log_Warning] + "/CLI", "Unknown command: " + CLI_Input_String);
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


// ############################################################ FS_Config_Settings_Set(String Array) ############################################################
bool FS_Config_Settings_Set(String String_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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

} // FS_Config_Settings_Set()


// ############################################################ FS_Config_Settings_Set(Integer Array) ############################################################
bool FS_Config_Settings_Set(int Integer_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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

} // FS_Config_Settings_Set()


// ############################################################ FS_Config_Settings_Set(Float Array) ############################################################
bool FS_Config_Settings_Set(float Float_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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

} // FS_Config_Settings_Set()


// ############################################################ FS_Config_Settings_Set(Byte Array) ############################################################
bool FS_Config_Settings_Set(byte Byte_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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


} // FS_Config_Settings_Set()


// ############################################################ FS_Config_Settings_Set(Unsigned Long Array) ############################################################
bool FS_Config_Settings_Set(unsigned long Unsigned_Long_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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


} // FS_Config_Settings_Set()


// ############################################################ FS_Config_Settings_Set(Boolian Array) ############################################################
bool FS_Config_Settings_Set(bool Boolian_Array[], byte Devices_Max, String Payload, String MQTT_Target, String Log_Text) {

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


} // FS_Config_Settings_Set()


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
  root_Config.set("MQTT_KeepAlive_Interval", MQTT_KeepAlive_Interval);

  // Devices


  String Return_String;
  root_Config.printTo(Return_String);
  return Return_String;

} // FS_Config_Build()


// #################################### FS_Config_Save() ####################################
bool FS_Config_Save() {

  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");
  if (!configFile) {
    Log(MQTT_Topic[Topic_Log_Error] + "/FSConfig", "Failed to open config file for writing");
    return false;
  }

  configFile.print(FS_Config_Build());
  configFile.close();

  Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig", "Saved to SPIFFS");

  return true;
} // FS_Config_Save()


// #################################### FS_Config_Drop() ####################################
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
  root.set("Config_ID", "0");

  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");
  
  if (!configFile) {
    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig", "Failed to open config file for writing");
    return;
  }

  root.printTo(configFile);
  configFile.close();

  Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig", "Config droped clean config saved to SPIFFS");

  return;
} // FS_Config_Drop()


// #################################### FS_Config_Check() ####################################
bool FS_Config_Check(String json_String) {

  // Try to phrase the json string
  StaticJsonBuffer<2048> jsonBuffer;
  JsonObject& root = jsonBuffer.parseObject(json_String);
  
  // Check if it phrased
  if (root.success() == false) {
    Log(MQTT_Topic[Topic_Log_Warning] + "/FSConfig/UDP", "Unable to phrase incomming config");
    Serial.println(json_String); // RM
    return false;
  }

  // Config_ID Check
  if (root.get<String>("Config_ID") == Config_ID) {
    Log(MQTT_Topic[Topic_Log_Debug] + "/FSConfig/UDP", "Config already up to date");
    return false;
  }

  // Check for required settings
  String Config_Check_List[] = {"Hostname", "System_Header", "WiFi_SSID", "WiFi_Password", "MQTT_Broker", "MQTT_Port", "MQTT_Username", "MQTT_Password", "Config_ID"};

  for (byte i = 0; i < 9; i++) {
    if (root.get<String>(Config_Check_List[i]) == "") {
      Log(MQTT_Topic[Topic_Log_Warning] + "/FSConfig/UDP", "Missing '" + Config_Check_List[i] + "' from config");
      return false;
    }
  }

  return true;

} // FS_Config_Check()


// #################################### FS_Config_UDP_Loop() ####################################
void FS_Config_UDP_Loop() {

  int packetSize = UDP_Client.parsePacket();

  if (packetSize) {
    // Log event
    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig/UDP", "UDP Config recived from: " + UDP_Client.remoteIP().toString());

    int Package_Length = UDP_Client.read(FS_Config_UDP_Buffer, FS_Config_UDP_Buffer_Size);

    if (Package_Length > 0) {
      FS_Config_UDP_Buffer[Package_Length] = 0;
    }

    File configFile = SPIFFS.open(FS_Confing_File_Name, "w");

    if (!configFile) {
      Log(MQTT_Topic[Topic_Log_Error] + "/FSConfig/UDP", "Failed to open config file for writing");
      return;
    }

    // Check if config is valid
    if (FS_Config_Check(FS_Config_UDP_Buffer) == false) {
      return;
    }

    configFile.print(FS_Config_UDP_Buffer);
    configFile.close();

    // Reply with packet size
    UDP_Client.beginPacket(UDP_Client.remoteIP(), UDP_Client.remotePort());
    UDP_Client.write(String("Recived: " + String(Package_Length)).c_str());
    UDP_Client.endPacket();

    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig/UDP", "Saved to SPIFFS");

    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig/UDP", "Config changed reboot required, rebooting in 2 seconds");
    Reboot(2000);
  }
    
} // FS_Config_UDP_Loop()


// ############################################################ FS_Config_Load() ############################################################
bool FS_Config_Load() {

  // Open file
  File configFile = SPIFFS.open(FS_Confing_File_Name, "r");
  // File check
  if (!configFile) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig", "Failed to open config file");
    configFile.close();
    Serial_CLI();
    return false;
  }

  size_t size = configFile.size();
  if (size > Config_Json_Max_Buffer_Size) {
    Config_json_Loaded = true;
    Log(MQTT_Topic[Topic_Log_Info] + "/FSConfig", "Config file size is too large");
    configFile.close();
    Serial_CLI();
    return false;
  }

  // Parrse json
  DynamicJsonBuffer jsonBuffer(size + 100);
  JsonObject& root = jsonBuffer.parseObject(configFile);

  // Close file
  configFile.close();

  // Load config into variables
  // ############### System ###############
  Hostname = root.get<String>("Hostname");
  System_Header = root.get<String>("System_Header");
  System_Sub_Header = root.get<String>("System_Sub_Header");
  // Rebuild topics to get naming right
  Rebuild_MQTT_Topics();

  Config_ID = root.get<String>("Config_ID");

  WiFi_SSID = root.get<String>("WiFi_SSID");
  WiFi_Password = root.get<String>("WiFi_Password");
  MQTT_Broker = root.get<String>("MQTT_Broker");
  MQTT_Port = root.get<String>("MQTT_Port");
  MQTT_Username = root.get<String>("MQTT_Username");
  MQTT_Password = root.get<String>("MQTT_Password");

  MQTT_KeepAlive_Interval = root.get<unsigned long>("MQTT_KeepAlive_Interval");
  

  // ############### Dimmer ###############
  if (root.get<String>("Dimmer_Pins") != "") {
    MQTT_Subscribe(MQTT_Topic[Topic_Dimmer], true, PLUS);
    FS_Config_Settings_Set(Dimmer_Pins, Dimmer_Max_Number_Of, root.get<String>("Dimmer_Pins"), MQTT_Topic[Topic_Log_Debug] + "/Dimmer", "Dimmer Pins");
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


  // ############### Relay ###############
  if (root.get<String>("Relay_On_State") != "" && root.get<String>("Relay_Pins") != "") {
    Relay_On_State = root.get<bool>("Relay_On_State");

    // Relay pins
    FS_Config_Settings_Set(Relay_Pins, Relay_Max_Number_Of, root.get<String>("Relay_Pins"), MQTT_Topic[Topic_Log_Debug] + "/Relay", "Relay Pins");
    for (byte i = 0; i < Relay_Max_Number_Of; i++) {
      if (Relay_Pins[i] != 255 && Pin_Monitor(Reserve_Normal, Relay_Pins[i]) == Pin_Free) {
        pinMode(Relay_Pins[i], OUTPUT);
        digitalWrite(Relay_Pins[i], !Relay_On_State);
      }
    }

    FS_Config_Settings_Set(Relay_Pin_Auto_Off, Relay_Max_Number_Of, root.get<String>("Relay_Pin_Auto_Off"), MQTT_Topic[Topic_Log_Debug] + "/Relay", "Relay Pins Auto Off");
    FS_Config_Settings_Set(Relay_Pin_Auto_Off_Delay, Relay_Max_Number_Of, root.get<String>("Relay_Pin_Auto_Off_Delay"), MQTT_Topic[Topic_Log_Debug] + "/Relay", "Relay Pins Auto Off Delay");

    MQTT_Subscribe(MQTT_Topic[Topic_Relay], true, PLUS);
    Relay_Configured = true;
  }


  // ############### Button ###############
  if (root.get<String>("Button_Pins") != "") {
    // MQTT_Subscribe(MQTT_Topic[Topic_Button], true, PLUS);
    FS_Config_Settings_Set(Button_Pins, Button_Max_Number_Of, root.get<String>("Button_Pins"), MQTT_Topic[Topic_Log_Debug] + "/Button", "Button Pins");
    Button_Configured = true;
    // Set pinMode
    for (byte i = 0; i < Button_Max_Number_Of; i++) {
      if (Button_Pins[i] != 255) {
        if (Pin_Monitor(Reserve_Normal, Button_Pins[i]) == Pin_Free) {
          pinMode(Button_Pins[i], INPUT_PULLUP);
        }
      }
    }
    if (root.get<String>("Button_Target") != "") {
      FS_Config_Settings_Set(Button_Target, Button_Max_Number_Of, root.get<String>("Button_Target"), MQTT_Topic[Topic_Log_Debug] + "/Button", "Button Target");
    }
  }


  // ############### Switch ###############
  if (root.get<String>("Switch_Pins") != "") {
    MQTT_Subscribe(MQTT_Topic[Topic_Switch], true, PLUS);
    FS_Config_Settings_Set(Switch_Pins, Switch_Max_Number_Of, root.get<String>("Switch_Pins"), MQTT_Topic[Topic_Log_Debug] + "/Switch", "Switch Pins");

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
      FS_Config_Settings_Set(Switch_Target_ON, Switch_Max_Number_Of, root.get<String>("Switch_Target_ON"), MQTT_Topic[Topic_Log_Debug] + "/Switch", "Switch Target ON");
    }

    if (root.get<String>("Switch_Target_OFF") != "") {
      FS_Config_Settings_Set(Switch_Target_OFF, Switch_Max_Number_Of, root.get<String>("Switch_Target_OFF"), MQTT_Topic[Topic_Log_Debug] + "/Switch", "Switch Target OFF");
    }
  }

  // ############### MQ ###############
  if (root.get<String>("MQ_Pin_A0") != "") {
    Log(MQTT_Topic[Topic_Log_Debug] + "/MQ", "Configuring");

    // Check if pin is free
    if (Pin_Monitor(Reserve_Normal, root.get<byte>("MQ_Pin_A0")) == Pin_Free) {
        // Set variable
        MQ_Pin_A0 = Pin_To_Number(root.get<String>("MQ_Pin_A0"));
        // Set pinmode
        pinMode(MQ_Pin_A0, INPUT);
        // Subscribe to topic
        MQTT_Subscribe(MQTT_Topic[Topic_MQ], true, NONE);
        // Set configured to true
        MQ_Configured = true;
        // Read once to set Min/Max referance
        MQ_Loop();
        // Set min max to current
        MQ_Value_Min = MQ_Current_Value;
        MQ_Value_Max = MQ_Current_Value;
        // Start ticker
        MQ_Ticker.attach_ms(MQ_Refresh_Rate, MQ_Loop);
        // Log configuration compleate
        Log(MQTT_Topic[Topic_MQ] + "/MQ", "Configuration compleate");
      }
      else {
        Log(MQTT_Topic[Topic_Log_Error] + "/MQ", "Configuration failed pin in use");
      }
    }
  return true;
}


// ############################################################ FS_List() ############################################################
void FS_List() {
  String str = "";
  Dir dir = SPIFFS.openDir("/");
  while (dir.next()) {
    str += dir.fileName();
    str += " / ";
    str += dir.fileSize();
    str += "\r\n";
  }
  Log(MQTT_Topic[Topic_Log_Info] + "/FS/List", str);
} // FS_List


// ############################################################ FS_Format() ############################################################
void FS_Format() {
  Log(MQTT_Topic[Topic_Log_Debug] + "/FS/Format", "SPIFFS Format started ... NOTE: Please wait 30 secs for SPIFFS to be formatted");
  SPIFFS.format();
  Log(MQTT_Topic[Topic_Log_Info] + "/FS/Format", "SPIFFS Format compleate");
} // FS_Format()


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

      Log(MQTT_Topic[Topic_Log_Info] + "/FS/cat", cat_String);
      return true;
    }
  }

  return false;
} // FS_cat()


// ############################################################ FS_del() ############################################################
bool FS_del(String File_Path) {

  if (SPIFFS.exists(File_Path)) {
    if (SPIFFS.remove(File_Path) == true) {
      Log(MQTT_Topic[Topic_Log_Info] + "/FS/del", File_Path);
      return true;
    }
    else {
      Log(MQTT_Topic[Topic_Log_Error] + "/FS/del", "Unable to delete: " + File_Path);
      return false;
    }
  }
  return false;
} // FS_cat()


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


// ############################################################ Base_Config_Check() ############################################################
void Base_Config_Check() {

  if (Hostname == "" || Hostname == "/NotConfigured") {
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
    Log(MQTT_Topic[Topic_Log_Debug] + "/Dobby", "Base config check done, all OK");
    return;
  }
}


// ############################################################ ArduinoOTA_Setup() ############################################################
void ArduinoOTA_Setup() {

  ArduinoOTA.setHostname(Hostname.c_str());
  ArduinoOTA.setPassword("StillNotSinking");

  ArduinoOTA.onStart([]() {
    Log(MQTT_Topic[Topic_Log_Info] + "/ArduinoOTA", "ArduinoOTA ... Started");
    ArduinoOTA_Active = true;
    MQTT_KeepAlive_Ticker.detach();
    String type;
    if (ArduinoOTA.getCommand() == U_FLASH) {
      type = "sketch";
    } else { // U_SPIFFS
      type = "filesystem";
    }

    // NOTE: if updating SPIFFS this would be the place to unmount SPIFFS using SPIFFS.end()
    Log(MQTT_Topic[Topic_Log_Info] + "/ArduinoOTA", "Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Log(MQTT_Topic[Topic_Log_Info] + "/ArduinoOTA", "ArduinoOTA ... End");
    // MQTT_Client.disconnect();
    ArduinoOTA_Active = false;
  });

  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });

  ArduinoOTA.onError([](ota_error_t error) {
    ArduinoOTA_Active = false;
    Serial.printf("Error[%u]: ", error);
    if (error == OTA_AUTH_ERROR) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/ArduinoOTA", "Auth Failed");
    } else if (error == OTA_BEGIN_ERROR) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/ArduinoOTA", "Begin Failed");
    } else if (error == OTA_CONNECT_ERROR) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/ArduinoOTA", "Connect Failed");
    } else if (error == OTA_RECEIVE_ERROR) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/ArduinoOTA", "Receive Failed");
    } else if (error == OTA_END_ERROR) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/ArduinoOTA", "End Failed");
    }
  });

  ArduinoOTA.begin();

} // ArduinoOTA_Setup()


// ############################################################ WiFi_On_Connect() ############################################################
void WiFi_On_Connect() {
    // Log event
    Log(MQTT_Topic[Topic_Log_Info] + "/WiFi", "Connected to SSID: '" + WiFi_SSID + "' - IP: '" + IP_To_String(WiFi.localIP()) + "' - MAC Address: '" + WiFi.macAddress() + "'");
    // Indicator_LED(LED_WiFi, false);
    WiFi_Disconnect_Message_Send = false;
    // Just a slight delay to make sure everything is up
    MQTT_Reconnect_At = millis() + 250;
    // Set MQTT_State to MQTT_State_Connecting so no log messages apear during initial connection
    MQTT_State = MQTT_State_Connecting;
    // Disable indicator led
    Indicator_LED(LED_WiFi, false);
    // FTP Server
    //username, password for ftp.  set ports in ESP8266FtpServer.h  (default 21, 50009 for PASV)
    FTP_Server.begin("dobby","heretoserve");
    // Request config
    Log(MQTT_Topic[Topic_Dobby] + "Config", Hostname + "," + Config_ID + ",FTP," + IP_To_String(WiFi.localIP()));

} // WiFi_On_Connect()


// ############################################################ WiFi_Setup() ############################################################
void WiFi_Setup() {

  bool WiFi_Reset_Required = false;

  WiFi.hostname(Hostname);
  Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Set Hostname to: " + Hostname);

  if (WiFi.getMode() != WIFI_STA) {
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Changing 'mode' to 'WIFI_STA'");
    WiFi.mode(WIFI_STA);
    WiFi_Reset_Required = true;
  }

  if (WiFi.getAutoConnect() != true) {
    WiFi.setAutoConnect(true);
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Changing 'AutoConnect' to 'true'");
  }

  if (WiFi.getAutoReconnect() != true) {
    WiFi.setAutoReconnect(true);
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Changing 'AutoReconnect' to 'true'");
  }

  if (WiFi.SSID() != WiFi_SSID) {
    WiFi.SSID();
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Changing 'SSID' to '" + WiFi_SSID + "'");
    WiFi_Reset_Required = true;
  }

  // WiFi_Client.setNoDelay(true);

  if (WiFi_Reset_Required == true) {
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Reset required");
    WiFi.disconnect(false);
  }

  // Callbakcs
  gotIpEventHandler = WiFi.onStationModeGotIP([](const WiFiEventStationModeGotIP& event) {
    WiFi_On_Connect();
  });

  disconnectedEventHandler = WiFi.onStationModeDisconnected([](const WiFiEventStationModeDisconnected& event) {
    // Check if the disconnected message have already been send if it has do nothing.
    if (WiFi_Disconnect_Message_Send == false) {
      
      // Do nothing if its within the first 5 sec of boot
      if (millis() < 5000) {
        return;
      }
      
      Log(MQTT_Topic[Topic_Log_Warning] + "/WiFi", "Disconnected from SSID: " + WiFi_SSID);
      Indicator_LED(LED_WiFi, true);
      WiFi_Disconnect_Message_Send = true;
    }
  });

  // Check if WiFi is up
  // WiFi connected
  if (WiFi.status() != WL_CONNECTED) {
    Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Connecting to SSID: " + WiFi_SSID);
    WiFi.begin(WiFi_SSID.c_str(), WiFi_Password.c_str());
  }
  // WiFi not connected
  else {
    WiFi_On_Connect();
  }

  // Set wifi to persistent so the defice reconnects asap
  WiFi.persistent(true);

  Log(MQTT_Topic[Topic_Log_Debug] + "/WiFi", "Configuration compleate");


} // WiFi_Setup()


// ############################################################ MQTT_Error_Text() ############################################################
String MQTT_Error_Text(int Error_Code) {

  if (Error_Code == MQTT_CONNECTION_TIMEOUT) return "Timeout - The server didn't respond within the keepalive time";
  else if (Error_Code == MQTT_CONNECTION_LOST) return "Connecton lost - The network connection was broken";
  else if (Error_Code == MQTT_CONNECT_FAILED) return "Connect failed - The network connection failed";
  else if (Error_Code == MQTT_DISCONNECTED) return "Disconnected - The client is disconnected cleanly";
  else if (Error_Code == MQTT_CONNECTED) return "Connected - The client is connected";
  else if (Error_Code == MQTT_CONNECT_BAD_PROTOCOL) return "Bad protocol - The server doesn't support the requested version of MQTT";
  else if (Error_Code == MQTT_CONNECT_BAD_CLIENT_ID) return "Bad client id - The server rejected the client identifier";
  else if (Error_Code == MQTT_CONNECT_UNAVAILABLE) return "Unavalible - The server was unable to accept the connection";
  else if (Error_Code == MQTT_CONNECT_BAD_CREDENTIALS) return "Bad credintials - The username/password were rejected";
  else if (Error_Code == MQTT_CONNECT_UNAUTHORIZED) return "Unauthorized - The client was not authorized to connect";
  else return "Unknown error code: " + String(Error_Code);

} // MQTT_Error_Text()

// ############################################################ High_Low_String() ############################################################
void Rebuild_MQTT_Topics() {
  // System
  MQTT_Topic[Topic_Config] = System_Header + Topic_Config_Text + Hostname;
  MQTT_Topic[Topic_Commands] = System_Header + Topic_Commands_Text + Hostname;
  MQTT_Topic[Topic_All] = System_Header + Topic_All_Text;
  MQTT_Topic[Topic_KeepAlive] = System_Header + Topic_KeepAlive_Text + Hostname;
  MQTT_Topic[Topic_Dobby] = System_Header + Topic_Dobby_Text;
  // Log
  MQTT_Topic[Topic_Log_Debug] = System_Header + "/Log/" + Hostname + Topic_Log_Debug_Text;
  MQTT_Topic[Topic_Log_Info] = System_Header + "/Log/" + Hostname + Topic_Log_Info_Text;
  MQTT_Topic[Topic_Log_Warning] = System_Header + "/Log/" + Hostname + Topic_Log_Warning_Text;
  MQTT_Topic[Topic_Log_Error] = System_Header + "/Log/" + Hostname + Topic_Log_Error_Text;
  MQTT_Topic[Topic_Log_Fatal] = System_Header + "/Log/" + Hostname + Topic_Log_Fatal_Text;
  // Devices
  MQTT_Topic[Topic_Ammeter] = System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname;
  MQTT_Topic[Topic_Button] = System_Header + System_Sub_Header + Topic_Button_Text + Hostname;
  MQTT_Topic[Topic_DHT] = System_Header + System_Sub_Header + Topic_DHT_Text + Hostname;
  MQTT_Topic[Topic_DC_Voltmeter] = System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname;
  MQTT_Topic[Topic_Dimmer] = System_Header + System_Sub_Header + Topic_Dimmer_Text + Hostname;
  MQTT_Topic[Topic_Distance] = System_Header + System_Sub_Header + Topic_Distance_Text + Hostname;
  MQTT_Topic[Topic_MQ] = System_Header + System_Sub_Header + Topic_MQ_Text + Hostname;
  MQTT_Topic[Topic_Relay] = System_Header + System_Sub_Header + Topic_Relay_Text + Hostname;
  MQTT_Topic[Topic_PIR] = System_Header + System_Sub_Header + Topic_PIR_Text + Hostname;
  MQTT_Topic[Topic_MAX31855] = System_Header + System_Sub_Header + Topic_MAX31855_Text + Hostname;
  MQTT_Topic[Topic_Switch] = System_Header + System_Sub_Header + Topic_Switch_Text + Hostname;
}


// ############################################################ MQTT_Subscribe() ############################################################
void MQTT_Subscribe(String Topic, bool Activate_Topic, byte SubTopics) {

  if (ArduinoOTA_Active == true) {
    return;
  }

  byte Topic_Number = 255;

  for (byte i = 0; i < MQTT_Topic_Number_Of; i++) {
    if (Topic == MQTT_Topic[i]) {
      Topic_Number = i;
      break;
    }
  }
  if (Topic_Number == 255) {
    Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Unknown Subscribe Topic: " + Topic);
    return;
  }

  MQTT_Topic_Subscribe_Active[Topic_Number] = Activate_Topic;
  MQTT_Topic_Subscribe_Subtopic[Topic_Number] = SubTopics;

  // Check if MQTT is connected
  if (MQTT_Client.connected() == false) {
    // if not then do nothing
    return;
  }

  String Subscribe_String = MQTT_Topic[Topic_Number];

  if (MQTT_Subscribtion_Active[Topic_Number] == false && MQTT_Topic_Subscribe_Active[Topic_Number] == true) {

    // Check if already subscribed
    if (MQTT_Subscribtion_Active[Topic_Number] == true && MQTT_Topic_Subscribe_Active[Topic_Number] == true) {
      Log(MQTT_Topic[Topic_Log_Warning] + "/MQTT", "Already subscribed to Topic: " + Subscribe_String);
      return;
    }
    // Add # or + to topic
    if (MQTT_Topic_Subscribe_Subtopic[Topic_Number] == PLUS) Subscribe_String = Subscribe_String + "/+";
    else if (MQTT_Topic_Subscribe_Subtopic[Topic_Number] == HASH) Subscribe_String = Subscribe_String + "/#";

    // Try to subscribe
    if (MQTT_Client.subscribe(Subscribe_String.c_str(), 0)) {
      Log(MQTT_Topic[Topic_Log_Info] + "/MQTT", "Subscribing to Topic: " + Subscribe_String + " ... OK");
      MQTT_Subscribtion_Active[Topic_Number] = true;
    }
    // Log failure
    else {
      Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Subscribing to Topic: " + Subscribe_String + " ... FAILED");
    }
  }
}


// ############################################################ MQTT_KeepAlive() ############################################################
void MQTT_KeepAlive() {

  // If the MQTT Client is not connected no reason to send try to send a keepalive
  // Dont send keepalives during updates
  if (MQTT_State != MQTT_State_Connected && ArduinoOTA_Active == true) return;

  // Create json buffer
  DynamicJsonBuffer jsonBuffer(220);
  JsonObject& root_KL = jsonBuffer.createObject();

  // encode json string
  root_KL.set("Hostname", Hostname);
  root_KL.set("IP", IP_To_String(WiFi.localIP()));
  root_KL.set("Uptime", millis());
  root_KL.set("FreeMemory", system_get_free_heap_size());
  root_KL.set("Software", Version);
  root_KL.set("IP", IP_To_String(WiFi.localIP()));
  root_KL.set("RSSI", WiFi.RSSI());

  String KeepAlive_String;

  root_KL.printTo(KeepAlive_String);

  Log(MQTT_Topic[Topic_KeepAlive], KeepAlive_String);

} // MQTT_KeepAlive()


// ############################################################ MQTT_Connect() ############################################################
void MQTT_Connect() {

  // Do nothing if OTA is active
  if (ArduinoOTA_Active == true) {
    return;
  }
  
  // Check WiFi status
  // If not connected do nothing
  else if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  // Connected to broker, subscribed and logged event
  if (MQTT_State == MQTT_State_Connected) {
    // Check if broker is still connected
    // Not connected
    if (MQTT_Client.connected() == false) {
      // Change MQTT_State
      MQTT_State = MQTT_State_Disconnecting;
    }
    // If connected do nothing
  }
  // Trying to connect to broker
  else if (MQTT_State == MQTT_State_Connecting) {
    // Check if connected to broker
    // Connected to broker but havent logged the event or subscribed
    if (MQTT_Client.connected() == true) {
      // Subscrive to topics
      for (byte i = 0; i < MQTT_Topic_Number_Of; i++) {
        MQTT_Subscribe(MQTT_Topic[i], MQTT_Topic_Subscribe_Active[i], MQTT_Topic_Subscribe_Subtopic[i]);
      }
      // Start MQTT_KeepAlive
      MQTT_KeepAlive_Ticker.attach(MQTT_KeepAlive_Interval, MQTT_KeepAlive);
      // Change MQTT State
      MQTT_State = MQTT_State_Connected;
    }
    // Not Connected
    // Try to connect
    else {
      if (MQTT_Reconnect_At > millis()) {
        return;
      }
      
      // Attempt to connect
      if (MQTT_Client.connect(Hostname.c_str(), MQTT_Username.c_str(), MQTT_Password.c_str(), String(MQTT_Topic[Topic_Log_Warning] + "/MQTT").c_str(), 0, false, "Will - Disconnected", true) == true) {
        // Log event
        Log(MQTT_Topic[Topic_Log_Info] + "/MQTT", "Connected to broker: " + MQTT_Broker);
        // Subscrive to topics
        for (byte i = 0; i < MQTT_Topic_Number_Of; i++) {
          MQTT_Subscribe(MQTT_Topic[i], MQTT_Topic_Subscribe_Active[i], MQTT_Topic_Subscribe_Subtopic[i]);
        }
        // Change MQTT State
        MQTT_State = MQTT_State_Connected;
        // Disable indicator led
        Indicator_LED(LED_MQTT, false);
        // Start MQTT_KeepAlive
        MQTT_KeepAlive_Ticker.attach(MQTT_KeepAlive_Interval, MQTT_KeepAlive);

      } 
      else {
        if (MQTT_State != MQTT_State_Error) {
          if (MQTT_Client.state() != MQTT_Last_Error) {
            // Log event
            Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Connection failed - Error text: " + MQTT_Error_Text(MQTT_Client.state()));
            // Reset subscribe status
            for (byte i = 0; i < MQTT_Topic_Number_Of; i++) MQTT_Subscribtion_Active[i] = false;
            // Change MQTT State
            MQTT_State = MQTT_State_Error;
            MQTT_Last_Error = MQTT_Client.state();
          }
        }
      }
      // Reset reconnect timer
      MQTT_Reconnect_At = millis() + MQTT_Reconnect_Interval;
    }
  }
  // Disconnected from broker
  else if (MQTT_State == MQTT_State_Disconnected) {
    if (WiFi.status() == WL_CONNECTED) {
      MQTT_State = MQTT_State_Connecting;
    }
  }
  else if (MQTT_State == MQTT_State_Disconnecting) {
    Log(MQTT_Topic[Topic_Log_Error] + "/MQTT", "Disconnected from Broker: '" + MQTT_Broker + "'");

    Indicator_LED(LED_MQTT, true);

    // Reset subscribe status
    for (byte i = 0; i < MQTT_Topic_Number_Of; i++) MQTT_Subscribtion_Active[i] = false;

    MQTT_KeepAlive_Ticker.detach();

    MQTT_State = MQTT_State_Disconnected;

    MQTT_Reconnect_At = millis() + MQTT_Reconnect_Interval;
  }
  else if (MQTT_State == MQTT_State_Error) {
    // Check if the error is recoverable
    // Fatal
    if (MQTT_Last_Error == MQTT_CONNECT_BAD_CREDENTIALS || MQTT_Last_Error == MQTT_CONNECT_UNAUTHORIZED) {
      Log(MQTT_Topic[Topic_Log_Fatal] + "/MQTT", "Bad username or password, unable to recover please check credentials");
    }
    // Try to recover
    else {
      MQTT_State = MQTT_State_Connecting;
      MQTT_Reconnect_At = millis() + MQTT_Reconnect_Interval;
    }
  }
  
} // MQTT_Connect()


// ############################################################ WiFi_Signal() ############################################################
// Post the devices WiFi Signal Strength
void WiFi_Signal() {

  Log(MQTT_Topic[Topic_Log_Info] + "/WiFi", "Signal Strength: " + String(WiFi.RSSI()));

} // WiFi_Signal()


// ############################################################ IP_Show() ############################################################
// Post the devices IP information
void IP_Show() {

  String IP_String;

  IP_String = "IP Address: " + IP_To_String(WiFi.localIP());
  IP_String = IP_String + " Subnetmask: " + IP_To_String(WiFi.subnetMask());
  IP_String = IP_String + " Gateway: " + IP_To_String(WiFi.gatewayIP());
  IP_String = IP_String + " DNS Server: " + IP_To_String(WiFi.dnsIP());
  IP_String = IP_String + " MAC Address: " + WiFi.macAddress();

  Log(MQTT_Topic[Topic_Log_Info] + "/IP", IP_String);
} // IP_Show()


// ############################################################ Pin_Monitor_State() ############################################################
void Pin_Monitor_State() {

  String Return_String;

  for (byte i = 0; i < Pin_Monitor_Pins_Number_Of; i++) {
    Return_String = Return_String + Pin_Monitor_Pins_Names[i] + ": " + Pin_Monitor_State_Text[Pin_Monitor_Pins_Active[i]];

    if (i != Pin_Monitor_Pins_Number_Of - 1) {
      Return_String = Return_String + " - ";
    }
  }

  Log(MQTT_Topic[Topic_Log_Info] + "/PinMonitor", Return_String);
} // Pin_Monitor_State()


// ############################################################ Pin_Monitor_Map() ############################################################
void Pin_Monitor_Map() {

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

    Log(MQTT_Topic[Topic_Log_Info] + "/PinMap", Pin_String);

} // Pin_Monitor_Map()


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


// ############################################################ Pin_Monitor() ############################################################
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
      Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");

      // Disable indicator led if pin D4 is used
      if (Number_To_Pin(Pin_Number) == "D4") {
        Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin D4 used, disabling indicator LED");

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
      Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");
      // Return state
      return Pin_SCL;
    }
    // Pin already used as I2C SCL
    else if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_SCL) {
      // Log event
      Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " already used as I2C SCL");
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
      Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is free");
      // Return state
      return Pin_SDA;
    }
    // Pin already used as I2C SDA
    else if (Pin_Monitor_Pins_Active[Selected_Pin] == Pin_SDA) {
      // Log event
      Log(MQTT_Topic[Topic_Log_Debug] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " already used as I2C SDA");
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
} // Pin_Monitor - Refferance only - Pin Name


// ############################################################ MQTT_Callback() ############################################################
void MQTT_Callback(char* topic, byte* payload, unsigned int length) {

  MQTT_RX_Queue_Topic.Push(topic);

  String Payload;

  for (byte i = 0; i < length; i++) {
    Payload = Payload + (char) payload[i];
  }
  
  MQTT_RX_Queue_Payload.Push(Payload);

} // MQTT_Callback()


// ################################### MQTT_Commands() ###################################
bool MQTT_Commands(String &Topic, String &Payload) {

  bool Unknown_Command = false;

  // Ignore none commands
  if (Topic.indexOf(MQTT_Topic[Topic_Commands]) == -1) {
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
    else Unknown_Command = true;
  }

  else if (Topic == "FS") {
    if (FS_Commands(Payload) == true) return true;
    else Unknown_Command = true;
  }

  else if (Topic == "Blink") {
    Indicator_LED_Blink(Payload.toInt());
    Unknown_Command = false;
  }

  else if (Topic == "Hostname") {
    Hostname = Payload;
    FS_Config_Drop();
    Log(MQTT_Topic[Topic_Log_Info] + "/System", "Hostname changed to: '" + Hostname + "' Reboot required rebooting in 2 seconds");
    Reboot(2000);
    Unknown_Command = true;
  }

  else if (Topic == "Version") {
    if (Payload == "Show") Log(MQTT_Topic[Topic_Log_Info], "Running Dobby - Wemos D1 Mini firmware version: " + String(Version));
    // if (Payload == "Update") Version_Update();
    else Unknown_Command = true;
  }

  else if (Topic == "IP") {
    if (Payload == "Show") IP_Show();
    else Unknown_Command = true;
  }

  // else if (Topic == "Dimmer/FadeJump") {
  //   Dimmer_Fade_Jump = Payload.toInt();
  //   Log(MQTT_Topic[Topic_Log_Debug] + "/Dimmer", "Dimmer Fade Jump changed to: " + String(Dimmer_Fade_Jump));
  // }

  // else if (Topic == "Dimmer/FadeJumpDelay") {
  //   Dimmer_Fade_Jump_Delay = Payload.toInt();
  //   Log(MQTT_Topic[Topic_Log_Debug] + "/Dimmer", "Dimmer Fade Jump Delay changed to: " + String(Dimmer_Fade_Jump_Delay));
  // } // Dimmer


  else if (Topic == "FSConfig") {
    if (Payload == "Save") FS_Config_Save();
    else if (Payload == "Drop") FS_Config_Drop();
    else Unknown_Command = true;
  }


  else if (Topic == "PinMonitor") {
    if (Payload == "State") Pin_Monitor_State();
    if (Payload == "Map") Pin_Monitor_Map();
    else Unknown_Command = true;
  }


  else if (Topic == "WiFi") {
    if (Payload == "Signal") WiFi_Signal();
    else Unknown_Command = true;
  }


  else if (Topic == "Test") {

    Log("/Test", "MARKER");

  } // Test

  if (Unknown_Command == true) {
    Log(MQTT_Topic[Topic_Log_Debug] + "/Commands", "Unknown command. " + Topic + " - " + Payload);
    return false;
  }

  return true;

} // MQTT_Commands()


// ############################################################ MQTT_Queue_Check() ############################################################
void MQTT_Queue_Check() {

  if (MQTT_RX_Queue_Topic.Queue_Is_Empthy == false) {

    String Topic = MQTT_RX_Queue_Topic.Pop();
    String Payload = MQTT_RX_Queue_Payload.Pop();

    if (MQTT_Commands(Topic, Payload) == true) return;
    else if (Relay(Topic, Payload) == true) return;
    else if (Dimmer(Topic, Payload) == true) return;
    else if (Switch(Topic, Payload) == true) return;
  }
  
} // MQTT_Queue_Check()


// ############################################################ MQTT_Loop() ############################################################
void MQTT_Loop() {
  // Check connection
  if (!MQTT_Client.connected()) {
    MQTT_Connect();
  }
  // Run loop
  MQTT_Client.loop();

  // Check if there is incomming messages in the queue
  MQTT_Queue_Check();

} // MQTT_Loop()


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
bool Dimmer(String &Topic, String &Payload) {

  if (Dimmer_Configured == false) {
    return false;
  }

  if (Topic.indexOf(MQTT_Topic[Topic_Dimmer]) != -1) {

    Topic.replace(MQTT_Topic[Topic_Dimmer] + "/", "");

    byte Selected_Dimmer = Topic.toInt();

    // Ignore all requests thats larger then Dimmer_Max_Number_Of
    if (Selected_Dimmer >= 1 && Selected_Dimmer <= Dimmer_Max_Number_Of) {
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


// ############################################################ Relay_Auto_OFF_Check() ############################################################
void Relay_Auto_OFF_Check(byte Selected_Relay) {

  if (Relay_Pin_Auto_Off_Delay[Selected_Relay - 1] != false) {
    Relay_Auto_OFF_At[Selected_Relay - 1] = millis() + Relay_Pin_Auto_Off_Delay[Selected_Relay - 1];
    Relay_Auto_OFF_Active[Selected_Relay - 1] = true;
  }
} // _Relay_Auto_OFF_Check()


// ############################################################ Relay() ############################################################
bool Relay(String &Topic, String &Payload) {

  if (Relay_Configured == false) {
    return false;
  }

  else if (Topic.indexOf(MQTT_Topic[Topic_Relay]) != -1) {

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
        return true;
      }

      else if(Is_Valid_Number(Payload) == true) {
        byte State = Payload.toInt();

        if (State > 2) {
          Log(MQTT_Topic[Topic_Log_Error] + "/Relay", "Relay - Invalid command entered");
          return true;
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
  }
  return false;
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

  if (Button_Configured == true || ArduinoOTA_Active == true) {

    byte Button_Pressed = Button_Pressed_Check();

    if (Button_Pressed == 254 || Button_Pressed == 255) {
      // 255 = Unconfigured Pin
      // 254 = No button pressed
      return false;
    }

    if (Button_Pressed < Button_Max_Number_Of) {

      String Topic = Button_Target[Button_Pressed].substring(0, Button_Target[Button_Pressed].indexOf("&"));
      String Payload = Button_Target[Button_Pressed].substring(Button_Target[Button_Pressed].indexOf("&") + 1, Button_Target[Button_Pressed].length());

      MQTT_Client.publish(Topic.c_str(), Payload.c_str());

      return true;
    }
  }

  return false;

} // Button_Loop


// ############################################################ Switch() ############################################################
bool Switch(String &Topic, String &Payload) {

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
  if (Switch_Configured == false || ArduinoOTA_Active == true) {
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
          MQTT_Client.publish(Topic.c_str(), Payload.c_str());

        }
      }
    }
    Switch_Ignore_Input_Untill = millis() + Switch_Refresh_Rate;
  }
  return true;
} // Switch_Loop()


// ############################################################ MQ_Loop() ############################################################
void MQ_Loop() {

  // Do nothing if its not configured
  if (MQ_Configured == false || ArduinoOTA_Active == true) {
    return;
  }

  // // Set currernt value
  MQ_Current_Value = analogRead(MQ_Pin_A0);
  // // Check min/max
  MQ_Value_Min = min(MQ_Current_Value, MQ_Value_Min);
  MQ_Value_Max = max(MQ_Current_Value, MQ_Value_Max);;

}  // MQ_Loop()


// ############################################################ MQ() ############################################################
bool MQ(String &Topic, String &Payload) {

  // Do nothing if its not configured
  if (MQ_Configured == false) {
    return false;
  }

  // If Values = -1 no readings resived form sensor so disabling it
  else if (MQ_Current_Value == -1) {
    // Disable sensor
    MQ_Configured = false;
    // Log Error
    Log(MQTT_Topic[Topic_Log_Error] + "/MQ", "Never got a readings from the sensor disabling it.");
    // Detatch ticket
    MQ_Ticker.detach();
    // Return
    return false;
  }

  // Check topic
  else if (Topic == MQTT_Topic[Topic_MQ]) {

    // Trim Payload from garbage chars
    Payload = Payload.substring(0, Payload.indexOf(";"));

    // State request
    if (Payload == "?") {
      Log(MQTT_Topic[Topic_MQ] + "/State", String(MQ_Current_Value));
      return true;
    }
    // Min/Max request
    else if (Payload == "json") {

      // Create json buffer
      DynamicJsonBuffer jsonBuffer(80);
      JsonObject& root_MQ = jsonBuffer.createObject();

      // encode json string
      root_MQ.set("Current", MQ_Current_Value);
      root_MQ.set("Min", MQ_Value_Min);
      root_MQ.set("Max", MQ_Value_Max);

      // Reset values
      MQ_Value_Min = MQ_Current_Value;
      MQ_Value_Max = MQ_Current_Value;

      String MQ_String;

      root_MQ.printTo(MQ_String);

      Log(MQTT_Topic[Topic_MQ] + "/json/State", MQ_String);

      return true;
    }
  }
  return false;
} // MQ


// ############################################################ setup() ############################################################
void setup() {
  
  // ------------------------------ Serial ------------------------------
  Serial.setTimeout(100);
  Serial.begin(115200);
  Serial.println();

  Log(MQTT_Topic[Topic_Log_Info], "Booting Dobby - Wemos D1 Mini firmware version: " + String(Version));

  // ------------------------------ Indicator_LED ------------------------------
  if (Indicator_LED_Configured == true) {
    pinMode(D4, OUTPUT);
    Indicator_LED(LED_Config, true);
  }

  // ------------------------------ FS Config ------------------------------
  SPIFFS.begin();

  Serial_CLI_Boot_Message(Serial_CLI_Boot_Message_Timeout);

  FS_Config_Load();

  Base_Config_Check();

  // ------------------------------ WiFi ------------------------------
  WiFi_Setup();


  // ------------------------------ ArduinoOTA ------------------------------
  ArduinoOTA_Setup();
    

  // ------------------------------ MQTT ------------------------------
  MQTT_Client.setServer(String_To_IP(MQTT_Broker), MQTT_Port.toInt());
  MQTT_Client.setCallback(MQTT_Callback);


  // ------------------------------ FS Config UDP ------------------------------
  UDP_Client.begin(FS_Config_UDP_Port);
  
  
  // Disable indicator led
  Indicator_LED(LED_Config, false);

} // setup()


// ############################################################ loop() ############################################################
void loop() {

  // OTA
  ArduinoOTA.handle();

  // MQTT
  MQTT_Loop();

  // FS Config
  FS_Config_UDP_Loop();

  // Devices
  Relay_Auto_OFF_Loop();
  Button_Loop();
  Switch_Loop();

  FTP_Server.handleFTP();        //make sure in loop you call handleFTP()!!  

} // loop()
