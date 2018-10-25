#!/usr/bin/python

# FTP
from ftplib import FTP
from StringIO import StringIO
import datetime


# ---------------------------------------- Database ----------------------------------------
def Open_db(db=""):
    try:
        db = MySQLdb.connect(host="localhost",    # your host, usually localhost
                             user="dobby",         # your username
                             passwd="HereToServe",  # your password
                             db=db)        # name of the data base
        return db

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None


def Close_db(conn, cur):
    try:
        conn.commit()
        cur.close()
        conn.close()
        return True

    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        return None


# DO NOT MOVE
# DO NOT MOVE
# DO NOT MOVE

# Threding
import threading

import time

# MySQL
import MySQLdb

Log_db = 'DobbyLog'


# ---------------------------------------- Logging ----------------------------------------
def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    print "Log_Level: " + str(Log_Level) + " Log_Source: " + str(Log_Source) + " Log_Header: " + str(Log_Header) + " Log_Text: " + str(Log_Text)

# DO NOT MOVE
# DO NOT MOVE
# DO NOT MOVE


ftp = FTP('10.0.1.11')
ftp.login('apc', 'apc')
FTP_Memory_File = StringIO()
ftp.retrbinary('RETR /data.txt', FTP_Memory_File.write)

# Convert to string
FTP_Memory_File = FTP_Memory_File.getvalue()

# Remove \r
FTP_Memory_File = FTP_Memory_File.replace("\t\r", "")

FTP_Memory_File = FTP_Memory_File.split("\n")


def Function():
    i = 0

    db_Connection = Open_db(Log_db)
    db_Curser = db_Connection.cursor()

    Device_Name = ''
    Last_Entry = ''

    for Line in FTP_Memory_File:

        # Line 4 contains device information
        if i == 4:
            Device_Name = Line.split('\t')
            Device_Name = Device_Name[2]

            Last_Entry = ''

            try:
                # Find last entry for device
                db_Curser.execute("SELECT DateTime FROM DobbyLog.APC_Monitor WHERE `Name`='" + Device_Name + "' ORDER BY DateTime DESC LIMIT 1;")
                Last_Entry = db_Curser.fetchone()

            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # 1146 = Table missing
                if e[0] == 1146:
                    Log("Info", "APC Monitor", "db", "Log Trigger Table missing creating it")
                    try:
                        db_Curser.execute("CREATE TABLE `APC_Monitor` ( `id` int(11) NOT NULL AUTO_INCREMENT, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, `Name` varchar(45) NOT NULL, `Hertz A` decimal(2,0) NOT NULL, `Hertz B` decimal(2,0) NOT NULL, `Vin A` decimal(3,0) NOT NULL, `Vin B` decimal(3,0) NOT NULL, `I Out` decimal(3,1) NOT NULL, `IO Max` decimal(3,1) NOT NULL, `IO Min` decimal(3,1) NOT NULL, `Active Output` tinyint(1) NOT NULL, PRIMARY KEY (`id`), UNIQUE KEY `id_UNIQUE` (`id`)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;")
                        # Try getting last entry for device again
                        db_Curser.execute("SELECT DateTime FROM DobbyLog.APC_Monitor WHERE `Name`='" + Device_Name + "' ORDER BY DateTime DESC LIMIT 1;")
                        Last_Entry = db_Curser.fetchone()

                    except (MySQLdb.Error, MySQLdb.Warning) as e:
                        # Error 1050 = Table already exists
                        if e[0] != 1050:
                            Log("Fatal", "APC Monitor", Device_Name, "Unable to create log db table, failed with error: " + str(e))
                            return

            if Last_Entry is not None:
                Last_Entry = Last_Entry[0]
            else:
                Last_Entry = datetime.datetime.strptime("1984-09-24 03:00:00", '%Y-%m-%d %H:%M:%S')

        # Lines after 7 is data entries
        elif i > 7:
            Entries = Line.split('\t')

            if Entries != ['']:
                Time_String = Entries[0] + str(" ") + Entries[1]

                Entry_Time = datetime.datetime.strptime(Time_String, '%Y-%m-%d %H:%M:%S')

                if Entry_Time > Last_Entry:

                    Value_String = "'" + str(Entry_Time) + "', '" + str(Device_Name) + "' ,"

                    for x in range(2, 10):
                        Value_String = Value_String + "'" + str(Entries[x]) + "'"
                        if x != 9:
                            Value_String = Value_String + ", "

                    db_Curser.execute("INSERT INTO `DobbyLog`.`APC_Monitor` (`DateTime`, `Name`, `Hertz A`, `Hertz B`, `Vin A`, `Vin B`, `I Out`, `IO Max`, `IO Min`, `Active Output`) VALUES (" + Value_String + ");")

        i = i + 1

    Close_db(db_Connection, db_Curser)

# ---------------------------------------- APC_Monitor ----------------------------------------
class APC_Monitor:

    db_Refresh_Rate = 1.5

    def __init__(self):
        # Log event
        Log("Info", "APC Monitor", "Checker", "Starting")

        self.APC_Monitor_Dict = {}

        # Sart checker thread
        APC_Monitor_Thread = threading.Thread(target=self.Checker, kwargs={})
        APC_Monitor_Thread.daemon = True
        APC_Monitor_Thread.start()

    def Checker(self):
        while True:
            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT id, Last_Modified FROM Dobby.APC_Monitor WHERE Enabled='1'")
            APC_Monitor_db = db_Curser.fetchall()

            Close_db(db_Connection, db_Curser)

            for i in APC_Monitor_db:
                # i[0] = APC_Monitor db id
                if i[0] not in self.APC_Monitor_Dict:
                    self.APC_Monitor_Dict[i[0]] = self.Agent(i[0])
                    Log("Debug", "APC Monitor", "Checker", "Starting: " + self.APC_Monitor_Dict[i[0]].Name)
                else:
                    # Change to APC_Monitor
                    if str(self.APC_Monitor_Dict[i[0]].Last_Modified) != str(i[1]):
                        Log("Debug", "APC Monitor", "Checker", "Change found in: " + self.APC_Monitor_Dict[i[0]].Name + " restarting agent")
                        # Wait for agent to close db connection
                        while self.APC_Monitor_Dict[i[0]].OK_To_Kill is False:
                            time.sleep(0.100)
                        # Delete agent
                        Log("Debug", "APC Monitor", "Checker", "Deleting: " + self.APC_Monitor_Dict[i[0]].Name)
                        del self.APC_Monitor_Dict[i[0]]

                        # FIX MAKRE SURE THE AGENT IS STOPPED FIRST

                        # Start agent again
                        self.APC_Monitor_Dict[i[0]] = self.Agent(i[0])
                        Log("Debug", "APC Monitor", "Checker", "Starting: " + self.APC_Monitor_Dict[i[0]].Name)

            time.sleep(APC_Monitor.db_Refresh_Rate)

    class Agent:
        def __init__(self, id):

            self.id = int(id)

            db_Connection = Open_db("Dobby")
            db_Curser = db_Connection.cursor()

            db_Curser.execute("SELECT Name, IP, Last_Modified FROM Dobby.APC_Monitor WHERE id='" + str(self.id) + "'")
            APC_Monitor_Info = db_Curser.fetchone()

            Close_db(db_Connection, db_Curser)

            self.Name = str(APC_Monitor_Info[0])

            # Canget log event before now if you want to use name
            Log("Debug", "APC Monitor", self.Name, 'Initializing')

            self.IP = APC_Monitor_Info[1]
            self.Last_Modified = APC_Monitor_Info[2]

            self.OK_To_Kill = False

            Log("Debug", "APC Monitor", self.Name, 'Initialization compleate')





        # ========================= Agent - Log Value =========================
        def Log_Value(self, Value, json_Tag=''):

            Log("Debug", "APC Monitor", "Logging", "Value: " + str(Value) + " json_Tag: " + str(json_Tag))

            db_Connection = Open_db()
            db_Curser = db_Connection.cursor()

            # Make sure Log_Value is string
            Value = str(Value)
            # Remove the ";" at the end if there
            if Value[-1:] == ";":
                Value = Value[:-1]

            # Change Last_Trigger
            db_Curser.execute("UPDATE `Dobby`.`APC_Monitor` SET `Last_Trigger`='" + str(datetime.datetime.now()) + "' WHERE `id`='" + str(self.id) + "';")

            # Log Value
            try:
                db_Curser.execute("INSERT INTO `" + Log_db + "`.`APC_Monitor` (Name, json_Tag, Tags, Value) Values('" + self.Name + "','" + str(json_Tag) + "' , '" + str(self.Tags) + "', '" + Value + "');")
            except (MySQLdb.Error, MySQLdb.Warning) as e:
                # Table missing, create it
                if e[0] == 1146:
                    Log("Info", "APC Monitor", "db", "Log Trigger Table missing creating it")
                    try:
                        db_Curser.execute("CREATE TABLE `" + Log_db + "`.`APC_Monitor` (`id` int(11) NOT NULL AUTO_INCREMENT, `Name` varchar(75) NOT NULL, `json_Tag` varchar(75) NOT NULL, `Tags` varchar(75) DEFAULT NULL, `Value` varchar(75) NOT NULL, `DateTime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (`id`))ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;")
                        # Try logging the message again
                        db_Curser.execute("INSERT INTO `" + Log_db + "`.`APC_Monitor` (Name, json_Tag, Tags, Value) Values('" + self.Name + "','" + str(json_Tag) + "' , '" + str(self.Tags) + "', '" + Value + "');")

                    except (MySQLdb.Error, MySQLdb.Warning) as e:
                        # Error 1050 = Table already exists
                        if e[0] != 1050:
                            Log("Fatal", "APC Monitor", self.Name, "Unable to create log db table, failed with error: " + str(e))
                            self.Disable()
                            return
                else:
                    Log("Critical", "APC Monitor", "db", "Unable to log message. Error: " + str(e))
                    return

            # Delete rows > max
            db_Curser.execute("SELECT count(*) FROM `" + Log_db + "`.`APC_Monitor` WHERE Name='" + self.Name + "' AND json_Tag='" + str(json_Tag) + "';")
            Rows_Number_Of = db_Curser.fetchall()

            if Rows_Number_Of[0][0] > int(self.Max_Entries):
                Rows_To_Delete = Rows_Number_Of[0][0] - int(self.Max_Entries)
                print ("DELETE FROM `" + Log_db + "`.`APC_Monitor` WHERE Name='" + self.Name + "' AND json_Tag='" + str(json_Tag) + "' ORDER BY 'DateTime' LIMIT " + str(Rows_To_Delete) + ";")
                db_Curser.execute("DELETE FROM `" + Log_db + "`.`APC_Monitor` WHERE Name='" + self.Name + "' AND json_Tag='" + str(json_Tag) + "' ORDER BY 'DateTime' LIMIT " + str(Rows_To_Delete) + ";")
                Log("Debug", "Dobby", self.Name, "History Length reached, deleting " + str(Rows_To_Delete))

            Log("Debug", "APC Monitor", self.Name, "Valure capured: " + Value)

            Close_db(db_Connection, db_Curser)




Function()
