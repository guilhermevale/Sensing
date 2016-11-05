#!/usr/bin/python           # This is server.py file

import socket               # Import socket module

import signal
import sys


class Server(object):
  #  host = ""
   # port = 0
   # s = None

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = socket.socket()
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))        # Bind to the port
        self.s.listen(5)

    def create_connection(self):

        c, addr = self.s.accept()     # Establish connection with client
        print 'Got connection from', addr
        return c

    def receive_data(self, c):
        data = c.recvfrom(1024)
        return(data[0])

    def close_connection(self):
        self.s.close()    
