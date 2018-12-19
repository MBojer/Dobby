/*
Serial CRC
*/


#include "Arduino.h"
#include "DobbyLib.h"


// // ============================================= Setup =============================================
DobbyLib::DobbyLib(String New_Hostname) {
  Hostname = New_Hostname;

  Rebuild_MQTT_Topics();
}


// ============================================= Functions =============================================

// --------------------------------------------- IPtoString ---------------------------------------------
String DobbyLib::IPtoString(IPAddress IP_Address) {

  String Temp_String = String(IP_Address[0]) + "." + String(IP_Address[1]) + "." + String(IP_Address[2]) + "." + String(IP_Address[3]);

  return Temp_String;

} // IPtoString


// --------------------------------------------- StringToIP ---------------------------------------------
IPAddress DobbyLib::StringToIP(String IP_String) {

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


// ############################################################ Rebuild_MQTT_Topics() ############################################################
void DobbyLib::Rebuild_MQTT_Topics() {
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
  MQTT_Topic[Topic_Button] = System_Header + System_Sub_Header + Topic_Button_Text + Hostname;
  MQTT_Topic[Topic_Dobby] = System_Header + Topic_Dobby_Text;
  MQTT_Topic[Topic_System] = System_Header + Topic_System_Text + Hostname;
  MQTT_Topic[Topic_LoadCell] = System_Header + System_Sub_Header + Topic_LoadCell_Text + Hostname;
  MQTT_Topic[Topic_DC_Voltmeter] = System_Header + System_Sub_Header + Topic_DC_Voltmeter_Text + Hostname;
  MQTT_Topic[Topic_Ammeter] = System_Header + System_Sub_Header + Topic_Ammeter_Text + Hostname;
  MQTT_Topic[Topic_Switch] = System_Header + System_Sub_Header + Topic_Switch_Text + Hostname;
  MQTT_Topic[Topic_MPU6050] = System_Header + System_Sub_Header + Topic_MPU6050_Text + Hostname;
  MQTT_Topic[Topic_BMP180] = System_Header + System_Sub_Header + Topic_BMP180_Text + Hostname;
  MQTT_Topic[Topic_Log_Debug] = System_Header + Topic_Log_Debug_Text + Hostname;
  MQTT_Topic[Topic_Log_Info] = System_Header + Topic_Log_Info_Text + Hostname;
  MQTT_Topic[Topic_Log_Warning] = System_Header + Topic_Log_Warning_Text + Hostname;
  MQTT_Topic[Topic_Log_Error] = System_Header + Topic_Log_Error_Text + Hostname;
  MQTT_Topic[Topic_Log_Fatal] = System_Header + Topic_Log_Fatal_Text + Hostname;
  MQTT_Topic[Topic_MQ2] = System_Header + System_Sub_Header + Topic_MQ2_Text + Hostname;
  MQTT_Topic[Topic_RFID] = System_Header + System_Sub_Header + Topic_RFID_Text + Hostname;
  MQTT_Topic[Topic_PIR] = System_Header + System_Sub_Header + Topic_PIR_Text + Hostname;
  MQTT_Topic[Topic_LDR] = System_Header + System_Sub_Header + Topic_LDR_Text + Hostname;
  MQTT_Topic[Topic_MAX31855] = System_Header + System_Sub_Header + Topic_MAX31855_Text + Hostname;
} // Rebuild_MQTT_Topics()


// ############################################################ isValidNumber() ############################################################
bool DobbyLib::isValidNumber(String str) {
  for(byte i=0;i<str.length();i++)
  {
    if(isDigit(str.charAt(i))) return true;
  }
  return false;
} // isValidNumber()
