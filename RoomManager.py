
import json

class Client():
    """ Represents all relevant data for a user """
    def __init__(self, sock, id, username):
        self.conn = sock
        self.id = id
        self.username = username
    
    def sendMessage(self, message, sender):
        """ Send a message to this user """
        info = {"msg":message, "sender":sender}
        msg = json.dumps(info).encode("utf-8")
        try: 
            self.conn.send(msg)
        except:
            print("That user is not getting massage")

class Room():
    """ A chatroom for users to join and send messages """
    def __init__(self, name, capacity):
        self.userlist = []
        self.name = name
        self.capacity = capacity


    def sendMessage(self, conn, msg, user):
        for user in self.userlist:
            # send message
            pass
        
    def addClient(self, client):
        """ Adds a client to the current room, returns 1 if success """
        
        # Check to see if this client is already here
        if client in self.userlist:
            return 1
        
        self.userlist.append(client)
        return 1
    
    def removeClient(self, client):
        """ remove a client from the room if they leave """
        if client in self.userlist:
            self.userlist.remove(client)

    def deleteRoom(self):
        print("Python garbage collection?")

#def createRoom(name, host, capacity = 10):
    #""" Creates a new room woith the specified name """
    #global rooms
    #new_room = Room(name, capacity)
    #rooms[name] = new_room

#def getRoomList():
    #global rooms
    #return rooms

#def joinRoom(name, conn, id):
    #""" Join a room as a client """

    #global rooms

    #if name  in rooms:
        #client = Client(conn, name, id)
        #room = rooms[name]
        #room.addClient(client)
        #return room.host
    #else:
        #return "FAILURE"