/*
Version: 1
*/

#ifndef DobbyLib_h
#define DobbyLib_h

#include "Arduino.h"
#include <Ethernet.h>

class DobbyLib {

public:
  // ============================================= Setup =============================================
  DobbyLib(String New_Hostname);

  // ============================================= Functions =============================================
  // Misc
  String IPtoString(IPAddress IP_Address);
  IPAddress StringToIP(String IP_String);

  bool isValidNumber(String str);

  byte Pin_Monitor(byte Action, byte Pin_Number);

  // Log
  void Log(String Topic, String Log_Text);
  void Log(String Topic, int Log_Text);
  void Log(String Topic, float Log_Text);



  // String Generate(String ID, String Value);
  // bool Decode(String Value);
  // bool Check(String Value);

  // MQTT
  void Rebuild_MQTT_Topics();

  // byte Pin_Monitor(byte Action, byte Pin_Number);

  // ============================================= Define =============================================
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
  #define Topic_MAX31855 28

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
  #define Topic_MAX31855_Text "/MAX31855/"


  // ============================================= Variables =============================================

  String Hostname;

  String Config_ID;

  String System_Header = "/Header";
  String System_Sub_Header = "";

  // MQTT
  String MQTT_Broker = "0.0.0.0";
  String MQTT_Port = "";

  String MQTT_Username = "";
  String MQTT_Password = "";

  unsigned long MQTT_KeepAlive_At = 60000;
  unsigned long MQTT_KeepAlive_Interval = 60000;

  #define MQTT_Topic_Number_Of 29
  String MQTT_Topic[MQTT_Topic_Number_Of];
  // String MQTT_Topic[MQTT_Topic_Number_Of] = {
  //   System_Header + Topic_Settings_Text + Hostname,
  //   System_Header + Topic_Config_Text + Hostname,
  //   System_Header + Topic_Commands_Text + Hostname,
  //   System_Header + Topic_All_Text,
  //   System_Header + Topic_KeepAlive_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Buzzer_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_DHT_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Relay_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Distance_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Dimmer_Text + Hostname,
  //   System_Header + Topic_Log_Error_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Button_Text + Hostname,
  //   System_Header + Topic_Dobby_Text,
  //   System_Header + Topic_System_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_LoadCell_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_Switch_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_MPU6050_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_BMP180_Text + Hostname,
  //   System_Header + Topic_Log_Warning_Text + Hostname,
  //   System_Header + System_Sub_Header + Topic_MQ2_Text + Hostname,
  //   System_Header + Topic_Log_Fatal_Text + Hostname,
  //   System_Header + Topic_Log_Info_Text + Hostname,
  //   System_Header + Topic_Log_Debug_Text + Hostname,
  //   System_Header + Topic_RFID_Text + Hostname,
  //   System_Header + Topic_PIR_Text + Hostname,
  //   System_Header + Topic_LDR_Text + Hostname,
  //   System_Header + Topic_MAX31855_Text + Hostname,
  // };

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
    false,
    false,
    false,
    false,
  };
  byte MQTT_Topic_Subscribe_Subtopic[MQTT_Topic_Number_Of] = {
    HASH,
    HASH,
    HASH,
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
    NONE,
    NONE,
    NONE,
    PLUS,
    NONE,
    HASH,
  };

  bool MQTT_Subscribtion_Active[MQTT_Topic_Number_Of];

};
#endif
