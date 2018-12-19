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

CREATE TABLE `Dobby`.`DashButtons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(45) NOT NULL,
  `Type` varchar(45) NOT NULL,
  `Target_Topic` varchar(45) NOT NULL,
  `Target_Payload` varchar(45) NOT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`APC_Monitor` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(45) NOT NULL,
  `Enabled` tinyint(1) NOT NULL DEFAULT '0',
  `Tags` varchar(100) DEFAULT NULL,
  `Refresh_Rate` int(4) NOT NULL DEFAULT '5',
  `Max_Entries` int(10) NOT NULL DEFAULT '125000',
  `FTP_URL` varchar(100) NOT NULL,
  `Next_Collect` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Last_Collect` datetime DEFAULT NULL,
  `Last_Modified` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`DeviceConfig` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Hostname` varchar(25) NOT NULL,
  `Config_Active` tinyint(1) unsigned NOT NULL,
  `Config_ID` int(11) unsigned NOT NULL DEFAULT '1',
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
  `Switch_Pins` varchar(25) DEFAULT NULL,
  `Switch_Target_ON` varchar(250) DEFAULT NULL,
  `Switch_Target_OFF` varchar(250) DEFAULT NULL,
  `LoadCell_Pins_DT` varchar(25) DEFAULT NULL,
  `LoadCell_Pins_SCK` varchar(25) DEFAULT NULL,
  `LoadCell_Calibration` varchar(25) DEFAULT NULL,
  `Ammeter_Pin_A0` varchar(25) DEFAULT NULL,
  `Ammeter_Offset` varchar(45) DEFAULT NULL,
  `DC_Voltmeter_Pins` varchar(250) DEFAULT NULL,
  `DC_Voltmeter_R1` varchar(25) DEFAULT NULL,
  `DC_Voltmeter_R2` varchar(25) DEFAULT NULL,
  `DC_Voltmeter_Curcit_Voltage` varchar(25) DEFAULT NULL,
  `DC_Voltmeter_Offset` varchar(25) DEFAULT NULL,
  `MPU6050_Pin_SCL` varchar(25) DEFAULT NULL,
  `MPU6050_Pin_SDA` varchar(25) DEFAULT NULL,
  `MPU6050_Pin_Interrupt` varchar(25) DEFAULT NULL,
  `MPU6050_Gyro_X_Offset` decimal(5,2) DEFAULT NULL,
  `MPU6050_Gyro_Y_Offset` decimal(5,2) DEFAULT NULL,
  `MPU6050_Gyro_Z_Offset` decimal(5,2) DEFAULT NULL,
  `MPU6050_Gyro_Invert_Axis` tinyint(1) DEFAULT NULL,
  `BMP180_Pin_SCL` varchar(45) DEFAULT NULL,
  `BMP180_Pin_SDA` varchar(45) DEFAULT NULL,
  `BMP180_Altitude` decimal(6,1) DEFAULT NULL,
  `MQ2_Pin_A0` varchar(45) DEFAULT NULL,
  `MFRC522_Pins` varchar(75) DEFAULT NULL,
  `PIR_Pins` varchar(45) DEFAULT NULL,
  `PIR_Topic` varchar(45) DEFAULT NULL,
  `PIR_OFF_Payload` varchar(45) DEFAULT NULL,
  `PIR_ON_Payload_1` varchar(45) DEFAULT NULL,
  `PIR_ON_Payload_2` varchar(45) DEFAULT NULL,
  `PIR_ON_Payload_3` varchar(45) DEFAULT NULL,
  `PIR_OFF_Delay` varchar(45) DEFAULT NULL,
  `LDR_Pin_A0` varchar(45) DEFAULT NULL,
  `LDR_Target_Topic` varchar(45) DEFAULT NULL,
  `LDR_Dark_At` varchar(45) DEFAULT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`Mail_Trigger` (
  `id` int(11) NOT NULL,
  `Name` varchar(45) NOT NULL,
  `Type` varchar(45) NOT NULL,
  `Enabled` tinyint(1) NOT NULL,
  `Alert_State` tinyint(1) NOT NULL DEFAULT '0',
  `MQTT_Target` varchar(45) NOT NULL,
  `MQTT_Payload_Clear` decimal(6,2) NOT NULL,
  `MQTT_Payload_Trigger` decimal(6,2) NOT NULL,
  `Alert_Target` varchar(45) NOT NULL,
  `Alert_Subject` varchar(45) NOT NULL,
  `Alert_Payload_Clear` varchar(45) NOT NULL,
  `Alert_Payload_Trigger` varchar(45) NOT NULL,
  `Triggered_DateTime` timestamp NULL DEFAULT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`Log_Trigger` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(45) NOT NULL,
  `Tags` varchar(100) DEFAULT NULL,
  `Max_Entries` int(10) NOT NULL DEFAULT '125000',
  `Enabled` tinyint(1) NOT NULL DEFAULT '0',
  `State` varchar(45) DEFAULT NULL,
  `Topic` varchar(45) NOT NULL,
  `Last_Trigger` datetime DEFAULT NULL,
  `Last_Modified` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `Topic_UNIQUE` (`Topic`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`MQTTFunctions` (
  `id` int(16) NOT NULL AUTO_INCREMENT,
  `CommandNumber` int(2) NOT NULL,
  `Function` varchar(25) NOT NULL,
  `Type` varchar(25) NOT NULL,
  `Command` varchar(200) NOT NULL,
  `DelayAfter` decimal(10,4) NOT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`Spammer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Name` varchar(45) NOT NULL,
  `Enabled` tinyint(1) NOT NULL DEFAULT '0',
  `Interval` decimal(10,4) NOT NULL DEFAULT '300.0000',
  `Topic` varchar(45) NOT NULL,
  `Payload` varchar(45) NOT NULL,
  `Next_Ping` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Last_Ping` datetime DEFAULT NULL,
  `Last_Modified` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`Users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `Username` varchar(45) NOT NULL,
  `Password` varchar(45) NOT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `Dobby`.`SystemConfig` (
  `id` int(16) NOT NULL AUTO_INCREMENT,
  `Target` varchar(25) NOT NULL,
  `Header` varchar(25) NOT NULL,
  `Name` varchar(25) NOT NULL,
  `Value` varchar(200) NOT NULL,
  `Last_Modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "System", "Header", "/Test");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Broker", "localhost");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Password", "NoSinking");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "PublishDelay", "0.5");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Username", "DasBoot");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTT", "Port", "1883");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTT", "Log", "Level", "Info");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "MQTTKeepAlive", "Interval", "60");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "SMTP", "Server", "smtp.gmail.com");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "SMTP", "Port", "587");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "SMTP", "Sender", "dobbysystemalerts@gmail.com");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "SMTP", "Username", "dobbysystemalerts");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "SMTP", "Password", "NoMailsSend");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "db", "DobbyLog");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "Length", "250000");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Dobby", "Log", "Level", "Info");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("KeepAliveMonitor", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("KeepAliveMonitor", "Log", "Length", "2500");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTTConfig", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("MQTTFunctions", "Log", "Level", "Info");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "Log", "Level", "Info");
INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Mail_Trigger", "Log", "Length", "5000");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Log_Trigger", "Log", "Level", "Info");

INSERT INTO `Dobby`.`SystemConfig` (Target, Header, Name, Value) Values("Spammer", "Log", "Level", "Info");
