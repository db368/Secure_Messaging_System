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
  print(conn.recv())
  conn.write(b'HTTP/1.1 200 OK\n\n%s' % conn.getpeername()[0].encode())

def initSecureServer(ip, port):
    """Starts a secure server using SSL """

    #Initiate a secure connection
    init_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    init_sock.bind((ip, port))
    init_sock.listen(1)
    
    print("Starting server")

    # Listen loop
    while(True):
        try:
            # Accept Incoming Connections
            info = {}
            connection, address = init_sock.accept()
    
            print("Connection get got")
            # Wrap this connection in SSL
            secure_sock = ssl.wrap_socket(connection, 
            ssl_version=ssl.PROTOCOL_TLSv1, ciphers="IDEA-CBC-SHA", server_side = True, certfile = "server.crt", keyfile="privkey.pem", do_handshake_on_connect=True)
            handle(secure_sock)

           # print("Secure Connection Constructed")
            #data = connection.recv(1024).decode("utf-8")
            #print(data)
            #response = "Pong"
            #connection.send(response.encode("utf-8"))
        except:
            continue

# Boot the server 
initSecureServer(ip, port)