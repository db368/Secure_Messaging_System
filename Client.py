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
    inputLoop(conn)
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
    while (attempts<3):
        try: 
            sock.connect((host_ip, port))
            break

        # If it doesn't work, try again a couple times
        except ConnectionRefusedError:
            if attempts == 2:
                input("Connection refused after 3 attempts. Terminating.")
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

    conn.settimeout(5.0)
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


def loginLoop(conn):
    """ Requests password and username from the client using the specified connection"""
    # Clear the screen
    os.system("cls")
    
    global username

    # Check to see if this is a new user. If not, continue going
    while True:
        newuser = input("Are you a new user y/n?")
        if newuser == 'y':
            # User Registration code
            username = input("New Username: ")
            password = input("New Password: ")

            content = {"purpose":"newuser", "username":username, "password":password}

            resp = tryAndSend(conn, json.dumps(content).encode("utf-8"))

            # Handle response from server 
            if resp == "SQL_FAIL":
                print("Something went wrong...")
                continue
            elif resp == "ALREADY_EXIST":
                print("That username already exists, try again")
                continue
            elif resp == "SUCCESS":
                print("User Successfully added!")
                break

        elif newuser == 'n':
            break
        else:
            print("Please only respond with y or n")
            continue
    
    # Take username and password from the user
    passisgood = False
    while not passisgood:
        username = input("Please enter your username: ")
        password = input("Please enter your password: ")

        # Create a dictionary with the info needed for login
        content = {"purpose":"login", "username":username, "password":password}        
        # Try sending this it to the server and checking the results
        resp = tryAndSend(conn, json.dumps(content).encode("utf-8"))
        print(resp)
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

def inputLoop(conn):
    """ The main menu of the client"""
    while True:
        os.system("cls")

        print("What would you like to do?")
        print("1) See available rooms")
        print("2) Create new Room")
        print("3) Exit")
        
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
                if ui in rn:
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
        
        message = '[' + sender + ']:' + text
        messageBuffer.insert(0, message)

        # Print all messages in buffer
        os.system("cls")
        # This actually reverses the thing
        for m in messageBuffer[::-1]:
            print(m)
    
def messagingMode(conn, room_name):
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

