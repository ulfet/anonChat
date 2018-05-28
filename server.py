from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from cryptography.fernet import Fernet
from cryptography.exceptions import InvalidSignature
from copy import deepcopy
import base64
import os
import random
import thread
import threading
import time

# initial server participant configuration
chatCapacity = 3
currentClients = []

clientNames = ["ulfet", "ozgur", "jennifer", "mary", "hamza"]
clientPasswords = ["ulfetp", "ozgurp", "jenniferp", "maryp", "hamzap"]
clientStatus = [False, False, False, False, False]

KNOWNADRESSES = {}
KNOWNPORTS = []


# generate server variables
HOST = ""
PORT = 1789
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)
SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
SERVER.bind(ADDRESS)

CHAT_ROOM_READY = False
CHAT_STARTED = False

# generate Fernet variables
# key = base64.urlsafe_b64encode(os.urandom(32))
SECRET_KEY_FOR_MESSAGES = "va2aCQbleD0z55zRfWRVEDMNhhEUCV8o1dUGJjjRAt8="
SECRET_KEY_FOR_AUTH     = "E-EKHr6Y9kCB4qUJQ-vAWf0d-qXMM9mGwhTjYVRLq6U="

# used for Fernet key generation
def generateFernetKey(messageOrAuth):
	if messageOrAuth == "message":
		return SECRET_KEY_FOR_MESSAGES
	if messageOrAuth == "auth":
		return SECRET_KEY_FOR_AUTH

# returns Fernet variable
def buildFernet(messageOrAuth):
	key = generateFernetKey(messageOrAuth)
	f = Fernet(key)
	return f

# check whether message is valid or not
def checkMessageValidity(fernetVar, messageVar):
	encrypted = fernetVar.encrypt(messageVar)
	try:
		decrypted = fernetVar.decrypt(encrypted)
		return (1, decrypted)
	except:
		return (-1, "")

fMessage = buildFernet("message")
fAuth = buildFernet("auth")

def checkNamePasswordMatch(nameVar, passwordVar):
	if nameVar in clientNames:
		index = clientNames.index(nameVar)
		validPassword = clientPasswords[index]

		if validPassword == passwordVar:
			return True
		else:
			return False

	else:
		return False

def markAsOnline(nameVar):
	# assumes name is in the list
	index = clientNames.index(nameVar)
	clientStatus[index] = True


def authenticateClient(clientVar):
	print "[EVENT]: Authenticate Client"
	credential = clientVar.recv(BUFFER_SIZE)	
	try:
		decrypted = fAuth.decrypt(credential)
		name, password = decrypted.split(" ")
		authFlag = checkNamePasswordMatch(name, password)
	
		if authFlag == True:
			answer = "Valid"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)
			markAsOnline(name)
			print "	[SUB]: Success"
			return True

		else:
			answer = "Not Valid"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)
			print "	[SUB]: Fail"
			return False

	except:
		print "Invalid Token"
		clientVar.send("Not Valid")
		return False

# get participant list
def getParticipantList():
	peopleInChat = []
	for i in range(len(clientStatus)):
		status = clientStatus[i]
		if status == True:
			onlineName = clientNames[i]
			peopleInChat.append(onlineName)
	return peopleInChat


def printChatStatus():
	global CHAT_ROOM_READY
	previousList = []

	time.sleep(1)
	print "[EVENT]: WAITING_FOR_CONNECTIONS"

	while 1:
		time.sleep(2)

		# get people that are active
		peopleInChat = getParticipantList()
		
		# if any changes have occurred, print the participant list
		if (peopleInChat == previousList):
			continue
		else:
			print "	People In the Room: ", peopleInChat
			previousList = deepcopy(peopleInChat)

		if len(peopleInChat) == chatCapacity:
			CHAT_ROOM_READY = True
			print "[EVENT]: CHAT_ROOM_READY"
			break

messageList = []

def newMessageArrived(messageVar):
	messageList.append(messageVar)

def listener(clientVar):
	global CHAT_ROOM_READY
	global CHAT_STARTED

	if CHAT_STARTED:
		print "	[SUB]: Chat already started"
		print " [SUB]: Rejected user, room full"
		return

	# set to True by printChatStatus() function
	while CHAT_ROOM_READY == False:
		message = clientVar.recv(BUFFER_SIZE)
		decryptedMessage = fAuth.decrypt(message)

		if decryptedMessage == "ROOM_STATUS":
			answer = "ROOM_NOT_READY"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)
		else:
			answer = "INTRUDER! ALARM! ALARM!"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)

	CHAT_STARTED = True
	# chat room ready
	message = clientVar.recv(BUFFER_SIZE)
	decryptedMessage = fAuth.decrypt(message)

	# notify user of the event "ROOM_READY"
	if decryptedMessage == "ROOM_STATUS":
		answer = "ROOM_READY"
		encryptedAnswer = fAuth.encrypt(answer)
		clientVar.send(encryptedAnswer)

	# retrieve messages nonstop
	while 1:
		message = clientVar.recv(BUFFER_SIZE)
		if message != "":
			newMessageArrived(message)


def broadcaster():
	global messageList
	while True:
		if messageList != []:
			message = messageList[0]
			# print message
			decryptedMessage = fAuth.decrypt(message)
			print "SERVER RECEIVED: ", decryptedMessage
			for client in currentClients:
				try:
					client.send(message)
				except:
					currentClients.remove(client)
			messageList = messageList[1:]

		

def acceptConnections():
	global CHAT_STARTED
	global chatCapacity

	SERVER.listen(chatCapacity)
	print "[EVENT]: SERVER @", ADDRESS
	while not CHAT_STARTED:
		client, clientAddress = SERVER.accept()
		clientPort = clientAddress[1]

		if clientPort not in KNOWNPORTS:
			# authentication procedure
			# print "First Time", clientAddress
			KNOWNPORTS.append(clientPort)
			authFlag = authenticateClient(client)
			if authFlag:
				currentClients.append(client)
				t = threading.Thread(target=listener, args=(client,));
				t.start()

		# if len(currentClients) == chatCapacity:
		# 	CHAT_STARTED = True

	time.sleep(1)
	print "[EVENT]: Room complete, reject rest of connections"
	while True:
		client, clientAddress = SERVER.accept()
		answer = "Room Full"
		encryptedAnswer = fAuth.encrypt(answer)
		client.send(encryptedAnswer)
		print "[EVENT]: Room Full, but somebody attempted to connect"
		client.close()
	while True:
		pass

def main():
	# chat room ready control
	thread.start_new_thread(printChatStatus, ())

	# thread that broadcasts messages to all the participants of the chat
	thread.start_new_thread(broadcaster, ())

	# accept client connections
	acceptConnections()

main()