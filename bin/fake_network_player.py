from socket import *
import pickle

server_host = '' 
server_port = 60987 # selected for no good reason

sock = socket(AF_INET, SOCK_STREAM)
sock.bind((server_host,server_port))
sock.listen(5)

while 1:
    conn, addr = sock.accept()
    try:
        data_in = ''
        while 1:
            data = conn.recv(1024)
            if not data:
                break
            data_in += data
        
        print pickle.loads(data_in)
    finally:
        conn.close()
