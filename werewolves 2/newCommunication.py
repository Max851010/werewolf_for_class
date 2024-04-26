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
import signal
import random

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
stop_chat = type('StopChat', (object,), {'stop': False})()


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

con_handle_bool = 1

import socket
import select
import random
import time
#socket setting
def setup_server_socket(port=9999, max_con=100):
    SerSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SerSoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    SerSoc.bind(('localhost', port))
    SerSoc.listen(max_con)
    SerSoc.setblocking(0)
    return SerSoc

def handleConnections(Start_T, randomize):
    global con_handle_bool, all

    # Read names from file
    names = []
    with open('names.txt', 'r') as file:
        names = file.read().splitlines()
    if randomize:
        random.shuffle(names)

    # server socket with epoll!!
    epoll = select.epoll()
    SerSoc = setup_server_socket()
    epoll.register(SerSoc.fileno(), select.EPOLLIN)

    try:
        conns = {}
        addr = {}
        dataIN = {}
        con_handle_bool = True
        start_time = time.time()

        while con_handle_bool and time.time() - start_time < Start_T:
            events = epoll.poll(1)
            ##go through
            for filenum, event in events:
                if filenum == SerSoc.fileno():
                    connection, address = SerSoc.accept()
                    connection.setblocking(0)
                    fd = connection.fileno()
                    epoll.register(fd, select.EPOLLIN)
                    conns[fd] = connection
                    addr[fd] = address
                    dataIN[fd] = ''
                elif event & select.EPOLLIN:
                    data = conns[filenum].recv(1024).decode('utf-8')
                    if data:
                        dataIN[filenum] += data
                        if 'connect' in dataIN[filenum]:
                            name_index = int(addr[filenum][1]) % len(names)
                            name = names[name_index]
                            message = "Hello, {}. You are connected. Please wait for the game to start.".format(name)
                            conns[filenum].sendall(message.encode('utf-8'))
                            epoll.modify(filenum, select.EPOLLOUT)
                    else:
                        epoll.unregister(filenum)
                        conns[filenum].close()
                        del conns[filenum]
                elif event & select.EPOLLOUT:
                    conns[filenum].sendall("Message to send".encode('utf-8'))
                    epoll.modify(filenum, 0)
                elif event & select.EPOLLHUP:
                    epoll.unregister(filenum)
                    conns[filenum].close()
                    del conns[filenum]
        con_handle_bool = False
        all = conns
    finally:
        epoll.unregister(SerSoc.fileno())
        epoll.close()
        SerSoc.close()
    return all

###############################

##broadcast with socket
def broadcast(message, everysockets):
    """
    Send a message to all clients except the sender.
    """
    for sock in everysockets.values():
        try:
            sock.send(message.encode('utf-8'))
        except Exception as e:
            print("Broadcast failed to", sock, "with error", e)

def send(msg, client_soc):
    """Send a message to the client through the socket."""
    if readVulnerability_2 != 0:
        #  injection or vulnerabilities? nope.
        msg = msg.replace("'", '').replace(';', '').replace('"', '').replace('\n', '').replace('(', '[').replace(')', ']').replace('>', '').replace('<', '').replace(':', '')

    try:
        # msg form:
        # msg = ':' + 'sender' + ':' + msg + '\n'
        client_soc.sendall(msg.encode('utf-8'))
    except Exception as e:
        print 'send error: %s' % str(e)
    #if len(msg)!=0:
      #          msg='(echo :%s:%s > %s%sD/%s) 2> /dev/null &'%(sender,msg,pipeRoot,pipe,pipe)
       #         o=os.popen(msg)

def recv(client_soc):
    """
    Receive data from the socket. The data is decoded from UTF-8 to Unicode.
    """
    try:
        data = client_soc.recv(1024)  # Adjust buffer size as needed
        if data.decode("utf-8") == "CLOSE":
            print "Game closes by clients"
            os.kill(os.getpid(), signal.SIGINT)

        if not data:
            return None  # No data received, possibly connection is closed
        return data.decode('utf-8')  # Decode from UTF-8 to Unicode string
    except socket.error as e:
        print "Socket error:", e##log('receive error:%s'%p, 0, 0, 0)
        return None


#print, publicLog, modLog
##only for vote and poll now.
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

def multiRecv(theOne_soc, clientsoc, clientid, toVote=False):
    """
    Process incoming messages from a specific player's socket.
    """
    global deathspeech, deadGuy, voters, allowed  #  globally defined
    
    try:
        message = recv(theOne_soc)  # recv handles decoding
        if message:
            ##same cat
            if deathspeech and clientid == deadGuy:
                print str(clientid), "'s deathspeech: ", message
                broadcast("%s-%s" % (clientid, message), modPlayers(clientid, clientsoc))
            elif (toVote==True) or (votetime and clientid in voters):
                print str(clientid), "votes", message
                vote(clientid, message)
            elif clientid in allowed:
                print "allowed msg: %s" % message
                broadcast("%s-%s" % (clientid, message), modPlayers(clientid, clientsoc))
            else:
                print "Else msg: ", message
    except Exception as e:
        print "Error handling message for %s: %s" % (clientid, e)

def groupChat(clientsoc, chat_duration, toVote=False):
    """
    Handle group chat using select for efficient I/O multiplexing, with time control.
    """
    global stop_chat
    print "Group Chat started"
    sockets_list = list(clientsoc.values())
    client_ids = {sock.fileno(): oneid for oneid, sock in clientsoc.items()}
    start_time = time.time()
    ##make sure time limit
    try:
        while (time.time() - start_time) < chat_duration:
            read_sockets, _, _ = select.select(sockets_list, [], [], 0.1)

            for notified_socket in read_sockets:
                oneid = client_ids[notified_socket.fileno()]
                if toVote:
                    multiRecv(notified_socket, clientsoc, oneid, True)
                else:
                    multiRecv(notified_socket, clientsoc, oneid, False)

    finally:
        print "Chat session ended."

def close_groupChat():
    """
    Signal to close the group chat using the global stop_chat variable.
    """
    global stop_chat
    stop_chat.stop = True

def modPlayers(exclude_player, clientsoc):
    """
    Modify the list of players to exclude the sender from receiving their own messages.
    """
    return {p: s for p, s in clientsoc.items() if p != exclude_player}


votetime = 0
voteAllowDict = {'w':0, 'W':0, 't':0}
votes = {}
votesReceived = 0
voters = {}
targets = []
character = ""

# Global dictionary to determine if user has voted
voter_targets = {}

##everthing might stay the same except using groupChat
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

    #sleep(duration + 1)
    log(str(votes), 1, logChat, 1)

    results = []
    mode = 0
    groupChat(passedVoters, duration + 1, True)
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

##this part can remain the same. no new method needed.
def vote(voter, target):
    global votes, votesReceived, voters, character, isSilent, voter_targets

    # Code Updated on 7/20 by Tim
    if voter_targets.get(voter, None) == None:  # Added line

        unicode_targets = [unicode(t) for t in targets]
        if target in unicode_targets:
            try: votes[target] += 1  # changed from += 1 to just 1
            except: votes[target] = 1
            #message[0] is sent to who[0]; message[1] sent to who[1]; etc.
            messages = []
            who = []

            log(str(voter) + " voted for " + str(target), 1, 0, 1)

            if character == "witch":
                messages.append("Witch voted")
                who.append(all)
            elif character == "wolf":
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, str(target)))
                #messages.append("Wolf vote received.")
                who.append(voters)

                messages.append("Wolf vote received.")
                comp = complement(voters, all)
                who.append(comp)
                #who.append(complement(voters,all))
            else:#townsperson vote
                if isSilent: messages.append('%s voted.'%voter)
                else: messages.append('%s voted for %s'%(voter, str(target)))
                who.append(all)

            for i in range(len(messages)):
                broadcast(messages[i], who[i])


            votesReceived += 1
            voter_targets[voter] = target  

            if votesReceived == len(voters): skip()

        else:
            #vote_targets[voter] = None  # Added by Tim
            send('invalid vote: %s'%str(target), voters[voter])

    # Added by Tim    
    else:
        send('You already voted: %s'%str(target), voters[voter])

def spawnDeathSpeech(player, players, endtime):
    global deathspeech, deadGuy
    deathspeech = 1
    deadGuy = player

    groupChat(players, endtime)

    deathspeech = 0
    deadGuy = ""

