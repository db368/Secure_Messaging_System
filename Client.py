import socket
import time
import ssl
import json
import os
import sys
import threading
from time import sleep

port = 12000
host_ip = 'localhost'
username = None
get_back = False

def startConnection(host_ip, port):
    """Initiates a Connection with the Server Module """
    # Create HTTP Socket and send our get request
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    attempts = 0

    # Do a quick try catch for the server not being up
    while (attempts<3):
        try: 
            sock.connect((host_ip, port))
            break
        except ConnectionRefusedError:
            if attempts == 2:
                input("Connection refused. Terminating")
                exit(0)
            else:
                print("Connection refused, retrying...")
            time.sleep(1)
        attempts = attempts + 1
    
    return sock

def handle(conn):
    """Send a request confirming our connection """
    print("Sending verification...")
    conn.write(b'GET / HTTP/1.1\n')
    print("[Server]:", conn.recv().decode())
    
    print("Beginning login loop")
    
    loginLoop(conn)
    conn.close()

def startSecureConnection(host_ip, port, cafile):
    """Initiates a Secure Connection with the Server at host_ip, listening
       on the given port, certified by the given cafile """
    
    print("Booting client.")
    
    # Create Socket and context for server authentication
    initial_sock = socket.socket(socket.AF_INET)
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    context.load_cert_chain(certfile="client.crt", keyfile = "client.key")
    context.set_ciphers("HIGH:!aNULL:!kRSA:!PSK:!SRP:!MD5:!RC4")
    
    # Wrap Socket
    sock = context.wrap_socket(initial_sock, server_hostname=host_ip)
    attempts = 0

    print("Socket wrapped, attempting to connect to the server")
    
    # Do a quick try catch to allow for retrying if the server isn't up
    while (attempts<10):
        try: 
            sock.connect((host_ip, port))
            break

        # If it doesn't work, try again a couple times
        except ConnectionRefusedError:
            if attempts == 10:
                input("Connection refused after 10 attempts. Terminating.")
                exit(0)
            else:
                print("Connection refused, retrying...")
            time.sleep(1)
        
        # Throw an error if the cert cannot be verified
        except ssl.SSLCertVerificationError as e:
            print("Cert Could not be verified!", e)
            exit(-1)
            break
        attempts = attempts + 1
        continue
        # Check for ssl exceptions

    return sock

def tryAndSend(conn, s, timeouts=3):
    """ Tries to send the specified string to the given connection
        and decode the string it returns."""

    if s is not None: 
        conn.write(s)

    conn.settimeout(20.0)
    for i in range(timeouts):
        try:
            response = conn.recv().decode("utf8")
            return response
       
        except TimeoutError:
            attempts += 1
        except ConnectionResetError:
            print("Server died")
            sys.exit(-1)

    # If we got here, then the thing timed out
    return False


def testMight(password):
    """Checks the strength of the specified password"""
    # Gather Info   
    n = len(password)
    numbers = sum(c.isdigit() for c in password)
    words = sum(c.isalpha() for c in password)
    spaces = sum(c.isspace() for c in password)
    other = len(password) - words - spaces

    # Check each criteria
    if n<8:
        print("Password is too short")
        return False
    if spaces > 0:
        print("Password has spaces")
        return False
    if numbers<2:
        print("Password has less than 2 numbers")
        return False

    return True

def loginLoop(conn):
    """ Requests password and username from the client using the specified connection"""
    # Clear the screen
    os.system("cls")
    
    global username

    # Check to see if this is a new user. If not, continue going
    while True:
        newuser = input("Are you a new user y/n?")
        if newuser == 'y':
            # User Registration Loop
            while True:
                os.system("cls")
                print("____Registration Page_____")
                print("Password Requirements:")
                print("- Must be atleast 8 characters long")
                print("- Must have atleast 2 numbers")
                print("- No spaces")
                username = input("New Username: ")
                password = input("New Password: ")
                
                # Test if password meets standards
                if not testMight(password):
                    input("Press Enter to try again")
                    continue
                
                # Have user confirm password
                cpassword = input("Confirm Password: ")
                if not password == cpassword:
                    input("Passwords are different, try again")
                    continue
                
                content = {"purpose":"newuser", "username":username, "password":password}

                resp = tryAndSend(conn, json.dumps(content).encode("utf-8"))

                # Handle response from server 
                if resp == "SQL_FAIL":
                    print("Something went wrong...")
                    continue
                elif resp == "ALREADY_EXIST":
                    input("That username already exists, try again")
                    continue
                elif resp == "WEAK_PASS":
                    input("That password is too weak, try again")
                    continue
                elif resp == "SUCCESS":
                    print("User Successfully added!")
                    break
            break
        elif newuser == 'n':
            break
        else:
            print("Please only respond with y or n")
            continue
    
    # Take username and password from the user
    passisgood = False
    while not passisgood:
        os.system("cls")
        print("______Login Page______")
        username = input("Please enter your username: ")
        password = input("Please enter your password: ")

        # Create a dictionary with the info needed for login
        content = {"purpose":"login", "username":username, "password":password}        
        # Try sending this it to the server and checking the results
        resp = tryAndSend(conn, json.dumps(content).encode("utf-8"))
        if resp == "SUCCESS":
            inputLoop(conn, username)
        else:
            print("That username/password pair does not exist")
            input("Press enter to try again.")
            continue
        return

        if resp is False:
            print("The server timed out!")
            continue

def interpretCommand(cmd):
    """ Interprets whether or not a / command has been executed """
    # Strip leading and trailing whitespace
    cmd = cmd.strip()

    # Check to see if there was a / in front of the command
    if not cmd[0] == "/":
        return None
    
    # Split by space then return
    return cmd.split('/')[1].split(" ")

def inputLoop(conn, username):
    """ The main menu of the client"""
    while True:
        os.system("cls")
        print("______ Main Menu ______")
        print("Welcome", username + "!")
        print("")
        print("What would you like to do?")
        print("1) See available rooms")
        print("2) Create new Room")
        print("3) Start a Private Chat")
        print("4) Add new Friend")
        print("5) Check Notifications")
        print("6) Exit")
        
        command = input()
        if command == "1":
            print("checking available rooms...")
            # Get room list from the server
            content = {"purpose":"get_rooms"}
            r = tryAndSend(conn, json.dumps(content).encode("utf-8"))

            # Decode this json, then iterate through and print rooms
            j = json.loads(r)
            for rn,oc in j.items():
                print(rn + ": " + str(oc), "Users")
            
            #Loop through and ask user if they would like to join a room
            ui = input("Type a valid room name to join it, or /back to return")
            while True:
                
                # This room is in our list of rooms, join the specified room
                if ui in j:
                    content = {"purpose":"join_room", "name":ui}
                    success = tryAndSend(conn, json.dumps(content).encode("utf-8"))

                    # Check to see if this was successful
                    if success:
                        messagingMode(conn, ui)
                        break
                    else:
                        input("Room joining failed! Returning to main menu")
                    continue
                
                # This is not a valid room 
                else:
                    #Check to see if the user input a /back
                    pc = interpretCommand(ui)
                    if pc and pc[0] == "back":
                        continue
                    # otherwise just go back to looping 
                    ui = input(ui + " is not a valid room name. Try again.")

        elif command == "2":
            # Get room name from user 
            rn = input("Please enter the name for this new room: ")
            content = {"purpose":"create_room", "name":rn}
            print("Creating new room...")
            res = tryAndSend(conn, json.dumps(content).encode("utf-8"))
            
            # Interpret return. 0 on success, 1 on failure
            if res == 0:
                input("The room name requested already exists or is invalid. Press enter to return to main menu")
            elif res == 1:
                input("Room "+rn+" successfully created! Press Enter to Return to Main Menu")
        
        elif command == "3":
            # Get this user's friendslist
            content = {"purpose":"get_friends"}
            res = tryAndSend(conn, json.dumps(content).encode("utf-8"))

            # Decode list, and iterate through to print friends           
            friendlist = json.loads(res)
            counter = 1
            friends = []
            for friend,status in friendlist.items():
                print(str(counter)  + ")", friend,":", status)
                friends.append(friend)
                counter+=1
            
            # Ask the client to start a room with the specified friend
            target = input("Type the number of the friend you want to message")
            try:
                # Check to see if this number is in range
                index = int(target) - 1
                if index > counter or index < 0:
                    print(index, ">", counter, index>counter)
                    raise ValueError
                
                target = friends[index]

                # Send a request to the server that we're waiting
                content = {"purpose":"start_p2p", "username":target}
                result = tryAndSend(conn, json.dumps(content).encode('utf-8'))
                if result == "0":
                    input("FAILURE ! Send me some angry emails")
                elif result == "1":
                    waitForFriend(conn, "localhost", 3939)
            except ValueError as e:
                input("That's not a valid number, returning to main menu...")
            
        
        elif command == "4":
            # Send the name of the client that the user would like to add
            sname = input("Type the name of the user you'd like to add: ")
            content = {"purpose":"search_username", "like":sname}  
            names = tryAndSend(conn, json.dumps(content).encode("utf-8"))         

            # Print a list of names from the server in numerical order
            print(names)
            namelist = json.loads(names)["results"]
            counter = 1
            for name in namelist:
                print(str(counter) + ")", name)
                counter+=1
            
            # Take user input on one to send a request to 
            target = input("Type the number of the user you would like to add as a friend")
            try:
                # Check to see if this number is in range
                index = int(target) - 1
                if index > counter or index < 0:
                    print(index, ">", counter, index>counter)
                    raise ValueError
                
                target = namelist[index]

                # Send a request to the server to add these dudes
                content = {"purpose":"add_friend", "username":target}
                result = tryAndSend(conn, json.dumps(content).encode('utf-8'))
            except ValueError as e:
                input("That's not a valid number, returning to main menu...")
            
            print(result)
            if result == "0":
                input("FAILURE ! Send me some angry emails")
            
            else:
                input(target + " added successfully!")
        
        elif command == "5":
            content = {"purpose":"check_pings"}
            results = tryAndSend(conn, json.dumps(content).encode("utf-8"))
            
            j = json.loads(results)

            for one,two in j.items():
                print(one, "Has invited you to a room!")
                ip = two[1]
                port = two[0]
                if input("Press y to accept") == "y":
                    content = {"purpose":"accept_ping", "username":one}
                    print(tryAndSend(conn, json.dumps(content).encode("utf-8")))
                    PMode(conn, ip, port)
                    
                

            input()
        elif command == "6":
            print("Quitting...")
            exit()
        
        # Test Methods
        elif command == "93":
            print("Listening...")
            print(conn.recv())
        elif command == "39":
            print("Developer test activated, sending message")
            content = {"purpose": "announce", "msg":"Testing!"}
            conn.send(json.dumps(content).encode("utf-8"))

    
    print(" What would you like to do next?")

def waitForMessages(conn):
    """ Intended to be ran as a thread for recieving and printing messages"""
    global get_back

    # Store incoming messages as a list that we use like a queue
    buffersize = 12
    messageBuffer = []
    conn.settimeout(1.0)
    # Recieving loop
    while True:
        # Check if we should get back!
        if get_back:
            get_back = False
            return
        # Wait for message
        try:
            msg = json.loads(conn.recv().decode("utf-8"))
            sender = msg["sender"]
            text = msg["msg"]
        except:
            continue
        
        # Message recieved, see if the message buffer is full
        if len(messageBuffer) > 12:
            messageBuffer.pop(12)
        
        message = '[' + sender + ']:' + text + " | cypher, key, #bits" + str(conn.cipher())
        messageBuffer.insert(0, message)

        # Print all messages in buffer
        os.system("cls")
        # This actually reverses the thing
        for m in messageBuffer[::-1]:
            print(m)

def waitForFriend(init_conn, ip, port):
    """ Essentially play server for a bit """

    global username
    sender = username
    # Need to hunker for a bit and wait for the server to get us the ipa
    counter = 1
    while counter < 10:
        try:
            print("Waiting...")
            stuff = json.loads(init_conn.recv().decode("utf-8"))
            targetport = stuff["port"]
            print("Ok this guy should be at port", targetport)
            break
        except:
            # You didn't come this far to give up now!
            print("zzz")
            counter+=1
            if counter == 10:
                print("Guess they aren't coming...")
                return

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
            #if address[1] != targetport:
            #    print("Non, target",address," detected. Get out of here!")
            #    connection = None
            #    continue

            print("Connection recieved, attempting to wrap in a secure socket")
            
            # Define context and wrap socket
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile = "rootCA.pem")
            context.load_cert_chain(certfile="server.crt", keyfile = "server.key")
            secure_sock = context.wrap_socket(connection, server_side = True)
            
            # clients[address] = secure_sock
            print("Client achieved. Feel big?")
            break

        except ssl.SSLError as e:
            print("SSL ERROR", e)
            continue

    # Ok so we've got our socket, now we just neeed to set up our message thread, and hunker down
    new_thread =  threading.Thread(target=messagingMode, args=(secure_sock, "server"))
    new_thread.start()

    while True:
        message = input() 
        info = {"msg":message, "sender":sender}
        msg = json.dumps(info).encode("utf-8")
        try: 
            secure_sock.send(msg)
        except:
            print("That user is not getting msg")

def PMode(server_conn, ip, port):
    """ Enter private messaging mode"""

    # Wait for the server to send us some credentials
    print("Connecting to other user")
    
    #   Server should send us an IP and Port
    # stuff = json.loads(server_conn.recv().decode("utf-8"))
    # ip = stuff["ip"]
    # port = stuff["port"]


    # Ok now we do the init secure connection
    print("Connecting to guy at ip", ip, "and port", 3939)
    sock = startSecureConnection('localhost', 3939, "rootCA.pem")
    msg_thread = threading.Thread(target=waitForMessages, args=(sock,))
    msg_thread.start()

    global username
    sender = username
    while True:
        message  = input() 
        info = {"msg":message, "sender":sender}
        msg = json.dumps(info).encode("utf-8")
        try: 
            sock.send(msg)
        except:
            print("That user is not getting msg")

def messagingMode(conn, room_name, privatemode = False):
    """ Handle sending and recieving messages """
    global get_back
    # Set up listener thread
    msg_thread = threading.Thread(target=waitForMessages, args=(conn,))
    msg_thread.start()

    send_request = {"purpose":"msg_room", "name":room_name}
    while True: # Wait for input
        message = input(">")
        # Check to see if this was a command
        cmd = interpretCommand(message)
        
        if cmd is not None and len(cmd) > 0: 
            # Kill the message thread and tell the server
            if cmd[0] == "quit":
                content = {"purpose":"leave_room", "room_name":room_name}
                conn.send(json.dumps(content).encode("utf-8"))
               
                get_back = True
                print("Backing out of room...")
                # Give the socket time to timeout
                sleep(1)
                return
            else:
                print(cmd, "That is not a valid command!")
        
        # Send our message to the server
        send_request["msg"] = message
        conn.send(json.dumps(send_request).encode("utf-8"))



    
# Initiate our connection
s = startSecureConnection(host_ip, port, "rootCA.pem")
handle(s)

# Goto the login screen

print("Closing Client")

