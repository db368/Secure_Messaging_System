import socket
import time

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

s = startConnection(host_ip, port)

s.send("Ping".encode("utf-8"))
response = s.recv(1024).decode("utf-8")
print(response)
