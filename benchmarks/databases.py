
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import mysql.connector
from mysql.connector import errorcode
import config as cfg
from . import schema as sch


class Db:

    DBMS_NAME = None

    def __init__(self, name, verbose=True):
        super().__init__()
        self.name = name
        self.verbose = verbose
        self.sessionmaker = None
        
    def connect(self):
        return self.sessionmaker()
    
    def disconnect(self):
        pass
    

class SqliteDb(Db):
    
    DBMS_NAME = 'Sqlite'

    def __init__(self, name, verbose=True):
        super().__init__(name, verbose=verbose)
        path = os.path.join(cfg.DATA_DIR, 'bin', f'{name}.db')
        engine = create_engine(f"sqlite:///{path}" , echo=verbose)    
        sch.Base.metadata.create_all(engine)
        self.sessionmaker = sessionmaker(bind=engine, autoflush=False)
        self.engine = engine
        self.path = path
        

class MySqlDb(Db):
    
    DBMS_NAME = 'MySql'

    def __init__(self, name, verbose=True):
        super().__init__()
        self._check_database(name)
        connargs = dict(connect_timeout=6000)
        connstr = f"mysql+mysqlconnector://rcemp:rcemp@localhost:3306/{name}"
        # engine = create_engine(connstr, echo=verbose, connect_args=connargs, pool_pre_ping=True)       
        engine = create_engine(connstr, echo=verbose, connect_args=connargs)    
        sch.Base.metadata.create_all(engine)
        # self.sessioncls = scoped_session(sessionmaker(bind=engine, autoflush=False))
        self.sessioncls = sessionmaker(bind=engine, autoflush=False)
        self.engine = engine

    def _check_database(self, name):
        cnx = mysql.connector.connect(user='rcemp', password='rcemp')
        cursor = cnx.cursor()
        try:
            cursor.execute("USE {}".format(name))
        except mysql.connector.Error as err:
            print("Database {} does not exists.".format(name))
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                self._create_database(cursor, name)
                print("Database {} created successfully.".format(name))
                cnx.database = name
            else:
                print(err)
                exit(1)
        finally:
            cnx.close()

    def _create_database(self, cursor, name):
        try:
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(name))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)
