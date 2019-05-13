import sqlite3 as sqlite
import os
from enum import Enum
import hashlib
import base64
import uuid

class UserStatus(Enum):
    SUCCESSFUL = 0
    ALREADY_EXIST = 1
    FAILURE = 2
    WEAK_PASS = 3

def initDatabase():
    """ Returns false if a new database was created, true otherwise
    return false connection"""

    dbname = "backend"
    dbname = "sql/" + dbname + ".db"

    # Check to see if our sql folder exists
    if not os.path.exists("sql"):
        os.mkdir("sql")
    
    # Check to see if the DB has already been initialized
    if not os.path.isfile(dbname):
        # It's not, so we need to initalize our own tables
        conn = sqlite.connect(dbname)
        c = conn.cursor()

        createTables(c)
        conn.commit()
        conn.close()
        return False
    
    return True 

def createTables(c, purge = False):
    """ Creates all the necessary tables. If purge is true, wipe out
        all existing information before creating """
    
    query_path = "sql/queries/createtables.sql" 
    query_file = open(query_path)

    query = query_file.read()

    c.executescript(query)

    return True

def registerUser(username, password):
    """ Registers a new user to the database """   
    # Test your might!
    if not testMight(password):
        return(UserStatus.WEAK_PASS)
    
    # Open Connection to the DB
    conn = sqlite.connect("sql/backend.db")
    c = conn.cursor()

    # Check to see if this username already exists
    c.execute("SELECT * FROM Users WHERE user_name = ?", (username,))
    if not c.fetchone() is None:
        conn.close()
        return UserStatus.ALREADY_EXIST

    # If it doesn't, then add it to the DB
    addquery = "INSERT INTO Users VALUES(null, ?, ?)"
    c.execute(addquery, (username, password))
    conn.commit()
    conn.close()
    return UserStatus.SUCCESSFUL

def getFriends(username1):
    """ Return the friends of the given user """
    
    return ["bob", "Jay", "Ricky"]

def addFriendRelationship(username1, username2):
    # First get user ID 
    # conn = sqlite.connect(dbname)
    # c = conn.cursor()
    
    return []

def removeFriends():
    return []
def testMight(password):
    """Checks the strength of the specified password"""
    # Gather Info   
    n = len(password)
    numbers = sum(c.isdigit() for c in password)
    words = sum(c.isdigit() for c in password)
    spaces = sum(c.isspace() for c in password)
    other = len(password) - words - spaces

    # Check each criteria
    if n<8:
        return False
    if spaces > 0:
        return False
    if numbers<2:
        return False

    return True

def checkCreds(username, password):
    """ Check to see if there is a matching username/password pair in the database """
    # Open Connection
    conn = sqlite.connect("sql/backend.db")
    c = conn.cursor()

    checkquery = "SELECT user_id FROM Users WHERE user_name = ? AND user_pass = ?"
    c.execute(checkquery, (username, password))

    # Pull userid out of tuple if exists
    results = c.fetchone()
    if results is not None:
        return results
    # fail if it doesnt
    return -1