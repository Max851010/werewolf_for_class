#Author: Mike Jacobi
#Test and Update: Xu Zhang
#Virtual Werewolf Game
#Collaborators: Roya Ensafi, Jed Crandall
#This is an example client for players to connect to the Mafia server

#Copyright (c) 2012 Mike Jacobi, Xu Zhang, Roya Ensafi, Jed Crandall
#This file is part of Virtual Werewolf Game.

#Virtual werewolf is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#Virtual werewolf is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Virtual werewolf.  If not, see <http://www.gnu.org/licenses/>.
import socket
import sys
import select
import signal

##socket
def connect_to_server(host='localhost', port=9999):
    """ Create a socket connection to the server """
    clientsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientsoc.connect((host, port))
        clientsoc.setblocking(0)  # Set the socket to non-blocking
        clientsoc.sendall("connect")
        return clientsoc
    except socket.error as e:
        print "Failed to connect to the server:", e
        sys.exit()

def listen(server_soc):
    """ Check for messages from the server """
    try:
        while True:
            ready_cli, _, _ = select.select([server_soc], [], [], 0.5)
            if server_soc in ready_cli:
                data = server_soc.recv(1024).decode()
                if not data:
                    print "Connection closed by the server."
                    return False
                else:
                    print data
            return True
    except Exception as e:
        print "Error receiving data:", e
        return False

def send(server_soc):
    """Send a message entered by the user."""
    try:
        readyy, _, _ = select.select([sys.stdin], [], [], 0.1)
        if readyy:
            msg = sys.stdin.readline().strip()  # Read a line from stdin without blocking the program
            if msg:
                server_soc.sendall(msg.encode())
                if msg.lower() == 'exit':
                    return False
        return True
    except Exception as e:
        print("Error sending data:", e)
        return False

##for close
def signal_handler(signal, frame, server_soc):
    """Handle SIGINT and SIGTERM to close the socket gracefully."""
    print("\nReceived termination signal, closing connection...")
    server_soc.sendall("CLOSE".encode())
    server_soc.close()
    sys.exit(0)

if __name__ == '__main__':
    server_soc = connect_to_server()
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, server_soc))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, server_soc))

    print "Connected. Type 'exit' to quit."
    try:
        while True:
            
            if not listen(server_soc):  # Listen for incoming messages
                break
            if not send(server_soc):  # Check for user input and send messages
                break
    finally:
        server_soc.close()
        print "Disconnected !!"

