
// Releaed under The GNU General Public License v3.0

#include <Arduino.h>
extern "C" {
  #include "user_interface.h"
}

// ---------------------------------------- Dobby ----------------------------------------
#define Version 1.28

String Hostname = "NotConfigured";
String System_Header = "";
String System_Sub_Header = "";
String Config_ID = "0";

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

#define Config_Json_Max_Buffer_Size 2048
bool Config_json_Loaded = false;

#define FS_Confing_File_Name "/Dobby.json"

// ------------------------------------------------------------ MQTT ------------------------------------------------------------
#include <AsyncMqttClient.h>

AsyncMqttClient MQTT_Client;
Ticker mqttReconnectTimer;

String MQTT_Broker = "0.0.0.0";
String MQTT_Port = "";

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
#define Topic_Error 9
#define Topic_Button 10
#define Topic_Dobby 11
#define Topic_System 12
#define Topic_Config 13

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
#define Topic_Error_Text "/Error/"
#define Topic_Button_Text "/Button/"
#define Topic_Dobby_Text "/Commands/Dobby/"
#define Topic_System_Text "/System/"

const byte MQTT_Topic_Number_Of = 14;
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
  System_Header + System_Sub_Header + Topic_Error_Text + Hostname,
  System_Header + System_Sub_Header + Topic_Button_Text + Hostname,
  System_Header + Topic_Dobby_Text,
  System_Header + Topic_System_Text + Hostname
};

bool MQTT_Topic_Subscribe_Active[MQTT_Topic_Number_Of] = {
  true,
  true,
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
  true
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
  NONE
};

bool MQTT_Subscribtion_Active[MQTT_Topic_Number_Of] = {
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
  false,
  false,
  false
};

#define MQTT_Reconnect_Delay 5 // in secounds

#define MQTT_Boot_Wait_For_Connection 15000

bool MQTT_Config_Requested = false;


// ------------------------------------------------------------ MQTT_Allow_Flash() ------------------------------------------------------------
Ticker MQTT_Allow_Flash_Ticker;
bool Allow_Flash = false;

unsigned long MQTT_Allow_Flash_Delay = 30000;


// ------------------------------------------------------------ ESP_Reboot() ------------------------------------------------------------
Ticker ESP_Reboot_Ticker;


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

unsigned long previousMillis = 0;            // When the sensor was last read
const long interval = 2000;                  // Wait this long until reading again


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

bool Distance_Sensor_State[Distance_Max_Number_Of];

unsigned long Distance_Auto_OFF_At[Distance_Max_Number_Of] = {0, 0, 0};
unsigned long Distance_Auto_OFF_Delay[Distance_Max_Number_Of];
bool Distance_Auto_OFF_Active[Distance_Max_Number_Of];

unsigned long Distnace_Sensor_Read_At[Distance_Max_Number_Of] = {0, 0, 0};


// ------------------------------------------------------------ Dimmer ------------------------------------------------------------
#define Dimmer_Max_Number_Of 6
bool Dimmer_Configured = false;
byte Dimmer_Pins[Dimmer_Max_Number_Of] = {255, 255, 255, 255, 255, 255};

int Dimmer_State[Dimmer_Max_Number_Of];
byte Dimmer_Procent[Dimmer_Max_Number_Of];

byte Dimmer_Fade_Jump = 20;
byte Dimmer_Fade_Jump_Delay = 40;

// ------------------------------------------------------------ Pin_Monitor ------------------------------------------------------------
#define Pin_Monitor_Pins_Number_Of 9
byte Pin_Monitor_Pins_List[Pin_Monitor_Pins_Number_Of] = {D1, D2, D3, D4, D5, D6, D7, D8, A0};
bool Pin_Monitor_Pins_Active[Pin_Monitor_Pins_Number_Of] = {false, false, false, false, false, false, false, false, false};


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

float Indicator_LED_Hertz;

bool Indicator_LED_State = true;

unsigned int Indicator_LED_Blink_For = 250;

byte Indicator_LED_Blinks_Active = false;
byte Indicator_LED_Blinks_Left;

#define LED_OFF 0
#define LED_MQTT 0.5
#define LED_WiFi 1
#define LED_Config 2.5


// ------------------------------------------------------------ Update() ------------------------------------------------------------
Ticker Update_Ticker;


// ------------------------------------------------------------ CLI ------------------------------------------------------------
#define Command_List_Length 18
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
  "fs list",
  "fs cat",
  "fs format",
  "fs config drop",
  "show mac",
  "save",
  "check",
  "reboot"};

String CLI_Input_String;
bool CLI_Command_Complate = false;

#define Serial_CLI_Boot_Message_Timeout 5


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
// Returns "HIGH" of 1 and "LOW" if 0
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
  MQTT_Topic[Topic_Error] = System_Header + System_Sub_Header + Topic_Error_Text + Hostname;
  MQTT_Topic[Topic_Button] = System_Header + System_Sub_Header + Topic_Button_Text + Hostname;
  MQTT_Topic[Topic_Dobby] = System_Header + Topic_Dobby_Text;
  MQTT_Topic[Topic_System] = System_Header + Topic_System_Text + Hostname;
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

  if (MQTT_Client.connected() == true) {
    // State message post as retained message
    if (Topic.indexOf("/State") != -1) {
      MQTT_Client.publish(Topic.c_str(), 0, true, Log_Text.c_str());
    }
    // Post as none retained message
    else MQTT_Client.publish(Topic.c_str(), 0, false, Log_Text.c_str());
  }

  Serial.println(Topic + " - " + Log_Text);

} // Log()

void Log(String Topic, int Log_Text) {
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
    Log(MQTT_Topic[Topic_Error] + "/IndicatorLED", "Indicator LED not configured");
  }

  Log(MQTT_Topic[Topic_System] + "/IndicatorLED", "Bliking " + String(Number_Of_Blinks) + " times");

  Indicator_LED_Blinks_Active = true;
  Indicator_LED_Blinks_Left = Number_Of_Blinks - 1;

  Indicator_LED_Blink(); // for instant reaction then attach the ticket below
  Indicator_LED_Blink_Ticker.attach(1, Indicator_LED_Blink);

} // Indicator_LED_Blink()


/* ############################################################ Indicator_LED() ############################################################
      Blinkes the blue onboard led based on the herts specified in a float
      NOTE: Enabling this will disable pind D4
      0 = Turn off
*/

void Indicator_LED(float Hertz) {

  if (Indicator_LED_Configured == false) {
    Log(MQTT_Topic[Topic_Error] + "/IndicatorLED", "Indicator LED not configured");
    return;
  }

  // Turn Off
  if (Hertz == 0) {
    Indicator_LED_Blink_Ticker.detach();
    digitalWrite(D4, HIGH);
  }

  else {
    Indicator_LED_Blink_Ticker.attach(Hertz, Indicator_LED_Blink);
  }
} // Indicator_LED()


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

  if (Button_Configured == true) {

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

    }
  }

  return false;

} // Button_Loop


// ############################################################ Pin_Monitor_String() ############################################################
// Will return false if pin is in use or invalid
String Number_To_Pin(byte Pin_Number) {

  Serial.println("Pin_Number: " + String(Pin_Number));

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
bool Pin_Monitor(byte Pin_Number) {

  byte Selected_Pin = 255;

  // Find seleced Pin
  for (byte i = 0; i < Pin_Monitor_Pins_Number_Of; i++) {
    if (Pin_Number == Pin_Monitor_Pins_List[i]) {
      Selected_Pin = i;
      break;
    }
  }

  // On list check
  if (Selected_Pin == 255) {
    Log(MQTT_Topic[Topic_Error] + "/PinMonitor", "Pin " + String(Pin_Number) + " not on pin list");
    return false;
  }

  // In use check
  if (Pin_Monitor_Pins_Active[Pin_Number] == true) {
    Log(MQTT_Topic[Topic_Error] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " is in use");
    return false;
  }

  // Not in use
  else {
    Pin_Monitor_Pins_Active[Pin_Number] = true;
    Log(MQTT_Topic[Topic_System] + "/PinMonitor", "Pin " + Number_To_Pin(Pin_Number) + " ok");
    return true;
  }
} // Pin_Monitor


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
      Log(MQTT_Topic[Topic_Error] + "/FS/del", "Unable to delete: " + File_Path);
      return false;
    }
  }
  return false;
} // FS_cat()


// ############################################################ FS_File_Check() ############################################################
bool FS_File_Check(String File_Path, bool Report_Error) {

  if (SPIFFS.exists(File_Path)) return true;

  if (Report_Error == true) {
    Log(MQTT_Topic[Topic_Error] + "/FS/FileCheck", "FS Unable to find file: " + File_Path);
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


// ############################################################ Reboot() ############################################################
void Reboot(unsigned long Reboot_In) {

  Log(MQTT_Topic[Topic_System], "Kill command issued, rebooting in " + String(Reboot_In / 1000) + " seconds");

  ESP_Reboot_Ticker.once_ms(Reboot_In, ESP_Reboot);

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



// ############################################################ Echo() ############################################################
// Reads the distance
int Echo(byte Echo_Pin_Trigger, byte Echo_Pin_Echo) {

  // Clears the Echo_Pin_Trigger
  digitalWrite(Echo_Pin_Trigger, LOW);
  delayMicroseconds(2);

  // Sets the Echo_Pin_Trigger on HIGH state for 10 micro seconds
  digitalWrite(Echo_Pin_Trigger, HIGH);
  delayMicroseconds(10);
  digitalWrite(Echo_Pin_Trigger, LOW);

  // Reads the Echo_Pin_Echo, returns the sound wave travel time in microseconds
  float Duration = pulseIn(Echo_Pin_Echo, HIGH);

  // Calculating the distance
  float Distance = (Duration / 2) * 0.0343;

  if (Distance > 400) return -1;

  return Distance;

} // Echo


// ############################################################ Distance() ############################################################
// Handles MQTT Read request
bool Distance(String Topic, String Payload) {

    if (Topic.indexOf(MQTT_Topic[Topic_Distance]) != -1 && Payload.indexOf("?") != -1) {
      // Ignore state publish from localhost
      if (Topic.indexOf("/State") == -1)  {

        Topic.replace(MQTT_Topic[Topic_Distance] + "/", "");

        if (Topic.toInt() == 0 || Topic.toInt() > Distance_Max_Number_Of) {
          Log(MQTT_Topic[Topic_Error] + "/Distance", "Distance Sensor " + Topic + " is not a valid distance sensor");
          return true;
        }

        if (Distance_Pins_Trigger[Topic.toInt() - 1] == 0 || Distance_Pins_Echo[Topic.toInt() - 1] == 0) {
          Log(MQTT_Topic[Topic_Error] + "/Distance", "Distance Sensor " + Topic + " is not configured");
          return true;
        }

        int Distance = Echo(Distance_Pins_Trigger[Topic.toInt() - 1], Distance_Pins_Echo[Topic.toInt() - 1]);

        Log(MQTT_Topic[Topic_Distance] + "/" + Topic + "/State", String(Distance));
        return true;
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

      int Distance = Echo(Distance_Pins_Trigger[i], Distance_Pins_Echo[i]);

      if (Distance == -1) {
        Log(MQTT_Topic[Topic_Error] + "/Distance", "Distance Sensor - Echo mesure off");
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
        Log(MQTT_Topic[Topic_Error] + "/MQTT", "Subscribing to Topic: " + Subscribe_String + "  ... FAILED");
      }
    }

    if (MQTT_Subscribtion_Active[Topic_Number] == true && MQTT_Topic_Subscribe_Active[Topic_Number] == true) {
      Log(MQTT_Topic[Topic_Error] + "/MQTT", "Already subscribed to Topic: " + Subscribe_String);
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
bool Relay(String Topic, String Payload) {

  if (Relay_Configured == false) {
    Serial.println("MARKER222");
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

      else if(isValidNumber(Payload) == true) {
        byte State = Payload.toInt();

        if (State > 2) {
          Log(MQTT_Topic[Topic_Error] + "/Relay", "Relay - Invalid command entered");
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


// ############################################################ DHT_Read() ############################################################
void DHT_Read(byte DHT_Selected) {

  if (DHT_Pins[DHT_Selected - 1] != 255) {
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= interval) {
      // Save the last time you read the sensor
      previousMillis = currentMillis;

      byte temperature = 0;
      byte humidity = 0;
      int err = SimpleDHTErrSuccess;
      if ((err = dht22.read(DHT_Pins[DHT_Selected - 1], &temperature, &humidity, NULL)) != SimpleDHTErrSuccess) {
        Log(MQTT_Topic[Topic_Error] + "/DHT/" + String(DHT_Selected), "Read DHT22 failed, Error: " + err);
        return;
      }

      // Humidity
      Log(MQTT_Topic[Topic_DHT] + "/" + String(DHT_Selected) + "/Humidity", String(humidity));

      // Temperature
      Log(MQTT_Topic[Topic_DHT] + "/" + String(DHT_Selected) + "/Temperature", String(temperature));
    }
  }

} // DHT_Read()


// ############################################################ DHT() ############################################################
bool DHT(String Topic, String Payload) {
  if (Topic.indexOf(MQTT_Topic[Topic_DHT]) != -1) {

    Topic.replace(MQTT_Topic[Topic_DHT] + "/", "");

    if (Topic.toInt() <= DHT_Max_Number_Of) {
      DHT_Read(Topic.toInt());
      return true;
    }

  }
  return false;
} // DHT


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

  // Create json buffer
  DynamicJsonBuffer jsonBuffer(220);
  JsonObject& root_KL = jsonBuffer.createObject();

  // encode json string
  root_KL.set("Hostname", Hostname);
  root_KL.set("Uptime", millis());
  root_KL.set("FreeMemory", system_get_free_heap_size());
  root_KL.set("Software", Version);

  String KeepAlive_String;

  root_KL.printTo(KeepAlive_String);

  Log(MQTT_Topic[Topic_KeepAlive], KeepAlive_String);

} // MQTT_KeepAlive()


// ############################################################ onMqttConnect() ############################################################
void onMqttConnect(bool sessionPresent) {
  Log(MQTT_Topic[Topic_System] + "/MQTT", "Connected to Broker: '" + MQTT_Broker + "'");

  Indicator_LED(LED_OFF);

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


} // onMqttConnect()


// ############################################################ connectToMqtt() ############################################################
void connectToMqtt() {
  Log(MQTT_Topic[Topic_System] + "/MQTT", "Connecting to Broker: '" + MQTT_Broker + "' ...");
  MQTT_Client.connect();
}


// ############################################################ onMqttDisconnect() ############################################################
void onMqttDisconnect(AsyncMqttClientDisconnectReason reason) {

  Log(MQTT_Topic[Topic_Error] + "/MQTT", "Disconnected from Broker: '" + MQTT_Broker + "'");

  if (Indicator_LED_Configured == true) Indicator_LED(LED_MQTT);

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

  if (Dimmer_Configured == true) {
    root_Config.set("Button_Pins", Byte_ArrayToString(Button_Pins));
    root_Config.set("Button_Target", Button_Target);
  }


  String Return_String;
  root_Config.printTo(Return_String);
  return Return_String;

} // FS_Config_Build()



// #################################### FS_Config_Save() ####################################
bool FS_Config_Save() {

  File configFile = SPIFFS.open(FS_Confing_File_Name, "w");
  if (!configFile) {
    Log(MQTT_Topic[Topic_System] + "/FSConfig", "Failed to open config file for writing");
    return false;
  }

  configFile.print(FS_Config_Build());
  configFile.close();

  Log(MQTT_Topic[Topic_System] + "/FSConfig", "Saved to SPIFFS");

  return true;
}



// ############################################################ Device_Config() ############################################################
void Device_Config(String Setting, String Value) {

  String Old_Value;

  // Value = "" = no reason to continue
  if (Value == "") return;

  // ############### System ###############
  if (Setting == "Hostname") {
    if (Value == Hostname) return;
    Old_Value = Hostname;
    Hostname = Value;
    Rebuild_MQTT_Topics();
  }

  else if (Setting == "System_Header") {
    if (Value == System_Header) return;
    Old_Value = System_Header;
    System_Header = Value;
    Rebuild_MQTT_Topics();
  }

  else if (Setting == "System_Sub_Header") {
    if (Value == System_Sub_Header) return;
    Old_Value = System_Sub_Header;
    System_Sub_Header = Value;
    Rebuild_MQTT_Topics();
  }

  else if (Setting == "WiFi_SSID") {
    if (Value == WiFi_SSID) return;
    Old_Value = WiFi_SSID;
    WiFi_SSID = Value;
  }
  else if (Setting == "WiFi_Password") {
    if (Value == WiFi_Password) return;
    Old_Value = WiFi_Password;
    WiFi_Password = Value;
  }
  else if (Setting == "MQTT_Broker") {
    if (Value == MQTT_Broker) return;
    Old_Value = MQTT_Broker;
    MQTT_Broker = Value;
  }
  else if (Setting == "MQTT_Port") {
    if (Value == MQTT_Port) return;
    Old_Value = MQTT_Port;
    MQTT_Port = Value;
  }
  else if (Setting == "MQTT_Username") {
    if (Value == MQTT_Username) return;
    Old_Value = MQTT_Username;
    MQTT_Username = Value;
  }
  else if (Setting == "MQTT_Password") {
    if (Value == MQTT_Password) return;
    Old_Value = MQTT_Password;
    MQTT_Password = Value;
  }
  else if (Setting == "MQTT_Allow_Flash_Password") {
    Old_Value = MQTT_Allow_Flash_Password;
    MQTT_Allow_Flash_Password = Value;
  }

  else if (Setting == "MQTT_KeepAlive_Interval") {
    if ((unsigned long)Value.toInt() * 1000 == MQTT_KeepAlive_Interval) return;
    Old_Value = MQTT_KeepAlive_Interval;
    MQTT_KeepAlive_Ticker.detach();
    MQTT_KeepAlive_Interval = Value.toInt() * 1000;
    MQTT_KeepAlive_Ticker.attach_ms(MQTT_KeepAlive_Interval, MQTT_KeepAlive);
  }

  // ############### Byzzer ###############
  else if (Setting == "Buzzer_Pins") {
    // FIX add check if old value = new calue then ignore
    Old_Value = Buzzer_Pins;
    Buzzer_Pins = Value.toInt();
    if (Pin_Monitor(Buzzer_Pins) == true) {
      pinMode(Buzzer_Pins, OUTPUT);
      MQTT_Subscribe(MQTT_Topic[Topic_Buzzer], true, NONE);
      Buzzer_Configured = true;
    }
  }

  // ############### DHT ###############
  else if (Setting == "DHT_Pins") {
    Old_Value = Byte_ArrayToString(DHT_Pins);
    MQTT_Settings_Set(DHT_Pins, DHT_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/DHT", "DHT Pins");
    MQTT_Subscribe(MQTT_Topic[Topic_DHT], true, PLUS);
    DHT_Configured = true;
  }


  // ############### Relay ###############
  else if (Setting == "Relay_On_State") {
    Old_Value = Relay_On_State;
    Relay_On_State = Value.toInt();
    MQTT_Subscribe(MQTT_Topic[Topic_Relay], true, PLUS);
  }

  else if (Setting == "Relay_Pins") {
    Old_Value = Byte_ArrayToString(Relay_Pins);
    MQTT_Settings_Set(Relay_Pins, Relay_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Relay", "Relay Pins");
    // Set pinMode
    for (byte i = 0; i < Relay_Max_Number_Of; i++) {
      if (Relay_Pins[i] != 255 && Pin_Monitor(Relay_Pins[i]) == true) {
          pinMode(Relay_Pins[i], OUTPUT);
          digitalWrite(Relay_Pins[i], !Relay_On_State);
          Relay_Configured = true;
      }
    }
  }
  else if (Setting == "Relay_Pin_Auto_Off") {
    Old_Value = Bool_ArrayToString(Relay_Pin_Auto_Off);
    MQTT_Settings_Set(Relay_Pin_Auto_Off, Relay_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Relay", "Relay Pins Auto Off");
  }
  else if (Setting == "Relay_Pin_Auto_Off_Delay") {
    Old_Value = ul_ArrayToString(Relay_Pin_Auto_Off_Delay);
    MQTT_Settings_Set(Relay_Pin_Auto_Off_Delay, Relay_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Relay", "Relay Pins Auto Off Delay");
  }


  // ############### Distance ###############
  else if (Setting == "Distance_Pins_Trigger") {
    Old_Value = Byte_ArrayToString(Distance_Pins_Trigger);
    MQTT_Subscribe(MQTT_Topic[Topic_Distance], true, PLUS);
    MQTT_Settings_Set(Distance_Pins_Trigger, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Trigger");
    // Set pinMode
    for (byte i = 0; i < Distance_Max_Number_Of; i++) {
      if (Distance_Pins_Trigger[i] != 255 && Pin_Monitor(Distance_Pins_Trigger[i]) == true) {
        pinMode(Distance_Pins_Trigger[i], OUTPUT);
      }
    }
  }

  else if (Setting == "Distance_Pins_Echo") {
    Old_Value = Byte_ArrayToString(Distance_Pins_Echo);
    MQTT_Settings_Set(Distance_Pins_Echo, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Echo");
    // Set pinMode
    for (byte i = 0; i < Distance_Max_Number_Of; i++) {
      if (Distance_Pins_Echo[i] != 255 && Pin_Monitor(Distance_Pins_Echo[i]) == true) {
        pinMode(Distance_Pins_Echo[i], INPUT);
      }
    }
  }

  else if (Setting == "Distance_Trigger_At") {
    Old_Value = int_ArrayToString(Distance_Trigger_At);
    MQTT_Settings_Set(Distance_Trigger_At, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Trigger At");
  }
  else if (Setting == "Distance_Target_ON") {
    Old_Value = String_ArrayToString(Distance_Target_ON);
    MQTT_Settings_Set(Distance_Target_ON, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Target ON");
  }
  else if (Setting == "Distance_Target_OFF") {
    Old_Value = String_ArrayToString(Distance_Target_OFF);
    MQTT_Settings_Set(Distance_Target_OFF, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Target OFF");
  }
  else if (Setting == "Distance_Refresh_Rate") {
    Old_Value = ul_ArrayToString(Distance_Refresh_Rate);
    MQTT_Settings_Set(Distance_Refresh_Rate, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Refresh Rate");
  }
  else if (Setting == "Distance_Auto_OFF_Delay") {
    Old_Value = ul_ArrayToString(Distance_Auto_OFF_Delay);
    MQTT_Settings_Set(Distance_Auto_OFF_Delay, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Auto OFF Delay");
  }
  else if (Setting == "Distance_Auto_OFF_Active") {
    Old_Value = Bool_ArrayToString(Distance_Auto_OFF_Active);
    MQTT_Settings_Set(Distance_Auto_OFF_Active, Distance_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Distance", "Distance Auto OFF Active");
  }
  else if (Setting == "Dimmer_Pins") {
    MQTT_Subscribe(MQTT_Topic[Topic_Dimmer], true, PLUS);
    MQTT_Settings_Set(Dimmer_Pins, Dimmer_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Pins");
    // Set pinMode
    for (byte i = 0; i < Dimmer_Max_Number_Of; i++) {
      if (Dimmer_Pins[i] != 255) {
        if (Pin_Monitor(Dimmer_Pins[i]) == true) {
          pinMode(Dimmer_Pins[i], OUTPUT);
          analogWrite(Dimmer_Pins[i], 0);
          Dimmer_State[i] = 0;
        }
      }
    }
  }

  else if (Setting == "Button_Pins") {
    MQTT_Settings_Set(Button_Pins, Button_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Button", "Button Pins");

    // Set pinMode
    for (byte i = 0; i < Button_Max_Number_Of; i++) {
      if (Button_Pins[i] != 255) {
        if (Pin_Monitor(Button_Pins[i]) == true) {
          pinMode(Button_Pins[i], INPUT_PULLUP);
        }
      }
    }
  }
  else if (Setting == "Button_Target") MQTT_Settings_Set(Button_Target, Button_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Button", "Button Target");

  // Config_ID is last config so will reboot if needed and save config
  else if (Setting == "Config_ID") {
    if (Value == "") {
      Value = "0";
    }
    Config_ID = Value;
    // Only save if triggered after config is loaded
    if (Config_json_Loaded == true) FS_Config_Save();
  }

  else {
    Log(MQTT_Topic[Topic_Error] + "/DeviceConfig", "Unknown configuration: " + Setting);
    return;
  }

  // Log value change
  Log(MQTT_Topic[Topic_System] + "/Dobby", "'" + Setting + "' changed from: " + Old_Value + " to: " + Value);


} // Device_Config()


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

  // // ############### Byzzer ###############
  if (root.get<String>("Buzzer_Pins") != "") {
    Buzzer_Pins = root.get<byte>("Buzzer_Pins");
    if (Pin_Monitor(Buzzer_Pins) == true) {
      pinMode(Buzzer_Pins, OUTPUT);
      MQTT_Subscribe(MQTT_Topic[Topic_Buzzer], true, NONE);
      Buzzer_Configured = true;
    }
  }

  // ############### DHT ###############
  if (root.get<String>("DHT_Pins") != "") {
    MQTT_Settings_Set(DHT_Pins, DHT_Max_Number_Of, root.get<String>("DHT_Pins"), MQTT_Topic[Topic_System] + "/DHT", "DHT Pins");
    MQTT_Subscribe(MQTT_Topic[Topic_DHT], true, PLUS);
    DHT_Configured = true;
  }


  // ############### Relay ###############
  if (root.get<String>("Relay_On_State") != "") {
    Relay_On_State = root.get<bool>("Relay_On_State");

    // Relay pins
    MQTT_Settings_Set(Relay_Pins, Relay_Max_Number_Of, root.get<String>("Relay_Pins"), MQTT_Topic[Topic_System] + "/Relay", "Relay Pins");
    for (byte i = 0; i < Relay_Max_Number_Of; i++) {
      if (Relay_Pins[i] != 255 && Pin_Monitor(Relay_Pins[i]) == true) {
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
    Relay_Configured = true;
    MQTT_Subscribe(MQTT_Topic[Topic_Distance], true, PLUS);
    MQTT_Settings_Set(Distance_Pins_Trigger, Distance_Max_Number_Of, root.get<String>("Distance_Pins_Trigger"), MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Trigger");
    // Set pinMode
    for (byte i = 0; i < Distance_Max_Number_Of; i++) {
      if (Distance_Pins_Trigger[i] != 255 && Pin_Monitor(Distance_Pins_Trigger[i]) == true) {
        pinMode(Distance_Pins_Trigger[i], OUTPUT);
      }
    }
  }

  if (root.get<String>("Distance_Pins_Echo") != "") {
    MQTT_Settings_Set(Distance_Pins_Echo, Distance_Max_Number_Of, root.get<String>("Distance_Pins_Echo"), MQTT_Topic[Topic_System] + "/Distance", "Distance Pins Echo");
    // Set pinMode
    for (byte i = 0; i < Distance_Max_Number_Of; i++) {
      if (Distance_Pins_Echo[i] != 255 && Pin_Monitor(Distance_Pins_Echo[i]) == true) {
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

  if (root.get<String>("Dimmer_Pins") != "") {
    MQTT_Subscribe(MQTT_Topic[Topic_Dimmer], true, PLUS);
    MQTT_Settings_Set(Dimmer_Pins, Dimmer_Max_Number_Of, root.get<String>("Dimmer_Pins"), MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Pins");
    // Set pinMode
    for (byte i = 0; i < Dimmer_Max_Number_Of; i++) {
      if (Dimmer_Pins[i] != 255) {
        if (Pin_Monitor(Dimmer_Pins[i]) == true) {
          pinMode(Dimmer_Pins[i], OUTPUT);
          analogWrite(Dimmer_Pins[i], 0);
          Dimmer_State[i] = 0;
          Dimmer_Configured = true;
        }
      }
    }
  }

  // else if (Setting == "Button_Pins") {
  //   MQTT_Settings_Set(Button_Pins, Button_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Button", "Button Pins");
  //
  //   // Set pinMode
  //   for (byte i = 0; i < Button_Max_Number_Of; i++) {
  //     if (Button_Pins[i] != 255) {
  //       if (Pin_Monitor(Button_Pins[i]) == true) {
  //         pinMode(Button_Pins[i], INPUT_PULLUP);
  //       }
  //     }
  //   }
  // }
  // else if (Setting == "Button_Target") MQTT_Settings_Set(Button_Target, Button_Max_Number_Of, Value, MQTT_Topic[Topic_System] + "/Button", "Button Target");
  //
  // // Config_ID is last config so will reboot if needed and save config
  // else if (Setting == "Config_ID") {
  //   if (Value == "") {
  //     Value = "0";
  //   }
  //   Config_ID = Value;
  //   // Only save if triggered after config is loaded
  //   if (Config_json_Loaded == true) FS_Config_Save();
  // }

  // else {
  //   Log(MQTT_Topic[Topic_Error] + "/DeviceConfig", "Unknown configuration: " + Setting);
  //   return;
  // }

  // Log value change
  // Log(MQTT_Topic[Topic_System] + "/Dobby", "'" + Setting + "' changed from: " + Old_Value + " to: " + Value);

  return true;

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


// ############################################################ FS_Config_Set() ############################################################
bool FS_Config_Set(String Topic, String Payload) {

  if (Topic != MQTT_Topic[Topic_Config]) {
    Serial.println("RETURN MARKER");
    return false;
  }

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


// ############################################################ MQTT_Settings() ############################################################
bool MQTT_Settings(String Topic, String Payload) {

  if (Topic.indexOf(MQTT_Topic[Topic_Settings]) == -1) return false;

  if (Payload.indexOf(";") == -1) return false; // ADD ERROR for missing ";"

  // Remove ";" and anything after
  Payload = Payload.substring(0, Payload.indexOf(";"));

  Topic.replace(MQTT_Topic[Topic_Settings] + "/", "");

  Device_Config(Topic, Payload);

  return true;

} // MQTT_Settings


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

  if (Topic == "Power" && Payload.indexOf("Reboot") != -1) {
    Reboot(10000);
    return true;
  }

  else if (Topic == "Flash" && Payload.indexOf(MQTT_Allow_Flash_Password) != -1) {
    MQTT_Allow_Flash();
    return true;
  }

  else if (Topic == "FS") {
    if (FS_Commands(Payload) == true) return true;
  }

  else if (Topic == "Pins" && Payload == "Map") {
    Pin_Map();
    return true;
  }

  else if (Topic == "Blink") {
    Indicator_LED_Blink(Payload.toInt());
    return true;
  }

  else if (Topic == "Hostname") {
    Hostname = Payload;
    FS_Config_Drop();
    Log(MQTT_Topic[Topic_System] + "/DeviceConfig", "Reboot required rebooting in 2 seconds");
    Reboot(2000);
    return true;
  }

  else if (Topic == "Version") {
    if (Payload == "Show") Version_Show();
    if (Payload == "Update") Version_Update();
    return true;
  }

  else if (Topic == "IP") {
    if (Payload == "Show") IP_Show();
    return true;
  }

  else if (Topic == "Dimmer") {

    Topic.replace("Dimmer", "");

    if (Topic == "FadeJump") {
      Dimmer_Fade_Jump = Payload.toInt();
      Log(MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Fade Jump changed to: " + String(Dimmer_Fade_Jump));
      return true;
    }

    else if (Topic == "FadeJumpDelay") {
      Dimmer_Fade_Jump_Delay = Payload.toInt();
      Log(MQTT_Topic[Topic_System] + "/Dimmer", "Dimmer Fade Jump Delay changed to: " + String(Dimmer_Fade_Jump_Delay));
      return true;
    }
  } // Dimmer


  else if (Topic == "FSConfig") {
    if (Payload == "Save") FS_Config_Save();
    else if (Payload == "Show") FS_Config_Show();
    else if (Payload == "Drop") FS_Config_Drop();
    return true;
  }

  else if (Topic == "FSConfig/Set") {
    FS_Config_Set(Topic, Payload);
    return true;
  }

  else if (Topic == "Test") {

    Serial.println("MARKER TEST");
    Log("/ts", "MARKER");

    String publish_String;

    for (byte i = 0; i < Relay_Max_Number_Of; i++) {

      publish_String = publish_String + " - " + String(Relay_Pins[i]);

    }

    Log("/ts", publish_String);


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

  if (ArduinoOTA_Active == true) return;

  else if (MQTT_Settings(topic, payload)) return;

  else if (MQTT_Commands(topic, payload)) return;

  else if (MQTT_All(topic, payload)) return;

  else if (Buzzer(topic, payload)) return;

  else if (DHT(topic, payload)) return;

  else if (Relay(topic, payload)) return;

  else if (Distance(topic, payload)) return;

  else if (Dimmer(topic, payload)) return;

  else if (FS_Config_Set(topic, payload)) return;

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
    Serial.println("Start updating " + type);
  });

  ArduinoOTA.onEnd([]() {
    Log(MQTT_Topic[Topic_System] + "/ArduinoOTA", "ArduinoOTA ... End");
    ArduinoOTA_Active = false;
    Serial.println("End");
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

  if (Indicator_LED_Configured == true) Indicator_LED(LED_Config);

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
void Serial_CLI_Boot_Message() {
  for (byte i = Serial_CLI_Boot_Message_Timeout; i > 0; i--) {
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
    Serial_CLI_Boot_Message();
    return;
  }
}


// ############################################################ setup() ############################################################
void setup() {

  // ------------------------------ Serial ------------------------------
  Serial.setTimeout(100);
  Serial.begin(115200);
  Serial.println();


  // ------------------------------ Indicator_LED ------------------------------
  if (Indicator_LED_Configured == true) {
    pinMode(D4, OUTPUT);
  }
  if (Indicator_LED_Configured == true) Indicator_LED(LED_Config);

  // ------------------------------ FS ------------------------------
  SPIFFS.begin();

  FS_Config_Load();

  Base_Config_Check();

  // ------------------------------ Random Seed ------------------------------
  randomSeed(analogRead(0));


  // ------------------------------ MQTT ------------------------------
  MQTT_Client.onConnect(onMqttConnect);
  MQTT_Client.onDisconnect(onMqttDisconnect);
  MQTT_Client.onMessage(onMqttMessage);

  MQTT_Client.setServer(String_To_IP(MQTT_Broker), MQTT_Port.toInt());
  MQTT_Client.setCredentials(MQTT_Username.c_str(), MQTT_Password.c_str());
  MQTT_Client.setClientId(Hostname.c_str());



  // ------------------------------ WiFi ------------------------------
  Log(MQTT_Topic[Topic_System] + "/WiFi", "SSID set to: " + WiFi_SSID);

  WiFi.disconnect();

  WiFi.mode(WIFI_STA);
  WiFi.hostname(Hostname);

  gotIpEventHandler = WiFi.onStationModeGotIP([](const WiFiEventStationModeGotIP& event) {
    Wifi_State = 1;
    wifiReconnectTimer.detach();
    Log(MQTT_Topic[Topic_System] + "/WiFi", "Connected to SSID: '" + WiFi_SSID + "' - IP: '" + IPtoString(WiFi.localIP()) + "' - MAC Address: '" + WiFi.macAddress() + "'");
    if (Indicator_LED_Configured == true) Indicator_LED(LED_OFF);
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
      if (Indicator_LED_Configured == true) Indicator_LED(LED_WiFi);
      wifiReconnectTimer.attach_ms(WiFi_Reconnect_Delay, connectToWifi);
      Wifi_State = 2;
    }
    // MQTT
    mqttReconnectTimer.detach(); // ensure we don't reconnect to MQTT while reconnecting to WiFi
  });

  // Start wifi connection
  connectToWifi();

  if (Indicator_LED_Configured == true) Indicator_LED(LED_OFF);

} // setup()


// ############################################################ loop() ############################################################
void loop() {

  OTA_Handler();

  Relay_Auto_OFF_Loop();

  Distance_Sensor();

  Distance_Sensor_Auto_OFF();

  Button_Loop();

} // loop()
