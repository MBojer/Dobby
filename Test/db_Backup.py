#!/usr/bin/python


# DO NOT MOVE
# DO NOT MOVE
# DO NOT MOVE

# MySQL
import MySQLdb

# Threding
import threading

import datetime
# from datetime import tie

import time


# ---------------------------------------- Logging ----------------------------------------
def Log(Log_Level, Log_Source, Log_Header, Log_Text):
    print "Log_Level: " + str(Log_Level) + " Log_Source: " + str(Log_Source) + " Log_Header: " + str(Log_Header) + " Log_Text: " + str(Log_Text)


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


# ---------------------------------------- db_Backup ----------------------------------------
class db_Backup:

    # How often does esch db_Backup read write to the db (sec)
    # Next_Backup_At =
    # Loop_Delay = 0.500

    # sudo mysqldump Dobby > Dobby_db.sql

    def __init__(self):
        # Log event
        Log("Info", "db Backup", "Checker", "Starting")

        self.Next_Check = datetime.date.today() - datetime.timedelta(1)

        db_Backup_Thread = threading.Thread(target=self.Checker, kwargs={})
        db_Backup_Thread.daemon = True
        db_Backup_Thread.start()

    def Checker(self):
        # Start eternal loop
        while True:

            while datetime.date.today() != self.Next_Check:
                time.sleep(60)

            print "self.Next_Check"
            print self.Next_Check
            print type(self.Next_Check)



            quit()


            # time.sleep(db_Backup.db_Refresh_Rate)

        # Sart checker thread
        # db_Backup_Thread = threading.Thread(target=self.Checker, kwargs={})
        # db_Backup_Thread.daemon = True
        # db_Backup_Thread.start()


print "Hello"

db_Backup()

while True:
    time.sleep(360)

print "End"
