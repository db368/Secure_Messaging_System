import socket
import time
import ssl

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
    conn.write(b'GET / HTTP/1.1\n')
    print(conn.recv().decode())

def startSecureConnection(host_ip, port, cipher_list, cafile):
    """Initiates a Secure Connection with the Server Module """
    
    # Create Socket and context for server authentication
    initial_sock = socket.socket(socket.AF_INET)
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cafile)
    # context.options |= ssl.HAS_TLSv1
    # context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 
    # optional    # context.load_verify_locations("server.pem")
    # sock = ssl.wrap_socket(initial_sock, ssl_version = ssl.PROTOCOL_TLSv1, ciphers = cipher_list)
   # context.load_cert_chain(keyfile="server.key", certfile="server.pem", password="Miku") 
    context.load_cert_chain(certfile="client.crt", keyfile = "client.key")
    context.set_ciphers("HIGH:!aNULL:!kRSA:!PSK:!SRP:!MD5:!RC4")
    sock = context.wrap_socket(initial_sock, server_hostname=host_ip)
    attempts = 0

    # Do a quick try catch for the server not being up
    while (attempts<3):
        try: 
            sock.connect((host_ip, port))
            break

        # If it doesn't work, try again a couple times
        except ConnectionRefusedError:
            if attempts == 2:
                input("Connection refused. Terminating")
                exit(0)
            else:
                print("Connection refused, retrying...")
            time.sleep(1)
        # Check to see if certs work out
        except ssl.SSLCertVerificationError as e:
            print("Cert Refused!", e)
            exit(-1)
            break
        attempts = attempts + 1
        continue
        # Check for ssl exceptions

    return sock

# Initiate our connection
s = startSecureConnection(host_ip, port, "IDEA-CBC-SHA", "rootCA.pem")

handle(s)



