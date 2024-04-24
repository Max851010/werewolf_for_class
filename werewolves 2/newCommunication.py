#Author: Mike Jacobi
#Test and Update: Xu Zhang
#Thanks to Jeff Knockel, Geoff Reedy, Matthew Hall, and Geoff Alexander for
#suggesting fixes to communication.py
#De-bugged, tested and edited: Tim C'de Baca and John Montoya 7/2014
#Virtual Werewolves
#Collaborators: Roya Ensafi, Jed Crandall
#Cybersecurity, Spring 2012
#This script has generic helper functions used by the Mafia server and clients

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


import os
import time
import threading
import random
from threading import Thread

all = {}

pipeRoot = '/home/moderator/pipes/'
logName = ''
mLogName = ''
conns = {}
allowed = {}
logChat = 0
currentTime = 0

readVulnerability = 1
readVulnerability_2 = 1
imposterMode = 1
isSilent = 1
def setVars(passedReadVulnerability, passedReadVulnerability_2,passedImposterMode, publicLogName, moderatorLogName):
    #descriptions of these variables can be seen in the config file
    global readVulnerability, readVulnerability_2,imposterMode, logName, mLogName
    readVulnerability = int(passedReadVulnerability)
    readVulnerability_2 = int(passedReadVulnerability_2)
    imposterMode = int(passedImposterMode)
    logName = publicLogName
    mLogName = moderatorLogName


#returns all elements in y that are not in x
def complement(x, y):
    z = {}
    for element in y.keys():
        if element not in x.keys(): z[element] = y[element]
    return z

#resets all variables
def skip():
    global currentTime, deathspeech, deadGuy, voters, targets
    currentTime = 0
    deathspeech = 0
    deadGuy = ""
    voters = {}
    targets = {}

def sleep(duration):
    global currentTime
    currentTime = time.time()
    while time.time() < currentTime + duration:
        time.sleep(1)

def setLogChat(n):
    global logChat
    logChat = n

def obscure():
    pass
    #while 1:
        #os.system('ls '+pipeRoot+'* > /dev/null 2> /dev/null')
        #time.sleep(.1)

def allow(players):
    global allowed
    allowed = players

isHandlingConnections = 1

import socket
import select
import random
import time

def setup_server_socket(port=9999, max_connections=10):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', port))
    server_socket.listen(max_connections)
    server_socket.setblocking(0)
    return server_socket

def handleConnections(timeTillStart, randomize):
    global isHandlingConnections, all

    # Read names from file
    names = []
    with open('names.txt', 'r') as file:
        names = file.read().splitlines()
    if randomize:
        random.shuffle(names)

    # Setup server socket
    epoll = select.epoll()
    server_socket = setup_server_socket()
    epoll.register(server_socket.fileno(), select.EPOLLIN)

    try:
        connections = {}
        addresses = {}
        data_received = {}
        isHandlingConnections = True
        start_time = time.time()

        while isHandlingConnections and time.time() - start_time < timeTillStart:
            events = epoll.poll(1)
            for fileno, event in events:
                if fileno == server_socket.fileno():
                    connection, address = server_socket.accept()
                    connection.setblocking(0)
                    fd = connection.fileno()
                    epoll.register(fd, select.EPOLLIN)
                    connections[fd] = connection
                    addresses[fd] = address
                    data_received[fd] = ''
                elif event & select.EPOLLIN:
                    data = connections[fileno].recv(1024).decode('utf-8')
                    if data:
                        data_received[fileno] += data
                        if 'connect' in data_received[fileno]:
                            name_index = int(addresses[fileno][1]) % len(names)
                            name = names[name_index]
                            message = "Hello, {}. You are connected. Please wait for the game to start.".format(name)
                            connections[fileno].sendall(message.encode('utf-8'))
                            epoll.modify(fileno, select.EPOLLOUT)
                    else:
                        epoll.unregister(fileno)
                        connections[fileno].close()
                        del connections[fileno]
                elif event & select.EPOLLOUT:
                    connections[fileno].sendall("Message to send".encode('utf-8'))
                    epoll.modify(fileno, 0)
                elif event & select.EPOLLHUP:
                    epoll.unregister(fileno)
                    connections[fileno].close()
                    del connections[fileno]
        isHandlingConnections = False
        all = connections
    finally:
        epoll.unregister(server_socket.fileno())
        epoll.close()
        server_socket.close()
    return all

###############################

def broadcast(msg, players):
    """Broadcast a message to multiple clients."""
    log(msg, 1, logChat, 1)  # Log the message being broadcast
    time.sleep(0.1)  # Small delay to prevent spam

    for player, details in players.items():
        try:
            #send(msg, details[1])  # Assuming details[1] is the socket
            send(msg, details)  # Assuming details[1] is the socket
        except Exception as e:
            print 'broadcast error: %s' % str(e)  # Optional: log this error


def send(msg, client_socket):
    """Send a message to the client through the socket."""
    if readVulnerability_2 != 0:
        # Sanitize message to avoid potential injection or other vulnerabilities
        msg = msg.replace("'", '').replace(';', '').replace('"', '').replace('\n', '').replace('(', '[').replace(')', ']').replace('>', '').replace('<', '').replace(':', '')

    try:
        # Prepare message in a format suitable for sending
        msg = ':' + 'sender' + ':' + msg + '\n'
        client_socket.sendall(msg.encode('utf-8'))
    except Exception as e:
        print 'send error: %s' % str(e)

def recv(client_socket):
    """Receive a message from the client through the socket."""
    try:
        output = client_socket.recv(1024).decode('utf-8').split('\n')
        for i in range(len(output)):
            if len(output[i]) > 0:
                parts = output[i].split(':')
                # Assuming part[1] would be 's' from the protocol you might be using
                if parts[1] == 's' or imposterMode == 1:
                    return parts
    except Exception as e:
        print 'receive error: %s' % str(e)


#print, publicLog, modLog
def log(msg, printBool, publicLogBool, moderatorLogBool):
    global logName, mLogName

    if printBool:
        print msg

    msg = '(%s) - %s\n'%(str(int(time.time())), msg)
    if publicLogBool:
        f = open(logName, 'a')
        f.write(msg)
        f.close()
    if moderatorLogBool:
        g = open(mLogName, 'a')
        g.write(msg)
        g.close()

def clear(pipes):
    for p in pipes:
        for i in range(10):
            t=Thread(target = recv, args = [p])
            t.setDaemon(True)
            t.start()

deathspeech = 0
deadGuy = ""
import socket
import select
import time

# Assuming the rest of communication.py is defined here, including necessary globals and functions

def multiRecv(player_socket, players_sockets):
    """
    Handle received messages from a player, process based on game state.
    """
    while True:
        try:
            msg = recv(player_socket)
            if msg is None:
                continue

            # Finding the player identifier from the socket
            player = [key for key, value in players_sockets.items() if value == player_socket][0]

            # Death speech handling
            if deathspeech and player == deadGuy:
                broadcast('%s-%s' % (player, msg), modPlayers(player, players_sockets))

            # Voting handling
            elif votetime and player in voters:
                vote(player, msg)

            # Group chat handling
            elif player in allowed:
                broadcast('%s-%s' % (player, msg), modPlayers(player, allowed))

            # Prevent spam
            else:
                time.sleep(1)
        except Exception as e:
            print 'Error in multiRecv:', str(e)
            break

def groupChat(players_sockets):
    """
    Initialize group chat without threads, using epoll to handle multiple receivers.
    """
    epoll = select.epoll()
    for sock in players_sockets.values():
        epoll.register(sock.fileno(), select.EPOLLIN)
    
    try:
        while True:
            events = epoll.poll(1)
            for fileno, event in events:
                if event & select.EPOLLIN:
                    sock = next((s for s in players_sockets.values() if s.fileno() == fileno), None)
                    if sock:
                        multiRecv(sock, players_sockets)
    finally:
        for sock in players_sockets.values():
            epoll.unregister(sock.fileno())
        epoll.close()

def modPlayers(exclude_player, players_sockets):
    """
    Modify the list of players to exclude the sender from receiving their own messages.
    """
    return {p: s for p, s in players_sockets.items() if p != exclude_player}


votetime = 0
voteAllowDict = {'w':0, 'W':0, 't':0}
votes = {}
votesReceived = 0
voters = {}
targets = []
character = ""

# Global dictionary to determine if user has voted
voter_targets = {}

def poll(passedVoters, duration, passedValidTargets, passedCharacter, everyone, isUnanimous, passedIsSilent):
    global votes, voteAllowDict, allowed, votesReceived, logChat, votetime, voters, targets, character, isSilent, voter_targets

    votetime = 1
    voters = passedVoters
    votesReceived = 0
    votes = {}
    targets = passedValidTargets
    character = passedCharacter
    isSilent = passedIsSilent

    voter_targets = {}

    sleep(duration + 1)
    log(str(votes), 1, logChat, 1)

    results = []
    mode = 0
    for v in votes.keys():
        if votes[v] > mode:
            mode = votes[v]
            results = [v]
        elif votes[v] == mode:
            results.append(v)

    #this var signifies the class of result
    #0 - results[0]=victim; 1 - vote not unan; 2 - vote is tie
    resultType = 0

    if int(isUnanimous) and mode != len(passedVoters): #the voteCount of the winner is not equal the number of voters
        resultType = 1
    elif len(results) > 1 or len(results) == 0:#tie or nonvote
        resultType = 2

    validTargets = []
    votetime = 0
    voters = {}
    #voter_targets = {}

    return results, resultType

def vote(voter, target):
    global votes, votesReceived, voters, character, isSilent, voter_targets

    # Code Updated on 7/20 by Tim
    if voter_targets.get(voter, None) == None:  # Added line

        if target in targets:
            try: votes[target] += 1  # changed from += 1 to just 1
            except: votes[target] = 1
            #message[0] is sent to who[0]; message[1] sent to who[1]; etc.
            messages = []
            who = []

            log(voter + " voted for " + target, 1, 0, 1)

            if character == "witch":
                messages.append("Witch voted")
                who.append(all)
            elif character == "wolf":
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, target))
                #messages.append("Wolf vote received.")
                who.append(voters)

                messages.append("Wolf vote received.")
                comp = complement(voters, all)
                who.append(comp)
                #who.append(complement(voters,all))
            else:#townsperson vote
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, target))
                who.append(all)

            for i in range(len(messages)):
                broadcast(messages[i], who[i])


            votesReceived += 1
            voter_targets[voter] = target  

            if votesReceived == len(voters): skip()

        else:
            #vote_targets[voter] = None  # Added by Tim
            send('invalid vote: %s'%target, voters[voter][1])

    # Added by Tim    
    else:
        send('You already voted: %s'%target, voters[voter][1])

def spawnDeathSpeech(player, endtime):
    global deathspeech, deadGuy
    deathspeech = 1
    deadGuy = player

    sleep(endtime)

    deathspeech = 0
    deadGuy = ""

