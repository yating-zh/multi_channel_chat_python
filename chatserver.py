from socket import * # Import socket module
import socket
from _thread import * # allow thread
from datetime import datetime #get the server time
import pickle
import threading
import sys   #using sys.argv[1] get config file
from warnings import catch_warnings
import os


config_map = {}
channel_ports = []
channels = {}
waiting_queue = {}
size=5
queue=0

#use stop_event to stop a thread
stop_event = threading.Event()

def main():
    start_new_thread(listener,())
    stop_event.wait()
    # print('server shut down.')


def listener():
    # channel and port info, will get from external
    # load_config()

    # 0419 update: added bad configfile check
    if len(sys.argv) != 2:
        # print("no configfile,or more than one arguments")
        os._exit(1)
    configfile = sys.argv[1]
    load_config(configfile)


    # create main listener
    ServerSocket = socket.socket(AF_INET, SOCK_STREAM)
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # host = socket.gethostname() # Get local machine name
    host = "localhost"  # local host
    port = 9876  # server port number
    ServerSocket.bind((host, port)) #host is a string like 'google.com' or IP address "172.0.0.1", port is an integer.
    #print('Server waiting for client connection...')
    ServerSocket.listen(5)  # wait for a client connection

    # create channel listener
    for channel_name, config in config_map.items():
        start_new_thread(create_listener, (channel_name, "localhost", int(config[0]), int(config[1])))

    #also writing thread
    start_new_thread(write, (ServerSocket,))

    while True:
        ConnectionSocket, _ = ServerSocket.accept()  # accept new clients
        request_param = ConnectionSocket.recv(1024)  #from client: tuple(port number, username)
        decoded_param = pickle.loads(request_param) #pickle.loads() decode the tuple
        request_channel_port = decoded_param[0]

        # check if the port match one of three channel
        if request_channel_port not in channel_ports:
            ConnectionSocket.sendall(str.encode("Connect Failed. server main(): sorry, wrong channel port"))
        ConnectionSocket.sendall(str.encode("Connected."))


def load_config(configfile):
    try:
        with open(configfile, 'r') as lines:

            seen_channel_names = set()  #use to check channel duplicate channel names
            seen_channel_ports = set()   #use to check channel duplicate channel names
            # get each line
            for line in lines:
                strs = line.split(" ")

                if len(strs) != 4:
                    # print("config file format not match 4 segs per line ")
                    os._exit(1)
                #check channel name in configfile
                channel_name = strs[1]
                if channel_name in seen_channel_names:
                    os._exit(1)
                seen_channel_names.add(channel_name)
                #check port in configfile
                port = strs[2]
                if port in seen_channel_ports:
                    os._exit(1)
                seen_channel_ports.add(port)

                if port=="0":
                    # print("channel port cannot be 0 ")
                    os._exit(1)

                size = strs[3]
                size = 5   #0422: set to 5 for now
                config_map[channel_name] = (port, size)
                channels[channel_name] = []
                waiting_queue[channel_name] = []
                channel_ports.append(port)
            #check if config contains more than 2 cahnnels
            length = len(config_map)
            if length<=2:
                os._exit(1)

    except ValueError:
        # print("config error")
        os._exit(1)
    except FileNotFoundError:
        # print("config file not found")
        os._exit(1)
    except PermissionError:
        # print("config file not readable")
        os._exit(1)



def create_listener(channel_name, host, port, size):
    channel_socket = socket.socket(AF_INET, SOCK_STREAM)
    channel_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    channel_socket.bind((host, port))
    channel_socket.listen(size)  # wait for a client connection

    while True:
        # accept client connection
        conn_socket, _ = channel_socket.accept()  # accept new clients
        PortnName = conn_socket.recv(1024)  #from client: tuple(port number, username)
        decoded_PortnName = pickle.loads(PortnName) #pickle.loads() decode the tuple
        username=decoded_PortnName[1]
        # channelPort=decoded_PortnName[0]



        # channel length control
        channelLen = len(channels[channel_name])
        if channelLen >= size:
            # try queuing
            queue_user = [username, port, channel_name, conn_socket]
            waiting_queue[channel_name].append(queue_user)

            # start chatFun thread
            start_new_thread(queuing, (conn_socket, channel_name, username, port))
            continue


        # check if username duplicate
        connected_usernames = [user[0] for user in channels[channel_name]]
        if username in connected_usernames:
            conn_socket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Cannot connect to the {channel_name} channel."))
            conn_socket.sendall(str.encode("quit"))
            conn_socket.shutdown(socket.SHUT_RDWR)
            conn_socket.close()
            continue

        print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the {channel_name} channel.")  # 0422 moved to above
        conn_socket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Welcome to the {channel_name} channel, {username}.\n[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel."))  # to the current client #0422 removed"\n"
        # conn_socket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel."))

        #start chatFun thread
        start_new_thread(chatFun, (conn_socket, channel_name, username))



        # add client to channels
        user = [username, port, channel_name, conn_socket]
        channels[channel_name].append(user)

        # new client joined in send info to all but not new client itself
        for client in channels[channel_name]:  # iterate all the sockets and send message
            if client[3] != conn_socket:
                client[3].sendall(str.encode(
                    f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel.\n"))




def switch(conn_socket, username, channel_name,port):
    # # channel length control
    # channelLen = len(channels[channel_name])
    # if channelLen >= size:
    #     conn_socket.sendall(str.encode(f"sorry{username}, server busy"))

    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the {channel_name} channel.")  # 0422 moved to above
    conn_socket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Welcome to the {channel_name} channel, {username}.\n[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel."))  # to the current client #0422 removed"\n"
    # conn_socket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel."))

    # start chatFun thread
    start_new_thread(chatFun, (conn_socket, channel_name, username))

    # add client to channels
    user = [username, port, channel_name, conn_socket]
    channels[channel_name].append(user)

    # new client joined in send info to all but not new client itself
    for client in channels[channel_name]:  # iterate all the sockets and send message
        if client[3] != conn_socket:
            client[3].sendall(str.encode(
                f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel.\n"))



def queuing(ConnectionSocket,channelName,username, port):
    if ConnectionSocket.fileno() == -1:#ConnectionSocket.fileno() == -1 means socket closed
        stop_event.set()

    if waiting_queue != None:
        for index, client in enumerate(waiting_queue[channelName]):  # enumerate ->(index, element)
            if client[3] == ConnectionSocket:
                ConnectionSocket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Welcome to the {channelName} channel, {username}.\n[Server message ({datetime.now().strftime('%H:%M:%S')})] You are in the waiting queue and there are {index} user(s) ahead of you."))
    while True:
        try:
            message=ConnectionSocket.recv(1024).decode()
            # if client sent "/quit" or client quit the socket"
            if not message:
                break

            if message == "/quit":
                # close the current socket, tell server and other clients
                for item in waiting_queue[channelName]:
                    if username in item[0]:
                        print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has left the channel.")
                        if waiting_queue != None:
                            for index, client in enumerate(waiting_queue[channelName]):  # enumerate ->(index, element)
                                if client[3] != ConnectionSocket:
                                    client[3].sendall(str.encode(
                                        f"[Server message ({datetime.now().strftime('%H:%M:%S')})] You are in the waiting queue and there are {index-1} user(s) ahead of you."))
                        # remove client from queue
                        waiting_queue[channelName].remove(username)

                        stop_event.set()
                break


            channelLen = len(channels[channelName])
            if channelLen < size:

                # remove client from queue
                waiting_queue[channelName].remove(username)

                # start chatFun thread
                start_new_thread(chatFun, (ConnectionSocket, channelName, username))

                # add client to channels
                user = [username, port, channelName, ConnectionSocket]
                channels[channelName].append(user)

                # new client joined in send info to all but not new client itself
                for client in channels[channelName]:  # iterate all the sockets and send message
                    if client[3] != ConnectionSocket:
                        client[3].sendall(str.encode(
                            f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has joined the channel.\n"))
                return

            # message !=/quit
            if message:
                if waiting_queue != None:
                    for index, client in enumerate(waiting_queue[channelName]):  # enumerate ->(index, element)
                        if client[3] != ConnectionSocket:
                            client[3].sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] You are in the waiting queue and there are {index} user(s) ahead of you."))

        except:
            continue





def chatFun(ConnectionSocket,channelName,username): #using channels dictionary control message receive and sending
    if ConnectionSocket.fileno() == -1:#ConnectionSocket.fileno() == -1 means socket closed
        stop_event.set()

    while True:
        message=ConnectionSocket.recv(1024).decode()

        if not message:
            break

        #if client sent "/quit" or client quit the socket"
        if message=="/quit":

            # close the current socket, tell server and other clients
            for item in channels[channelName]:
                if username in item[0]:
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has left the channel.")
                    channels[channelName].remove(item)
                    for client in channels[channelName]:
                        client[3].sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has left the channel."))
            break

        if message=="/AFK":
            # close the current socket, tell server and other clients
            for item in channels[channelName]:
                if username in item[0]:
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} went AFK.")
                    channels[channelName].remove(item)
                    for client in channels[channelName]:
                        client[3].sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} went AFK."))
            break

         #list show channels details to client
        if message=="/list":
            status=[]
            for item in channels:
                staLine=f"[Channel] {item} {len(channels[item])}/{size}/{queue}"
                status.append(staLine)
            ConnectionSocket.sendall(str.encode(f"{status[0]}\n{status[1]}\n{status[2]}"))

        #whisper username message
        if message.startswith("/whisper"):
            cut = message.split() #using space split the string
            wisUser = cut[1]

            wisMessageSlice = cut[2:]

            wisMessage = ' '.join(wisMessageSlice) #0422 , convert string list to a single string

            #check if wisUser is in current channel
            flag = False
            for item in channels[channelName]:  #why this block always run
                if wisUser in item[0]:
                    flag=True

            if not flag:
                ConnectionSocket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {wisUser} is not here."))
                print(f"[{username} whispers to {wisUser}: ({datetime.now().strftime('%H:%M:%S')})] {wisMessage}")

            if flag:
                print(f"[{username} whispers to {wisUser}: ({datetime.now().strftime('%H:%M:%S')})] {wisMessage}")

                for item in channels[channelName]:
                    if item[0] == wisUser:
                        wisSocket = item[3]
                        wisSocket.sendall(str.encode(f"[{username} whispers to you: ({datetime.now().strftime('%H:%M:%S')})] {wisMessage}"))

        #switch
        if message.startswith("/switch"):
            cut_switch = message.split()
            switch_channel = cut_switch[1]
            #check if channel_name exist
            if switch_channel not in channels:
                ConnectionSocket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {switch_channel} does not exist."))
            else:
                username=username

                switch_port=int(config_map[switch_channel][0])

                # check if username duplicate
                connected_usernames = [user[0] for user in channels[switch_channel]]
                if username in connected_usernames:
                    ConnectionSocket.sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Cannot switch to the {switch_channel} channel."))
                    # switch_result = False
                else:
                    # remove the socket from the current channel, tell server and other clients
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has left the channel.")
                    for item in channels[channelName]:
                        if username in item[0]:
                            channels[channelName].remove(item)  # remove client from old channel
                            break
                    for client in channels[channelName]:
                        client[3].sendall(str.encode(
                            f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {username} has left the channel."))

                    start_new_thread(switch, (ConnectionSocket, username, switch_channel, switch_port))
                    return #break the main loop in chatFun





        #0421 server re-post message from one client to all the other clients in that channel; 0421 include the client itself
        if not(message.startswith("/")):

            # server repeat all the messages in server side
            print(f"[{username} ({datetime.now().strftime('%H:%M:%S')})] {message}")

            for client in channels[channelName]: # iterate all the sockets and send message
                    client[3].sendall(str.encode(f"[{username} ({datetime.now().strftime('%H:%M:%S')})] {message}"))
    ConnectionSocket.close()


def write(ConnectionSocket):
    if ConnectionSocket.fileno() == -1:#ChannelClientSocket.fileno() == -1 means socket closed
        stop_event.set()
    #main loop
    while True:
        try:
            Input = input("")  # ask user to enter their message

            # shotdown
            if Input == "/shutdown":
                for _, channel in channels.items():
                    for client in channel:
                        client[3].shutdown(socket.SHUT_RDWR)

                stop_event.set()
                return
            # kick
            elif Input.startswith("/kick"):
                try:
                    info = Input.split(" ")[1].split(":")
                    channel_name = info[0]
                    user_name = info[1]

                except Exception as e:
                    print("wrong input.")
                    continue

                # check if channel_name exists
                channel = channels.get(channel_name)
                if not channel:
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {channel_name} does not exist.")
                    continue
                # check if user_name exists
                channel_user_names_map = {}
                for i, item in enumerate(channel):
                    channel_user_names_map[item[0]] = i
                i = channel_user_names_map.get(user_name)
                if i is not None:
                    # kick it
                    channel[i][3].shutdown(socket.SHUT_RDWR)
                    del channel[i]
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] Kicked {user_name}.")
                    # notifying others
                    for item in channel:
                        item[3].sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {user_name} has left the channel."))
                else:
                    # user_name not found
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {user_name} is not in {channel_name}.")

            # empty
            elif Input.startswith("/empty"):
                channel_name = ""
                try:
                    # parse channel_name
                    channel_name = Input.split(" ")[1]
                except Exception as e:
                    print('wrong input.')
                    continue
                # check if channel_name exists
                channel = channels.get(channel_name)
                if not channel:
                    print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {channel_name} does not exist.")
                    continue
                # close all the client
                for client in channel:
                    client[3].shutdown(socket.SHUT_RDWR)
                channel.clear()
                print(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {channel_name} has been emptied.")
            else:
                #server send messages to all clients
                for channel, items in channels.items():
                    for item in items:
                        if Input !=None:
                            item[3].sendall(str.encode(f"[Server message ({datetime.now().strftime('%H:%M:%S')})] {Input}"))

        except EOFError:  #eoferror added 0419
            Input = None

if __name__ == '__main__': # a statement of python, the main() can be run in terminal or import by other scripts
    main()


