-------------------------------------------------------------
This is a chat server and client written in Python 2.7.3

Completed By Yiran Tao

10/07/2015
-------------------------------------------------------------

a) This project consists of:

    server.py
    client.py
    user_pass.txt

server.py is the chat server program, invoked with:

    python server.py <port>

Running the code will create a server and listen for clients. All changable variable
LAST_HOUR, TIME_OUT, BLOCK_TIME are already listed in the main function.

client.py is the chat client program, invoked with:

    python Client.py <ip-address> <port>

Running the code will connect to the server specified in the argument. Multiple instances
of the client program (with each instance supporting one client) are supported.

user_pass.txt is a text file that contains all valid combinations of usernames and passwords.
This file must be in the same directory as the server.

Possible commands runnable by a client after connection:

 1. whoelse                   						  	- displays names of other connected users
 2. wholast                								- displays names of only those users that connected within a specific time 
 3. broadcast <message>       							- broadcasts <message> to all connected users
 4. broadcast user <user><user><user> message <message>	- broadcasts listed user <message> 
 5. message <user> <message>  							- sends <message> privately to <user> 
 6. logout                    							- log out this user 
b) Additional functions
The chat program supports registration of a new user upon connected to the server. 
New user will have a chance to create a unique username and password combination to enter the chat room

The chat server supports send offline message sent with command 4 and 5 as these messages are considered more important then the broadcasted ones.

b) Development environment

This code was written in MAC OS 10.11, with Python 2.7.3, and function normally in Python 2.7.1.
The code will NOT work in Windows due to conflicting issues regarding Python's select.select() function. 
The compile method was specified in section a).

c)Sample output

SERVER:
python server.py 4119
server initiated 192.168.0.2
Socket is listening ...

Client 1:
python client.py 192.168.0.2 4119
Connection Succeeded.
connected
Are you a registered user? Enter "n" to regiser, press ENTER to log in.n
Choose a username: gerard
Set your password: gerard
Registration finished!
Username: gerard
Incorrect password. Attempts left: 2
Password: gerard
You have signed in!
Command: wholast 30
gerard




Client 2:
python client.py 192.168.0.2 4119
Connection Succeeded.
connected
Are you a registered user? Enter "n" to regiser, press ENTER to log in.
Please login
Username: columbia
Password: 116bway
You have signed in!
Command: whoelse   
gerard

Command: broadcast message hello gerard
[Me]: hello gerard
Command: message gerard hello
Command: message network there's a new guy
Command: broadcast message hi
[Me]: hi
Command: broadcast user gerard network message catch you later!
Command: logout
Logging off.
You have disconnected




on Client1:                 
"columbia": hello gerard
Command: 
"columbia" broadcasted: hi
Command: 
"columbia": catch you later!




Client 3 after 2 min:
python client.py 192.168.0.2 4119
Connection Succeeded.
connected
Are you a registered user? Enter "n" to regiser, press ENTER to log in.
Please login
Username: network
Password: seemsez
You have signed in!
Other user has sent you offline messages:
"columbia": there's a new guy 
"columbia": catch you later!
Command: whoelse
gerard

Command: wholast 1
gerard
network
 

