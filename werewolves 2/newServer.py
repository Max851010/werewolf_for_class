#Author: Mike Jacobi
#Test and Update: Xu Zhang
#Virtual Werewolves
#Collaborators: Roya Ensafi, Jed Crandall
#De-bugged, tested and edited: Tim C'de Baca and John Montoya 7/2014
#server.py is the automated moderator for Virtual Werewolves

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

import traceback
import datetime
import sys
import os
import time
import random
import signal
import newCommunication as c
import threading

i = {}
inputVars = open('config', 'r').read().split('\n')
for var in inputVars:
    var = var.strip('\n').split('=')
    key = var[0]
    try:#if a line doesn't have an = sign
        value = var[1]
    except:
        continue
    i[key] = value
logFile = ''

#time parameters
timeTillStart = int(i['timeTillStart'])
wolftalktime = int(i['wolfTalkTime'])
wolfvotetime = int(i['wolfVoteTime'])
townvotetime = int(i['townVoteTime'])
towntalktime = int(i['townTalkTime'])
witchvotetime = int(i['witchVoteTime'])
deathspeechtime = int(i['deathSpeechTime'])

test = int(i['test'])
giveDeathSpeech = int(i['deathSpeech'])
numWolves = int(i['numWolves'])

#moderator assignment global vars
wolfChoose = int(i['wolfChoose'])
moderatorAssignment = 0
moderatorAssignmentContinue = 0
moderatorAssignmentList = []

#group people by roles
all = {}
wolves = {}
townspeople = {}
witch = {}

potions = [int(i['kill']), int(i['heal'])]#[kill,heal]

round = 1

def removePlayer(player):
    global all, wolves, witch, logChat
    isTownsperson = True

    newAll = {p: all[p] for p in all if p != player}
    newWolves = {p: wolves[p] for p in wolves if p != player}
    if player in wolves:
        c.log('%s-wolf killed.' % player, 1, 0, 1)
        isTownsperson = False
    if player in witch:
        c.log('%s-witch killed' % player, 1, 0, 1)
        witch = {}
        isTownsperson = False
    if isTownsperson:
        c.log('%s-townsperson killed' % player, 1, 0, 1)

    c.setLogChat(1)
    if giveDeathSpeech:
        c.broadcast('These are %ss last words.' % player, newAll)
        c.send("Share your parting words.", all[player][1])
    c.setLogChat(0)

    c.send("YOU ARE DEAD. You will continue getting game updates, Please *DO NOT* close this terminal", all[player][1])

    all = newAll
    wolves = newWolves

    if len(wolves) <= 1:
        global wolftalktime
        wolftalktime = 0


gameNumber = 9999
winner = 'No winner'
def quitGame(signal, frame):
    global all, winner, gameNumber
    try:
        c.broadcast('close', all)
        c.log('\nGAME FORCE QUIT BY MODERATOR', 1, 1, 1)
        os.chmod(moderatorLogName, 0744)
        if not test:
            os.system('echo "Game %d is over. %s. Please reconnect your client to play again." | wall' % (gameNumber, winner))
    finally:
        # Ensure all sockets are closed properly
        for player, details in all.items():
            details.close()  # Assuming details[1] is the socket
        sys.exit()


signal.signal(signal.SIGINT, quitGame)

def assign():
    global all, wolves, townspeople, witch, moderatorAssignment, moderatorAssignmentContinue, moderatorAssignmentList, moderatorAssignmentChoices
    from communication import send  # Ensure 'send' is compatible and available

    numPlayers = len(all.keys())

    if not wolfChoose:  # Randomly assign roles
        # Creating role configuration
        config = ['W'] + ['w' for _ in range(numWolves)] + ['t' for _ in range(numPlayers - numWolves - 1)]
        random.shuffle(config)  # Randomize roles

        # Assign roles and inform players
        for idx, player in enumerate(all):
            role = 'townsperson'
            if config[idx] == 'w':
                wolves[player] = all[player]
                role = 'wolf'
            elif config[idx] == 'W':
                witch[player] = all[player]
                townspeople[player] = all[player]
                role = 'witch'
            else:
                townspeople[player] = all[player]

            send('~~~~~ YOU ARE A %s ~~~~~' % role, all[player])
    else:  # Moderator chooses roles
        moderatorAssignment = 1
        print '\nModerator Assignment:'
        moderatorAssignmentChoices = all.keys()
        print 'Choose wolves from %s. Enter "done" when finished.' % str(sorted(moderatorAssignmentChoices))
        moderatorAssignmentContinue = 1
        while moderatorAssignmentContinue == 1:
            time.sleep(1)

        wolfList = moderatorAssignmentList
        moderatorAssignmentList = []
        moderatorAssignmentChoices = [p for p in all if p not in wolfList]
        print 'Choose witch from %s.' % str(sorted(moderatorAssignmentChoices))
        moderatorAssignmentContinue = 1
        while moderatorAssignmentContinue == 1:
            if len(moderatorAssignmentList) == 1:
                if moderatorAssignmentList[0] in wolfList:
                    moderatorAssignmentList = []
                else:
                    break
            else:
                time.sleep(0.1)

        witchList = moderatorAssignmentList
        moderatorAssignment = 0

        # Assign roles based on moderator's choices
        for player in all:
            role = 'townsperson'
            if player in witchList:
                witch[player] = all[player]
                role = 'witch'
            elif player in wolfList:
                wolves[player] = all[player]
                role = 'wolf'
            else:
                townspeople[player] = all[player]

            send('~~~~~ YOU ARE A %s ~~~~~' % role, all[player])


def standardTurn():
    global all, wolves, witch, potions, towntalktime, wolftalktime
    wolfkill = 0
    witchkill = 0
    try:
        c.broadcast("Night falls and the town sleeps. Everyone close your eyes.", all)
        c.log('Night', 0, 1, 0)

        # ************** WEREWOLVES ************************
        c.allow(wolves)
        if len(wolves) < 2:
            wolftalktime = 0
        c.broadcast("Werewolves, open your eyes.", c.complement(wolves, all))
        c.broadcast('Werewolves, %s, you must choose a victim. You have %d seconds to discuss. Possible victims are %s.' % (str(wolves.keys()), wolftalktime, str(sorted(all.keys()))), wolves)
        c.log('Werewolves debate', 0, 1, 0)
        # Allow real-time discussion for wolftalktime
        c.groupChat(wolves, wolftalktime)
        #time.sleep(wolftalktime)  # Controlled wait for discussion
        c.broadcast("Werewolves, vote.", c.complement(wolves, all))
        c.broadcast('Werewolves, you must vote on a victim to eat. You have %d seconds to vote. Valid votes are %s.' % (wolfvotetime, str(sorted(all.keys()))), wolves)
        c.log('Werewolves vote', 0, 1, 0)
        wolfvote, voteType = c.poll(wolves, wolfvotetime, all.keys(), 'wolf', all, i['wolfUnanimous'], i['wolfSilentVote'])
        c.broadcast('Werewolves, go to sleep.', c.complement(wolves, all))

        if voteType == 1:
            c.broadcast('Vote not unanimous, nobody eaten.', wolves)
            c.log('Werewolves not unanimous', 0, 1, 0)
        elif voteType == 2:
            c.broadcast('Tie', wolves)
            c.log('Werewolves vote tie', 0, 1, 0)
        elif voteType == 0:
            msg = "Werewolves, you selected to eat %s" % str(wolfvote[0])
            wolfkill = 1
            c.broadcast(msg, wolves)
            c.log('Werewolves selected %s' % str(wolfvote[0]), 0, 1, 0)

        # ************** WITCH ************************
        if len(witch) > 0 and (potions[0] or potions[1]):
            witchPlayer = witch.keys()[0]
            if wolfkill:
                validKills = [p for p in all if p != wolfvote[0]]
                witchmoves = validKills + ['Heal', 'Pass'] if potions[1] else validKills
                c.send('Witch, wake up. The wolves killed %s. Valid votes are %s.' % (str(wolfvote[0]), str(witchmoves)), witch[witchPlayer][1])
                witchVote, voteType = c.poll(witch, witchvotetime, witchmoves, 'witch', all, 0, 0)
                if witchVote == ['Heal']:
                    c.send('The Witch healed you!', all[wolfvote[0]][1])
                    potions[1] -= 1
                    wolfkill = 0
                elif witchVote != ['Pass']:
                    witchkill = 1
                    potions[0] -= 1

        # ************** DAY TIME - TOWN ***********************
        c.allow(all)
        if wolfkill:
            c.broadcast('The werewolves ate %s!' % wolfvote[0], all)
            removePlayer(wolfvote[0])
        if witchkill:
            c.broadcast('The Witch poisoned %s! %d poison[s] remaining.' % (witchVote[0], potions[0]), all)
            removePlayer(witchVote[0])

        if len(wolves) == 0 or len(wolves) == len(all):
            return 1

        c.broadcast('It is day. Everyone, open your eyes. You have %d seconds to discuss who the werewolves are.' % towntalktime, all)
        c.groupChat(all, towntalktime)
        #time.sleep(towntalktime)  # Controlled wait for discussion

        c.broadcast('Townspeople, you have %d seconds to cast your votes on who to hang. Valid votes are %s' % (townvotetime, str(sorted(all.keys()))), all)
        killedPlayer, voteType = c.poll(all, townvotetime, all.keys(), 'town', all, i['townUnanimous'], i['townSilentVote'])
        if voteType == 0:
            c.broadcast('The town voted to hang %s!' % killedPlayer[0], all)
            removePlayer(killedPlayer[0])

        return 1
    except Exception as error:
        c.log('STANDARDTURNERROR:%s' % str(error), 1, 0, 1)
        return 0
#        time.sleep(.1)

import select
import sys
import os

def listenerThread():
    """Handles moderator commands within the main loop using non-blocking input checks."""
    global round, all, moderatorAssignment, moderatorAssignmentContinue, moderatorAssignmentList, moderatorAssignmentChoices
    try:
        # Check if there's input to be read
        input_ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if input_ready:
            i = sys.stdin.readline().strip()
            if i == '':
                pass
            elif moderatorAssignment == 1 and i in moderatorAssignmentChoices:
                if i == 'done':
                    moderatorAssignmentContinue = 0
                elif i not in moderatorAssignmentList:
                    moderatorAssignmentList.append(i)
                    print 'added %s' % i
                else:
                    print 'invalid'
            elif i == 'help':
                os.system('cat moderatorHelp.txt')
            elif i == 'status':
                print 'round %d' % round
                print 'all:', ', '.join(all.keys())
                print 'wolves:', ', '.join(wolves.keys())
                wStatus = ': %d poisons, %d heals' % (potions[0], potions[1])
                print 'witch:', ', '.join(witch.keys()), wStatus
            elif i.startswith('kill '):
                player = i.split(' ')[1]
                c.broadcast('Moderator removed %s' % player, all)
                c.log('Moderator removed %s' % player, 0, 1, 0)
                removePlayer(player)
            elif i == 'skip':
                c.skip()
                c.log('Moderator skipped current section.', 0, 1, 0)
            else:
                audience = i.split(' ')[0]
                message = i[len(audience) + 1:]
                if audience == 'all':
                    c.broadcast('moderator to all-%s' % message, all)
                elif audience == 'wolves':
                    c.broadcast('moderator to wolves-%s' % message, wolves)
                elif audience == 'witch':
                    c.broadcast('moderator to witch-%s' % message, witch)
                else:
                    print '*** Start your message with "all", "wolves", or "witch". ***'
    except Exception as e:
        print 'Error reading moderator input:', str(e)


publicLogName = ''
moderatorLogName = ''
listenThread = None
chatThread = None

def main():
    global all, round, publicLogName, moderatorLogName, winner, gameNumber

    if test:
        publicLogName = 'log/dummy.log'
        moderatorLogName = 'log/dummy-m.log'
        os.chmod(moderatorLogName, 0700)
        gameNumber = 9999
    else:
        nextround = open('log/nextround', 'r')
        gameNumber = int(nextround.readline().strip('\n'))
        nextround.close()
        nextround = open('log/nextround', 'w')
        nextround.write(str(gameNumber + 1))
        nextround.close()
        msg = 'Game %d starts in %d seconds.' % (gameNumber, timeTillStart)
        os.system('echo "%s" | wall' % msg)
        publicLogName = 'log/%d.log' % gameNumber
        moderatorLogName = 'log/%dm.log' % gameNumber

        if i['moderatorLogMode'] == 1:
            os.system('touch ' + moderatorLogName)
            os.system('chmod 700 ' + moderatorLogName)
        else:
            os.system('cp log/template ' + moderatorLogName)

    c.setVars(i['readVulnerability'], i['readVulnerability2'], i['imposterMode'], publicLogName, moderatorLogName)

    c.log('GAME: %d' % gameNumber, 1, 1, 1)
    all = c.handleConnections(timeTillStart, int(i['randomizeNames']))

    assign()
    c.log('roles assigned', 1, 0, 1)

    c.log('\nBegin.', 1, 1, 1)
    c.broadcast('There are ' + str(len(wolves)) + ' wolves, and ' + str(len(all) - len(wolves)) + ' townspeople.', all)
    c.allow({})

    while len(wolves) != 0 and len(wolves) < len(all):
        listenerThread()  # Synchronously check for and handle moderator commands

        c.log('\n\n', 1, 1, 1)
        c.broadcast('*' * 50, all)
        c.broadcast('*' * 21 + 'ROUND ' + str(round) + '*' * 22, all)
        c.broadcast('*' * 15 + str(len(all)) + ' players remain.' + '*' * 18, all)
        c.broadcast('*' * 50, all)
        c.log('Round ' + str(round), 0, 1, 0)
        c.log('Townspeople: ' + str(all.keys()), 1, 1, 1)
        c.log('Werewolves: ' + str(wolves.keys()), 1, 0, 1)
        c.log('Witch: ' + str(witch.keys()), 1, 0, 1)
        round += 1
        standardTurn()  # Execute game turns as originally intended

    if len(wolves) == 0:
        winner = 'Townspeople win'
    elif len(wolves) == len(all):
        winner = 'Werewolves win'
    c.log('\n%s' % winner, 0, 1, 0)
    c.broadcast(winner, all)
    c.broadcast('close', all)

    c.log('End', 1, 1, 1)
    if not test:
        os.chmod('log/%dm.log' % gameNumber, 0744)
        os.system('echo "Game %d is over. %s. Please reconnect your client to play again." | wall' % (gameNumber, winner))

if __name__ == '__main__':
    main()

