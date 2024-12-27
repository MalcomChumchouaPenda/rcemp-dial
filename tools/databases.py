
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import mysql.connector
from mysql.connector import errorcode
from model import schemas as sch


curdir = os.path.dirname(__file__)


class Db:

    def __init__(self, verbose=True):
        super().__init__()
        self.verbose = verbose
        self.sessionmaker = None
        self.sessions = {}
        
    def connect(self, key=None):
        session =  self.sessionmaker()
        self.sessions[key] = session
        return session
    
    def disconnect(self, key=None):
        session = self.sessions.pop(key)
        session.close()
        

class SqliteDb(Db):
    
    def __init__(self, path, verbose=True):
        super().__init__(verbose=verbose)
        connstr = f"sqlite:///{path}"    
        engine = create_engine(connstr, echo=verbose)    
        sch.Base.metadata.create_all(engine)
        self.sessionmaker = sessionmaker(bind=engine, autoflush=False)
        self.engine = engine
        

class MySqlDb(Db):
    
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
    