import socket
import time
import ssl

port = 12000
host_ip = '127.0.0.1'

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
    conn.write(b'GET / HTTP/1.1\n')
    print(conn.recv().decode())

def startSecureConnection(host_ip, port, cipher_list):
    """Initiates a Secure Connection with the Server Module """
    
    # Create Socket and init request
    initial_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = ssl.wrap_socket(initial_sock, ssl_version = ssl.PROTOCOL_TLSv1, ciphers = cipher_list)
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

# Initiate our connection
s = startSecureConnection(host_ip, port, "IDEA-CBC-SHA")

handle(s)
#Send customary ping
#s.send("Ping".encode("utf-8"))

# Recieve and print pong
#response = s.recv(1024).decode("utf-8")
#print(response)


