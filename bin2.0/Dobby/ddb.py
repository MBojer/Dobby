#!/usr/bin/python3

import pymysql

# System variables
Version = 300000

class Init:

    # -------------------------------------------------------------------------------------------------------
    # Custom Exception
    class Error(Exception):
        pass


    # -------------------------------------------------------------------------------------------------------
    def __init__(self, Username, Password, Server='localhost'):

        self.Server = Server
        self.Username = Username
        self.Password = Password

        # test db connection
        self.Run("SELECT VERSION()")


    # -------------------------------------------------------------------------------------------------------
    def Connect(self, db_Name="", Create_If_Missing=True):
        
        try:
            db = pymysql.connect(
                db=db_Name,
                host=self.Server,
                user=self.Username,
                passwd=self.Password,
                unix_socket='/var/run/mysqld/mysqld.sock'
            )
        except pymysql.err.InternalError as e:
            # 1049 = Missing db
            if "1049," in str(e) and Create_If_Missing == True:
                self.Create_Schema(db_Name)
                return self.Connect(db_Name)
            else:
                raise self.Error(str(e))
        else:
            # Return database connection
            return db


    # -------------------------------------------------------------------------------------------------------
    def Disconnect(self, Connection):
        # disconnect from server
        Connection.close()    
    


    # -------------------------------------------------------------------------------------------------------
    def Run(self, Command, All=False, db_Name="", Connection=None):

        db_Connection = None

        if Connection == None:
            db_Connection = self.Connect(db_Name)
        else:
            db_Connection = Connection

        # Create the cursor
        db_Cursor = db_Connection.cursor()
        # execute SQL query using execute() method.
        try:
            db_Cursor.execute(Command)
        except pymysql.err.ProgrammingError as e:
            if '1146' in str(e):
                if 'Table' in str(e):
                    raise self.Error("Missing table")
                elif 'Schema' in str(e):
                    raise self.Error("Missing schema")
            
            raise self.Error("Run error: " + str(e))


        if All == False:
            # Fetch a single row using fetchone() method.
            data = db_Cursor.fetchone()
            if data != None:
                # remove tubler
                data = data[0]
        else:
            data = db_Cursor.fetchall()

        if Connection == None:
            self.Disconnect(db_Connection)

        return data    
        
    # -------------------------------------------------------------------------------------------------------
    def Create_Schema(self, Name):
        # Create Schema
        self.Run("CREATE SCHEMA `" + Name + "`;")