## Werewolf using epoll()
# In Communication.py

## def handleConnections

1. We first create a socket for server which represent as server socket. when a client attempts to connect to the server, this server socket accepts this connection request and creates a new socket for that client. This new socket is used for subsequent communication with that client (such as receiving and sending data). Each client will have a new socket corresponding to it.
2. Then we create a dictionary called ‘connections’ to record every client’s file descriptor and their corresponding socket
3. Next, we register server socket to an epoll object and entering a infinity loop to handle every incoming event trigger epoll.
4. In the loop: 
   - If event is from server socket, means we have new connection. Then we store its socket and file descriptor for the new client.
     then register it to epoll object
   - If event if from client socket, means we received new data. Then we read the data from this socket and store it to a buffer called data_received. If the data we received is ‘connect’, then we would send a welcome message 
   - Otherwise, if the data we receive is ‘ ‘, means the connection is closed. Then we would close the corresponding socket and remove it from epoll
5. Finally, when the server is closed, we remove server socket from epoll and close the server socket.

## def broadcast

1.  we switch players[player][1] to details[1] (details[1] stands for the socket of the player)
