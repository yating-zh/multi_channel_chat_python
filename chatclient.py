from socket import * # Import socket module
import pickle #use dumps()to encode and loads() to decode
import sys
from _thread import * # allow thread
import threading
import time  #to use time.sleep() to pause the while loop
import os

stop_event = threading.Event()

#receive
def receive(ChannelClientSocket):
    if ChannelClientSocket.fileno() == -1: #ChannelClientSocket.fileno() == -1 means socket closed
        stop_event.set()
    while True:
        Response = ChannelClientSocket.recv(1024).decode()
        if not Response:
            stop_event.set()
            break
        if (Response == 'quit') or (Response == '/shutdown'):
            stop_event.set()
            break
        Response = Response.strip()
        if Response and not Response.isspace(): #0423 added  #strip() method remove leading and trailing"\n" and whitespace
            print(f"{Response}")



#Input write
def write(ChannelClientSocket):
    if ChannelClientSocket.fileno() == -1:
        stop_event.set()
    while True:
        try:
            Input = input("")  # ask user to enter their message
            if Input!= None:  #0421: added only if Input!= none , send to server
                ChannelClientSocket.sendall(str.encode(Input))  # send message to socket
                start_time=time.monotonic() #time.monotonic() returns the number of seconds has passed
                start_new_thread(timer, (start_time,ChannelClientSocket))
            if Input == "/quit":
                # ChannelClientSocket.close()
                stop_event.set()  # set the flag to stop the loop
                #break
        except EOFError:  #eoferror added 0419
            Input = None

def timer(start_time,ChannelClientSocket):
    while True:
        countdown=time.monotonic()-start_time    #time.monotonic() returns the number of seconds has passed
        if countdown > 100:
            ChannelClientSocket.sendall(str.encode("/AFK"))
            stop_event.set()  # set the flag to stop the loop
        time.sleep(1)


#use two thread to implement receiving and writing.
def main():
    ClientSocket = socket(AF_INET, SOCK_STREAM)


    host = "localhost"  # server IP
    port = 9876  # server port

    try:
        if len(sys.argv) != 3:  # check if there are two arguments
            os._exit(1)
        if sys.argv[1]==None:  #0422 add exit()
            os._exit(1)
        channel_port = sys.argv[1]   #moss
        if sys.argv[2]==None: #0422 add exit()
            os._exit(1)
        username=sys.argv[2]   #moss
    except ValueError:
        # print("config error")
        os._exit(1)


    PortnName=(channel_port,username)
    encode_PortnName=pickle.dumps(PortnName) #pickle.dumps() encode the tuple

    #sllow reuse socket
    ClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    #connect the server with the matched host and port
    ClientSocket.connect((host, port))
    #send channel Port and username tuple to server
    ClientSocket.sendall(encode_PortnName)
    resp = ClientSocket.recv(1024).decode()
    if resp.startswith("Connect Failed."):
        return
    # ClientSocket.shutdown
    ClientSocket.close()

    #connect the channel server with the channel port
    ChannelClientSocket = socket(AF_INET, SOCK_STREAM)
    #sllow reuse socket
    ChannelClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    ChannelClientSocket.connect((host, int(channel_port)))
    ChannelClientSocket.sendall(encode_PortnName)

    #use stop_event to quit a thread
    start_new_thread(receive,(ChannelClientSocket,))
    start_new_thread(write,(ChannelClientSocket,))
    
    stop_event.wait()

if __name__ == '__main__': # a statement of python, the main() can be run in terminal or import by other scripts
    main()

