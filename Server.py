import socket
import ssl

ip = '127.0.0.1'
port = 12000

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


def handle(conn):
    """ Sends the client an ok message confirming a successful connection"""
    print("[Client]:",conn.recv().decode())
    conn.write(b'HTTP/1.1 200 OK\n\n%s' % conn.getpeername()[0].encode())

def initSecureServer(ip, port, cafile):
    """Starts a secure server using SSL """
    print("Starting server")

    #Initiate a secure connection
    init_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    init_sock.bind((ip, port))
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
            
            # Send response, close connection
            print("Socket wrapped, printing message") 
            handle(secure_sock)
            print("Response sent, closing connection")
            secure_sock.close()

        except ssl.SSLError as e:
            print("SSL ERROR", e)
            continue
        except:
            print("Some Exception has occured")
            continue

# Boot the server 
initSecureServer(ip, port, "rootCA.pem")