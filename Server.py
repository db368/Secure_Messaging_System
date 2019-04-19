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
    """ Sends the client an ok message confirming successful HTTP connection"""
    print(conn.recv())
    conn.write(b'HTTP/1.1 200 OK\n\n%s' % conn.getpeername()[0].encode())

def initSecureServer(ip, port, cafile):
    """Starts a secure server using SSL """
    print("Starting server")

    #Initiate a secure connection
    init_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    init_sock.bind((ip, port))
    init_sock.listen(1)
    
    print("I'm all ears")

    # Listen loop
    while(True):
        try:
            # Accept Incoming Connections
            info = {}
            secure_sock = None
            connection, address = init_sock.accept()
    
            print("Connection get got")
            
            # Wrap this connection in SSL
            # secure_sock = ssl.wrap_socket(connection, 
            #ssl_version=ssl.PROTOCOL_TLSv1, ciphers="IDEA-CBC-SHA", server_side = True, certfile = "server.crt", keyfile="privkey.pem", do_handshake_on_connect=True)
            
            # Define context and wrap socket
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile = cafile)
            #context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:DHE-RSA-AES256-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES256-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES256-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA')
            context.load_cert_chain(certfile="server.crt", keyfile = "server.key")
            print("Cert Chain Locked and Loaded")
            secure_sock = context.wrap_socket(connection, server_side = True)
            handle(secure_sock)

            print("Secure Connection Constructed")
            #data = connection.recv(1024).decode("utf-8")
            #print(data)
            #response = "Pong"
            #connection.send(response.encode("utf-8"))
        except ssl.SSLError as e:
            print("SSL ERROR", e)
            continue
        except:
            print("Excepted")
            continue

# Boot the server 
initSecureServer(ip, port, "rootCA.pem")