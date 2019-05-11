import socket
import ssl
import threading
import json
import authMod as AuthMod

# - -- GLOBALS -- -
ip = '127.0.0.1'
port = 12000
clients = []
threads = []

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
    """ Handles all requests from clients"""
    print("Thread started, waiting on client")
    print("[Client]:",conn.recv().decode())
    conn.write(b'HTTP/1.1 200 OK\n\n%s' % conn.getpeername()[0].encode())

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
                if res == "SUCCESS":
                    conn.send("SUCCESS".encode())
                else:
                    conn.send("FAILURE".encode())
                
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
            clients.append(secure_sock)
            new_thread =  threading.Thread(target=handle, args=(secure_sock, address))
            new_thread.start()
            threads.append(new_thread)
            print("Client achieved.")

        except ssl.SSLError as e:
            print("SSL ERROR", e)
            continue
        except:
            print("Some Exception has occured")
            continue

# Boot the server 
initSecureServer(ip, port, "rootCA.pem")