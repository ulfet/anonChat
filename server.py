from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from cryptography.fernet import Fernet
import base64
import os
from cryptography.exceptions import InvalidSignature
import random
import thread
import threading
import time

chatCapacity = 2
clientNames = ["ulfet", "ozgur", "jennifer", "mary", "hamza"]
clientPasswords = ["ulfetp", "ozgurp", "jenniferp", "marryp", "hamzap"]
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

# returns Fernet
def buildFernet(messageOrAuth):
	key = generateFernetKey(messageOrAuth)
	f = Fernet(key)
	return f


def generateRandomPeopleList(numberOfPeopleVar, nDigits):
	rangeStart = 10**(nDigits-1)
	rangeEnd = (10**nDigits) -1
	randomList = random.sample( range(rangeStart, rangeEnd), numberOfPeopleVar)
	return randomList

# check
def checkMessageValidity(fernetVar, messageVar):
	encrypted = fernetVar.encrypt(messageVar)
	try:
		decrypted = fernetVar.decrypt(encrypted)
		return (1, decrypted)
	except:
		return (-1, "")

fMessage = buildFernet("message")
checkMessageValidity(fMessage, "Hello")

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
	credential = clientVar.recv(BUFFER_SIZE)	
	try:
		decrypted = fAuth.decrypt(credential)
		name, password = decrypted.split(" ")
		authFlag = checkNamePasswordMatch(name, password)
	
		if authFlag == True:
			# print "Valid"
			answer = "Valid"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)
			markAsOnline(name)

		else:
			# print "Not Valid"
			answer = "Not Valid"
			encryptedAnswer = fAuth.encrypt(answer)
			clientVar.send(encryptedAnswer)

	except:
		print "Invalid Token"
		clientVar.send("Not Valid")



def printChatStatus():
	global CHAT_ROOM_READY
	while 1:
		time.sleep(2)
		peopleInChat = []
		for i in range(len(clientStatus)):
			status = clientStatus[i]
			if status == True:
				onlineName = clientNames[i]
				peopleInChat.append(onlineName)
		print "People In the Room: ", peopleInChat

		if len(peopleInChat) == chatCapacity:
			CHAT_ROOM_READY = True
			break

messageList = []

def newMessageArrived(messageVar):
	messageList.append(messageVar)

def listener(clientVar):
	global CHAT_ROOM_READY

	while CHAT_ROOM_READY == False:
		message = clientVar.recv(BUFFER_SIZE)
		decryptedMessage = fAuth.decrypt(message)
		# print decryptedMessage

		if decryptedMessage == "ROOM_STATUS":
			answer = "ROOM_NOT_READY"
			encryptedAnswer = fAuth.encrypt(answer)
			# print encryptedAnswer
			clientVar.send(encryptedAnswer)
		else:
			answer = "FUCK YOU!"
			encryptedAnswer = fAuth.encrypt(answer)
			# print encryptedAnswer
			clientVar.send(encryptedAnswer)

	# chat room ready
	message = clientVar.recv(BUFFER_SIZE)
	decryptedMessage = fAuth.decrypt(message)
	# print decryptedMessage

	if decryptedMessage == "ROOM_STATUS":
		answer = "ROOM_READY"
		encryptedAnswer = fAuth.encrypt(answer)
		# print encryptedAnswer
		clientVar.send(encryptedAnswer)

	while 1:
		message = clientVar.recv(BUFFER_SIZE)
		if message != "":
			newMessageArrived(message)

clients = []
def broadcaster():
	global messageList
	while 1:
		if messageList != []:
			message = messageList[0]
			# print message
			decryptedMessage = fAuth.decrypt(message)
			print "SERVER RECEIVED: ", decryptedMessage
			for client in clients:
				client.send(message)
			messageList = messageList[1:]

		

def acceptConnections():
	SERVER.listen(chatCapacity)
	print "Server listening at", ADDRESS, "\n"
	while True:
		client, clientAddress = SERVER.accept()
		print clientAddress, "connected"

		clientPort = clientAddress[1]
		if clientPort not in KNOWNPORTS:
			# authentication procedure
			print "First Time", clientAddress
			KNOWNPORTS.append(clientPort)
			authenticateClient(client)
			clients.append(client)
			t = threading.Thread(target=listener, args=(client,));
			t.start()

		# while 1:
		# 	print client.recv(BUFFER_SIZE)

def main():
	# chat room ready control
	thread.start_new_thread(printChatStatus, ())
	thread.start_new_thread(broadcaster, ())
	# randomList = generateRandomPeopleList(chatCapacity, 5)
	# print randomList
	acceptConnections()

main()