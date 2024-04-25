# Werewolf using epoll()
## In Communication.py

### def handleConnections

1. We first create a socket for server which represent as server socket. when a client attempts to connect to the server, this server socket accepts this connection request and creates a new socket for that client. This new socket is used for subsequent communication with that client (such as receiving and sending data). Each client will have a new socket corresponding to it.
2. Then we create a dictionary called ‘connections’ to record every client’s file descriptor and their corresponding socket
3. Next, we register server socket to an epoll object and entering a while loop to handle every incoming connections within the start time.
4. In the loop: 
   - If event is from server socket, means we have new connection. Then we store its socket and file descriptor for the new client in a variable 'connections'.
     then register this client socket to epoll object
   - If event if from client socket, means we received new data. Then we read the data from this socket and store it to a buffer called data_received. If the data we received is ‘connect’, then we would send a welcome message 
   - Otherwise, if the data we receive is ‘ ‘ or we received a epollhup event, means the connection is closed. Then we would close the corresponding socket and unregister it from epoll
5. Finally, when the start time is over, we leave this loop and return connections as all players

### def multi_recv
1. read the message from input player's socket and deal with these messages based on different situation(chat, vote, deathspeech)
2. since we didn't use multithread to deal with multi_recv, there is no need to use infinity loop to run the multi_recv.
3. compare to original multi_recv, we would need to additionally 'pass a boolean' to multi_recv means we are currently voting or not

### def groupchat
1. we get all player's socket and store it into socket_list
2. Within the chat duration, we use select.select to track every readable socket and use multi_recv to deal these messages.

### def poll
1. since we didn't use multi thread to keep receving message from player, everytime when we call poll function, we creat a group chat and set the Boolean 'vote' as true. So that the multi_recv function know we are currently voting

### def broadcast

we switch players[player][1] to details[1] (details[1] stands for the socket of the player)

### def send

we encode the message by utf-8 and send it through the client socket rather than pip

### def recv

we receive the message through the client socket and decode it by utf-8

## In client.py

### def connect_to_server

connect to server through the server socket and set it as non-blocking socket. If fail to connect to server, then print the error message

### def listen

entering a infinity while loop to recevie and print every message from the server

### def send

1. check if whether sys.stdin is ready to write, if yes, then try to read the starndard input and send it to the server.
2. if the input text is 'exit', then close the connection

### main

use def connect_to_server to connect to server, then entering an while loop to keep track message from server and user's input text
