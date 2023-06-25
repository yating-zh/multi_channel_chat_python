
# Multi-channel Chat Application

A multi-channel chat application using socket programming in Python 3. 

## Abstract

    There are two programs: chatserver.py and chatclient.py (A chat client and a chat server.)
    The functionalities include: 
    
    1. Three chat channels, each channel contain five simultaneous connections.
    2. Clients will be held in waiting queue until the channel is available.
    3. AFK 100s, client will be removed after timing out
    4. Client commands: /whisper, /quit, list, /switch
    5. Server commands: /kick, /empty, /shutdown


## Functions and descriptions
	
	1. Functions in chatserver.py
	
	# main() - the main function, create listener() thread
	# listener() - The main listener listen "localhost"/"9876"; Read the configfile and create create_listener() threads for each channel; Start the server's write() thread.
	# load_config() - Load the configfile and "try/except" config errors
	# create_listener() - Channel listener. If the capacity available and username unique, add the client to "channels{}" and start the chatFun() function thread. If it over the capacity, add the client to "waiting_queue" and start the queuing() thread.
	# chatFun() - the chat function mainly deal with messages and commands from clients, like:"/quit","/list","/whisper","/switch","AFK", and other common messages. "/switch" only remove client from current channel, and using switch() to add the client to new channel. 
	# switch() - add the client to new channel by operating the "channels{}"
	# queuing() - deal with the clients that over channel's capacity. Keep checking the length of channel which the client is waiting for, and send messages. When there is an available place, remove the first index client from waiting_queue, add to channels{} and start chatFun() thread for the client.
	# write() - deal with the server side messages and commends, include"/kick", "/shutdown", "/empty", and common messages from server to clients.
    

	2. Functions in chatclient.py
	
	# main() - connect the main listener with "localhost"/"9876", and connect the channel listener with channel port number. Start the receive() and write() threads.
	# receive() - keep receiving messages from server, and deal with the server's commands, and print the messages to stdout.
	# write() - client's write() function which send client's messages to server. Record the AFK start_time using time.monotonic() and start the timer() thread. 
	# timer() - countdown 100s of "Away from keyboard", send the "/AFK" command when countdown is over.


## Test

	1. Test with test suite
	# Most functionalities can pass the test correctly.
	# Some may need to run multiple times (about 80%-90% pass), for example "channels.sh", etc

	2. Test manually
	# Run chatserver: python3 chatserver.py configfile (Test on Moss: port numbers in configfile are 9001-9002-9003, need to modify port number if in use on Moss)
	# Run chatclient: python3 chatclient.py 9001 Mary.
	# Client send a message. Server receives the message. The clients in the same channel receive the message ,the clients in different channels can't receive the message.
	# /Whisper + Mary + message: Only Mary receives the message. If "Mary" doesn't exist, server will reply "Mary is not here"
	# /list: Client will receive the current status of each channel. Add/Remove clients, the status will always reflect the current status of each channel.
	# /quit: Client quit the chat channel, server and other clients receive "Mary has left the channel."
	# /switch + channel_name: the client will quit the current channel, and join the new channel. 
	# /kick + channel_name:client_name: the client will be kicked out by server.
	# /empty + channel_name: all clients in that channel will be removed
	# /shutdown: the server shutdown, all clients in all the channels will be removed
	# AFK: client send the last message meanwhile start a stopwatch. The client will be removed after 100s.
	# Miscellaneous: All the messages contain the current server time. Check all the printed messages on stdout match the requirements


## 
    This can be said to be my first Python program. 
 
