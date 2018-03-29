from socket import AF_INET, socket, SOCK_STREAM
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
import time
import sys
import thread

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

HOST = ""
PORT = 1789
BUFFER_SIZE = 1024
ADDRESS = (HOST, PORT)
SERVER = socket(AF_INET, SOCK_STREAM)
fAuth = buildFernet("auth")

CURRENT_STATE = 0
NOT_CONNECTED = 0
NOT_AUTHENTICATED = 1
ROOM_NOT_READY = 2
READY = 3

def printCurrentState():
	if CURRENT_STATE == NOT_CONNECTED:
		print "[STATE]: NOT_CONNECTED"

	if CURRENT_STATE == NOT_AUTHENTICATED:
		print "[STATE]: NOT_AUTHENTICATED"

	if CURRENT_STATE == READY:
		print "[STATE]: READY"

	if CURRENT_STATE == ROOM_NOT_READY:
		print "[STATE]: ROOM_NOT_READY"


def connectToServer():
	global CURRENT_STATE
	SERVER.connect(ADDRESS)
	print "Connection to", ADDRESS
	CURRENT_STATE = NOT_AUTHENTICATED

def generatePassword():
	name = "ulfet"
	password = "ulfetp"
	message = name + " " + password
	encryptedMessage = fAuth.encrypt(message)
	return encryptedMessage

def authenticateMyself():
	# server need to be in connection
	global CURRENT_STATE
	credential = generatePassword()
	print "Sending: ", credential
	SERVER.sendall(credential)
	answer = SERVER.recv(BUFFER_SIZE)
	decryptedAnswer = fAuth.decrypt(answer)
	print decryptedAnswer
	if decryptedAnswer == "Valid":
		CURRENT_STATE = ROOM_NOT_READY
	else:
		print "Cannot authenticate"
		sys.exit(-1)

def waitForRoomReady():
	global CURRENT_STATE
	while 1:
		time.sleep(5)
		# send message
		message = "ROOM_STATUS"
		encryptedMessage = fAuth.encrypt(message)
		SERVER.send(encryptedMessage)

		# receive result
		answer = SERVER.recv(BUFFER_SIZE)
		try:
			decryptedAnswer = fAuth.decrypt(answer)
			if decryptedAnswer == "ROOM_READY":
				CURRENT_STATE = READY
				return
			else:
				print "ROOM_NOT_READY"

		except:
			print "Failed waiting for room readiness"
			pass



def broadcastListener():
	while 1:
		answer = SERVER.recv(BUFFER_SIZE)
		decryptedAnswer = fAuth.decrypt(answer)
		print "\n",decryptedAnswer

def messageSender():
	while 1:
		message = raw_input("SEND: ")
		encryptedMessage = fAuth.encrypt(message)
		SERVER.send(encryptedMessage)


def main():
	printCurrentState()

	connectToServer()
	printCurrentState()

	authenticateMyself()
	printCurrentState()

	waitForRoomReady()
	printCurrentState()

	thread.start_new_thread(broadcastListener, ())
	thread.start_new_thread(messageSender, ())
	while 1:
		pass

		





main()
