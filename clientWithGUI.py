from Tkinter import *
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
import time
import sys
import thread

SECRET_KEY_FOR_AUTH = "E-EKHr6Y9kCB4qUJQ-vAWf0d-qXMM9mGwhTjYVRLq6U="


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
CLIENT_SOCKET = socket(AF_INET, SOCK_STREAM)
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
    CLIENT_SOCKET.connect(ADDRESS)
    print "	Connection to", ADDRESS
    CURRENT_STATE = NOT_AUTHENTICATED


def getCredentialsFromCMD():
    if len(sys.argv) != 3:
        print "Usage:"
        print "	python client.py userName password"
        exit(-1)
    else:
        name = sys.argv[1]
        password = sys.argv[2]
        return name, password


def generatePassword():
    name, password = getCredentialsFromCMD()
    message = name + " " + password
    encryptedMessage = fAuth.encrypt(message)
    return encryptedMessage


def authenticateMyself():
    # server need to be in connection
    global CURRENT_STATE
    credential = generatePassword()
    print "	[SUB]: Sending credentials "
    CLIENT_SOCKET.sendall(credential)
    answer = CLIENT_SOCKET.recv(BUFFER_SIZE)
    decryptedAnswer = fAuth.decrypt(answer)
    # print decryptedAnswer
    if decryptedAnswer == "Valid":
        print "	[SUB]: Authenticated"
        CURRENT_STATE = ROOM_NOT_READY
    else:
        print "	[SUB]: Cannot authenticate"
        sys.exit(-1)


def waitForRoomReady():
    global CURRENT_STATE
    while 1:
        time.sleep(0.5)
        print("	[SUB]: Waiting for room to be complete")
        # send message
        message = "ROOM_STATUS"
        encryptedMessage = fAuth.encrypt(message)
        CLIENT_SOCKET.send(encryptedMessage)

        # receive result
        answer = CLIENT_SOCKET.recv(BUFFER_SIZE)
        try:
            decryptedAnswer = fAuth.decrypt(answer)
            if decryptedAnswer == "ROOM_READY":
                CURRENT_STATE = READY
                return
            else:
                # print "ROOM_NOT_READY"
                continue
        except:
            print "Failed waiting for room readiness"
            pass


def broadcastListener():
    message_list.insert(END, "Greetings from the Cave!")
    message_list.insert(END, "If you ever want to quit, type {quit} to exit.")
    message_list.insert(END, "-----------------------")
    while 1:
        try:
            answer = CLIENT_SOCKET.recv(BUFFER_SIZE)
            decryptedAnswer = fAuth.decrypt(answer)
            message_list.insert(END, decryptedAnswer)
        except OSError:  # Possibly client has left the chat.
            break


def messageSender(event=None):
    message = my_message.get()
    my_message.set("")
    encryptedMessage = fAuth.encrypt(message)
    CLIENT_SOCKET.send(encryptedMessage)
    if message == "{quit}":
        CLIENT_SOCKET.close()
        top.quit()


def on_closing(event=None):
    """This function is to be called when the window is closed."""
    my_message.set("{quit}")
    messageSender()


# Tkinter configurations.
top = Tk()
top.title("Cave - " + sys.argv[1])

messages_frame = Frame(top)
my_message = StringVar()  # For the messages to be sent.
my_message.set("Type your message here.")
scrollbar = Scrollbar(messages_frame)  # To navigate through past messages.

# Following will contain the messages.
message_list = Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
message_list.pack(side=LEFT, fill=BOTH)
message_list.pack()
messages_frame.pack()

entry_field = Entry(top, textvariable=my_message)
entry_field.bind("<Return>", messageSender)
entry_field.pack()
send_button = Button(top, text="Send", command=messageSender)
send_button.pack()

top.protocol("VM_DELETE_WINDOW", on_closing)


def main():
    getCredentialsFromCMD()

    printCurrentState()

    connectToServer()
    printCurrentState()

    authenticateMyself()
    printCurrentState()

    waitForRoomReady()
    printCurrentState()

    # receive_thread = Thread(target=broadcastListener)
    thread.start_new_thread(broadcastListener, ())
    # thread.start_new_thread(messageSender, ())
    mainloop()


main()
