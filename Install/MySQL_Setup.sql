CREATE DATABASE Dobby;
CREATE DATABASE DobbyLog;

CREATE USER 'dobby'@'localhost' IDENTIFIED BY 'HereToServe';
GRANT ALL PRIVILEGES ON Dobby.* TO 'dobby'@'localhost'
    WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON DobbyLog.* TO 'dobby'@'localhost'
    WITH GRANT OPTION;

CREATE USER 'dobby'@'%' IDENTIFIED BY 'HereToServe';
GRANT ALL PRIVILEGES ON Dobby.* TO 'dobby'@'%'
    WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON DobbyLog.* TO 'dobby'@'%'
    WITH GRANT OPTION;

CREATE TABLE `Dobby`.`DeviceConfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Hostname` varchar(25) NOT NULL,
  `Config_Active` tinyint(1) unsigned NOT NULL,
  `Config_ID` int(11) unsigned NOT NULL DEFAULT '0',
  `Auto_Update` tinyint(1) unsigned NOT NULL,
  `System_Header` varchar(25) NOT NULL,
  `System_Sub_Header` varchar(25) NOT NULL,
  `WiFi_SSID` varchar(25) NOT NULL,
  `WiFi_Password` varchar(25) NOT NULL,
  `MQTT_Broker` varchar(25) NOT NULL,
  `MQTT_Port` int(5) unsigned NOT NULL DEFAULT '1883',
  `MQTT_Username` varchar(25) NOT NULL,
  `MQTT_Password` varchar(25) NOT NULL,
  `MQTT_Allow_Flash_Password` varchar(25) NOT NULL,
  `MQTT_KeepAlive_Interval` int(60) NOT NULL DEFAULT '60',
  `Relay_On_State` tinyint(1) unsigned DEFAULT NULL,
  `Relay_Pins` varchar(25) DEFAULT NULL,
  `Relay_Pin_Auto_Off` varchar(50) DEFAULT NULL,
  `Relay_Pin_Auto_Off_Delay` varchar(50) DEFAULT NULL,
  `Buzzer_Pins` varchar(2) DEFAULT NULL,
  `DHT_Pins` varchar(25) DEFAULT NULL,
  `Distance_Pins_Trigger` varchar(25) DEFAULT NULL,
  `Distance_Pins_Echo` varchar(25) DEFAULT NULL,
  `Distance_Trigger_At` varchar(50) DEFAULT NULL,
  `Distance_Target_ON` varchar(250) DEFAULT NULL,
  `Distance_Target_OFF` varchar(250) DEFAULT NULL,
  `Distance_Refresh_Rate` varchar(25) DEFAULT NULL,
  `Distance_Auto_OFF_Delay` varchar(150) DEFAULT NULL,
  `Distance_Auto_OFF_Active` varchar(25) DEFAULT NULL,
  `Dimmer_Pins` varchar(25) DEFAULT NULL,
  `Button_Pins` varchar(25) DEFAULT NULL,
  `Button_Target` varchar(250) DEFAULT NULL,
  `Scale_Pins_DT` varchar(25) DEFAULT NULL,
  `Scale_Pins_SCK` varchar(25) DEFAULT NULL,
  `Scale_Calibration` double(5,2) DEFAULT NULL,
  `Ammeter_Pins` varchar(25) DEFAULT NULL,
  `Voltmeter_DC_Pins` varchar(25) DEFAULT NULL,
  `Voltmeter_AC_Pins` varchar(25) DEFAULT NULL,
  `Date_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;


CREATE TABLE `Dobby`.`MonitorAgentConfig` (
  `Agent_ID` tinyint(3) unsigned NOT NULL AUTO_INCREMENT,
  `Agent_Name` varchar(25) NOT NULL,
  `Agent_Enabled` tinyint(1) NOT NULL DEFAULT '1',
  `Agent_State` varchar(8) NOT NULL DEFAULT 'Stopped',
  `Agent_Interval` varchar(20) NOT NULL,
  `Agent_Targets` varchar(200) NOT NULL,
  `Agent_Targets_Payload` varchar(200) NOT NULL,
  `Agent_Sources` varchar(200) NOT NULL,
  `Agent_Log_Length` smallint(5) unsigned NOT NULL DEFAULT '15000',
  `Agent_Last_Ping` timestamp NOT NULL DEFAULT '1984-09-24 00:00:00',
  `Agent_Next_Ping` timestamp NOT NULL DEFAULT '1984-09-24 00:00:01',
  `Date_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Agent_ID`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;


CREATE TABLE `Dobby`.`MQTTFunctions` (
  `id` int(16) NOT NULL AUTO_INCREMENT,
  `CommandNumber` int(2) NOT NULL,
  `Function` varchar(25) NOT NULL,
  `Type` varchar(25) NOT NULL,
  `Command` varchar(200) NOT NULL,
  `DelayAfter` decimal(10,4) NOT NULL,
  `DateModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;


CREATE TABLE `Dobby`.`SystemConfig` (
  `id` int(16) NOT NULL AUTO_INCREMENT,
  `Target` varchar(25) NOT NULL,
  `Header` varchar(25) NOT NULL,
  `Name` varchar(25) NOT NULL,
  `Value` varchar(200) NOT NULL,
  `DateModified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='Contains settings';

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "db", "DobbyLog");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "Length", "250000");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Broker", "localhost");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Password", "NoSinking");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "PublishDelay", "0.5");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Username", "DasBoot");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Port", "1883");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "System", "Header", "/Test");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Dir", "Root", "/etc/Dobby");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Dir", "Script", "/home/dobby/Dobby");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Dir", "URL", "https://github.com/MBojer/Dobby/blob/master/.pioenvs/d1_mini/firmware.bin?raw=true");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("KeepAliveMonitor", "Log", "Length", "250");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MonitorAgent", "Log", "Length", "25000");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTTKeepAlive", "Interval", "60");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MonitorAgent", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("KeepAliveMonitor", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTTConfig", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTTFunctions", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTT", "Log", "Level", "Info");
