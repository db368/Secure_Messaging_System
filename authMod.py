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


def searchUsernames(name):
    """Search the DB for a specific username returns a wildcard list of users"""
    
    conn = sqlite.connect("sql/backend.db")
    c = conn.cursor()

    # Throw on some wildcard characters to give the user some leinency
    name = "%"+name+"%"
    
    # Send out a query to search the DB for the given username string
    c.execute("SELECT user_id, user_name FROM Users WHERE user_name LIKE ?",(name,))

    # Iterate through results and add to our return list
    users = [] 
    for user in c.fetchall():
        print(user) 
        username = user[1]
        users.append(username)

    conn.close()  
    return users

def getFriends(username1):
    """ Return the friends of the given user """
    
    conn = sqlite.connect("sql/backend.db")
    c = conn.cursor()

    friends=[]
    
    # Search the friend registry in both directions
    c.execute("SELECT user2 FROM Friends where user1=?",(username1,))
    for friend in c.fetchall():
        friends.append(friend[0])
    
    c.execute("SELECT user1 FROM Friends where user2=?",(username1,))
    for friend in c.fetchall():
       friends.append(friend[0])
    
    # Now get their usernames
    friendnames = []
    for friend in friends:
        c.execute("SELECT user_name FROM Users WHERE user_id =?", (friend,))
        name = c.fetchone()[0]
        friendnames.append(name)

    # Return this list of usernames
    conn.close()
    return friendnames

def addFriendRelationship(username1, username2):
    conn = sqlite.connect("sql/backend.db")
    c = conn.cursor()

    try:
        # Get user1 id
        c.execute("SELECT user_id FROM Users WHERE user_name = ? ", (username1,))
        id1 = c.fetchone()[0]

        # Get user 2 id
        c.execute("SELECT user_id FROM Users WHERE user_name = ? ", (username2,))
        id2 = c.fetchone()[0]
        #Insert a new relationship into friends table
        c.execute("INSERT INTO Friends VALUES(?,?)", (id1, id2))
    except ValueError as e:
        print("That's not ahppending")
        return 0

    conn.commit()
    conn.close()

    return 1

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
        return results[0]
    # fail if it doesnt
    return -1