from socket import *
import pickle
from random import randint

server_host = '' 
server_port = 60987 # selected for no good reason

sock = socket(AF_INET, SOCK_STREAM)
sock.bind((server_host,server_port))
sock.listen(5)

try:
    while 1:
        conn, addr = sock.accept()
        try:
            data_in = ''
            print "waiting to recv"
            data = conn.recv(4096)
            print "received from socket: %s <%d>" % (data, len(data))
            data_in += data
            #board = pickle.loads(data + "\n")
            valid_moves = data.split("/")
            print len(valid_moves)
            move = valid_moves[randint(0, len(valid_moves) - 1)]
            print "sending" + move
            conn.send(move)

        finally:
            conn.close()
finally:
    sock.close()
