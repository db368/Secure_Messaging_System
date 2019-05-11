import socket
import time
import ssl
import json
import os

port = 12000
host_ip = 'localhost'

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
    
    conn.write(s)
    for i in range(timeouts):
        try:
            response = conn.recv().decode("utf8")
            return response
        except TimeoutError:
            attempts += 1

    # If we got here, then the thing timed out
    return False


def loginLoop(conn):
    """ Requests password and username from the client using the specified connection"""
    # Clear the screen
    os.system("cls")
    
    # Define a flag to specify when pass and username are good
    passisgood = False
    while not passisgood:
        username = input("Please enter your username")
        password = input("Please enter your password")

        # Create a dictionary with the info needed for login
        content = {"purpose":"login", "username":username, "password":password}        
        # Try sending this
        resp = tryAndSend(conn, json.dumps(content).encode("utf-8"))
        print(resp)
        return
        if resp is False:
            print("The server timed out!")
            continue

# Initiate our connection
s = startSecureConnection(host_ip, port, "rootCA.pem")
handle(s)

# Goto the login screen

print("Closing Client")

