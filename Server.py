import socket
import ssl
import threading
import json
import authMod as AuthMod
import RoomManager

# - -- GLOBALS -- -
ip = '127.0.0.1'
port = 12000
clients = []
threads = []
rooms = {}

def initServer(ip, port):
    """Starts an insecure server"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((ip, port))
    sock.listen(1)

    print("Starting server")

    # Listen loop
    while(True):
        try:
            info = {}
            connection, address = sock.accept()
            data = connection.recv(1024).decode("utf-8")
            print(data)
            response = "Pong"
            connection.send(response.encode("utf-8"))
        except ConnectionAbortedError:
            continue


def handle(conn, address):
    """ Handles clients before they've successfully logged in"""
    print("Thread started, waiting on client")
    print("[Client]:",conn.recv().decode())
    conn.write(b'HTTP/1.1 200 OK\n\n%s' % conn.getpeername()[0].encode())
    
    # Store this for when the client eventually is logged in
    client = None
    
    # Now we need to handle arbitrary input from the client
    while True:
        try:
            # Get the input from the client, and decode it from json
            incoming = conn.recv().decode("utf-8")
            print(incoming)
            # This will be 0 if the client leaves
            if incoming == 0 or incoming == '' or not incoming:
                raise ConnectionResetError
            inc_dict = json.loads(incoming)

            # Figure out what to do with it based on its purpose tag
            purpose = inc_dict["purpose"]

            if purpose == "login":
                username = inc_dict["username"]
                password = inc_dict["password"]
                
                res = AuthMod.checkCreds(username, password)

                # Check to see if this succeeded in the DB
                # TODO: Research how the server is actually supposed to 
                #       auth and keep track of authed clients
                if res == -1:
                    conn.send("FAILURE".encode())
                else:
                    # If we get a userid, confirm the existance of this client,
                    # then store all relevant info
                    client = RoomManager.Client(conn, res, username)
                    conn.send("SUCCESS".encode())
                    break
                continue

            elif purpose == "newuser":
                # Attempt to register this user in the DB
                username = inc_dict["username"]
                password = inc_dict["password"]
                print("Trying to register new user")
                res = AuthMod.registerUser(username, password)
                
                # If the username already exists, shoot it back to the client
                if res == AuthMod.UserStatus.ALREADY_EXIST:
                    conn.send("ALREADY_EXIST".encode("utf-8"))
                    continue
                # Handle some other kind of failure
                elif res == AuthMod.UserStatus.FAILURE:
                    conn.send("SQL_FAIL".encode("utf-8"))
                    continue
                else:
                    conn.send("SUCCESS".encode("utf-8"))
                    print("Client successfully added")
            continue
        except TimeoutError:
            continue
        except ConnectionResetError:
            print("client left")
            return

   # Quick check to make sure nothing happens if the client is not registered 
    if client is None:
        print("Client does not exist, Something went wrong")
        conn.close()
    
    # If we've made it this far, the client should be a registered user
    trustedLoop(client)


            
def trustedLoop(client):
    """ Where the bulk of user operations take place with a confirmed client """

    # First add this client to our global list of clients
    global clients
    conn = client.conn
    clients.append(client)
    while True:
        try:
            # Get the input from the client, and decode it from json
            incoming = conn.recv().decode("utf-8")
            print(incoming)
            
            # This will be 0 if the client leaves
            if incoming == 0 or incoming == '' or not incoming:
                raise ConnectionResetError
            inc_dict = json.loads(incoming)
            
            # Handle this elsewhere
            performAction(client, inc_dict)
            
            # Loop again
            continue
        
        # Throw these for safety
        except TimeoutError:
            clients.remove(client)
            continue
        except ConnectionResetError:
            print("Registered cient left, removing from list")
            client.conn.close()
            clients.remove(client)
            return

def performAction(this_client, inc_dict):
    """ Performs an action based on incoming messages' purpose tags """

    global clients
    purpose = inc_dict["purpose"]

    # Test method for sending messages
    if purpose == "sendmsg":
        message = inc_dict["msg"]

        for client in clients:
            if client != this_client:
                client.sendMessage("msg", this_client.username)

    if purpose == "create_room":
        name = inc_dict["name"]
        success = createRoom(name)

        this_client.conn.send(str(success).encode("utf-8"))
    
    if purpose == "get_rooms":
        rl = showRooms()
        this_client.conn.send(rl)
    return

def createRoom(name, capacity = 10):
    """Creates a room with the given name"""
    global rooms
    
    # Check to see if a room with this name already exists
    if not name in rooms:
        rooms[name] = []
        return 1
    
    return 0 

def joinRoom(name, client):
    """ Adds a client to the specified room returns 1 if successful, 0 otherwise"""
    global rooms
    if name in rooms:
        rooms[name].append(client)
        return 1
    return 0

def leaveRoom(name, client):
    """ Remove a client from a room"""
    global rooms
   
    # Check to see if room exists
    if name in rooms:
        # Check to see if client is in room
        if client in rooms[name]:
            rooms[name].remove(client)
            return 1
    return 0

def showRooms():
    """ Returns a json with all valid rooms and occupants"""
    global rooms
    
    roomoccupants = {}
    for name,occupants in rooms.items():
        roomoccupants[name] = len(occupants)

    op = json.dumps(roomoccupants).encode("utf-8") 
    return op

def initSecureServer(ip, port, cafile):
    global clients
    global threads

    # Rev up DB
    
    AuthMod.initDatabase()
    """Starts a secure server using SSL """
    print("Starting server")

    #Initiate a secure connection
    init_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    init_sock.bind((ip, port))

    # Put the socket into server mode
    init_sock.listen(1)
    
    print("Socket bound, waiting for requests")

    # Listen loop
    while(True):
        try:
            # Accept Incoming Connections
            info = {}
            secure_sock = None
            connection, address = init_sock.accept()
    
            print("Connection recieved, attempting to wrap in a secure socket")
            
            # Define context and wrap socket
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile = cafile)
            context.load_cert_chain(certfile="server.crt", keyfile = "server.key")
            secure_sock = context.wrap_socket(connection, server_side = True)
            
            # Send response, add this client to our address list and give him a thread
            print("Socket wrapped, adding user to list") 
            # clients[address] = secure_sock
            new_thread =  threading.Thread(target=handle, args=(secure_sock, address))
            new_thread.start()
            threads.append(new_thread)
            print("Client achieved.")

        except ssl.SSLError as e:
            print("SSL ERROR", e)
            continue
        #except as e:
        #    print("Some Exception has occured")
        #    continue

# Boot the server 
initSecureServer(ip, port, "rootCA.pem")