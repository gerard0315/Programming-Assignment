#!/usr/bin/python2
import os
import sys
import time
import socket
import select
import string
import datetime
import math
import re
from thread import *
from threading import Timer

#get all username and password combinations
def get_login_info(filename):
	login_info = {}
	with open ("user_pass.txt") as file:
		for line in file:
			(usr, pwd) = line.split()
			login_info[usr] = pwd
			all_user.append(usr)
	return login_info

#send message to given socket
def server_send(client_socket, message):
	try:
		client_socket.send(message)
	except IOError:
		print 'socket close'
		_client_socket.close()

#receive message from socket
def server_receive(client_socket):
	try:
		print client_socket.recv(RECV_BUFFER)
	except IOError:
		print 'socket close.'
		_client_socket.close()

#logout a user
def logout(_client_socket, user_name):
	server_send(_client_socket, "Logging off.")
	logout_record[user_name] = datetime.datetime.now() #record the time one user logs out
	time.sleep(0.1)
	connections.remove(_client_socket) #remove relavent information
	usernames.remove(user_name)
	clients.pop(user_name, 0)
	_client_socket.close()
	print 'logged off'

#function for private message
def private_message(_user_name, user_name, _message):
	if _user_name in usernames: #if user is online
		(clients[_user_name][1]).send('\n"' + user_name + '": ' + str(_message))
		(clients[_user_name][1]).send('\nCommand: ')
	else:
		if _user_name in offline_message: #if user is offline
			offline_message[_user_name].append('\n"' + user_name + '":'+' ' + str(_message))
		else:
			offline_message[_user_name] = ['\n"' + user_name + '": ']
			offline_message[_user_name].append(str(_message) + ' ')

#function for listing other online users
def whoelse(server_socket, _client_socket, user_name):
	for i in range (0, len(usernames)):
		if usernames[i] == user_name:
			server_send(_client_socket, '\n')
		else:
			server_send(_client_socket, str(usernames[i]))
			if i < len(usernames):
				server_send(_client_socket, '\n')

#function for listing active user in a given time
def wholast(_client_socket, user_name, time):
	if float(time) <= 0 or float(time) > LAST_HOUR: #control time limits
		server_send(_client_socket, 'Please enter possitive number less then ' + str(LAST_HOUR) + '\n')
	else:
		for i in range (0, len(usernames)):
			server_send(_client_socket, str(usernames[i]))
			if i < len(usernames):
				server_send(_client_socket, '\n')
		for user_name in logout_record:
			if ((datetime.datetime.now() - logout_record[user_name]).total_seconds()) < 60 * float(time):
				if user_name not in usernames:#prevent double listing
					server_send(_client_socket, str(user_name) + '\n')

#function for broadcasting messages
def broadcast(server_socket, user_name, _message, _client_socket):
	for sock in connections:
		if sock != server_socket:
			try:
				if sock != _client_socket:
					sock.send('\n"' + user_name+ '" broadcasted: ' + _message + '\nCommand: ')
				else:
					sock.send('[Me]: ' + _message + '\n')
			except:
				sock.close()
				connections.remove(sock)

#run functions when entering commands
def input_commands(command_word, command, _client_socket, user_name):
	if command_word == 'broadcast message':
		_message = []
		_message = command.split(' ', 2)[2]
		if command.split(' ', 2)[1] != 'message':
			server_send(_client_socket, 'Invalid command!\n')
		else:
			broadcast(server_socket, user_name, _message, _client_socket)


	elif command_word == 'whoelse':
		whoelse(server_socket, _client_socket, user_name)


	elif command_word == 'logout':
		logout(_client_socket, user_name)


	elif command_word == 'wholast':
		time = command.split(' ')[1]
		wholast(_client_socket, user_name, time)


	elif command_word == 'message':
		if clients[user_name][4] == 0:
			_message = command.split(' ', 2)[2]
			_user_name = command.split(' ', 2)[1]
			if _user_name not in all_user: #if input wrong user name
				server_send(_client_socket, 'No such user.\n')
			else:
				private_message(_user_name, user_name, _message)
		else:
			print 'error'

	#send message to a list of users
	elif command_word == 'broadcast user':
		to_send = []
		_message_list= []
		_message = command.split()
		if clients[user_name][4] == 0:
			for i in range(2, len(_message)):#find users to send the message
				tag = 0
				for j in all_user:
					if _message[i] == j:
						tag = 1
						_message_list.append(_message[i])
						l = i
						break
				if tag == 0:
					to_send.append(_message[i])
			if to_send[0] != 'message':
				server_send(_client_socket, 'Invalid command or no such user. \n')
			else:
				del to_send[0]#find the correct message to send
				_to_send = " ".join(to_send)
				try:
					for m in range(0, l - 1):
						_user_name = _message_list[m]
						if _user_name in usernames:
							(clients[_user_name][1]).send('\n"' + user_name + '": ' + _to_send)
							(clients[_user_name][1]).send('\nCommand: ')
						else:
							if _user_name in offline_message:
								offline_message[_user_name].append('\n"' + user_name + '":'+' ' + _to_send)
							else:
								offline_message[_user_name] = ['\n"' + user_name + '": ']
								offline_message[_user_name].append(_to_send + ' ')

				except:
						print 'offline is', offline_message

#kicks a user offline when inactive for a specific time
def kick(_client_socket, user_name):
	server_send(_client_socket, '\nTimed out. Type to disconnect.\n')
	logout(_client_socket, user_name)

#new client connections
def client_thread(client_socket, addr):
	#start login or registration
	server_send(client_socket, '\nAre you a registered user? Enter "n" to regiser, press ENTER to log in.')
	choice = client_socket.recv(RECV_BUFFER)
	choice = choice.rstrip()
	#registration process
	if choice == 'n' or choice == 'N':
		login_info = get_login_info('user_pass.txt')
		server_send(client_socket, 'Choose a username: ')
		new_name = client_socket.recv(RECV_BUFFER)
		print new_name
		new_name = new_name.rstrip()

		var = 1
		while var == 1:
			if new_name in login_info:
				server_send(client_socket, 'This username has been taken, choose another:')#prevent using same names
				new_name = client_socket.recv(RECV_BUFFER)
				new_name = new_name.rstrip()
			else:
				var = 2
				server_send(client_socket, 'Set your password: ')
				new_pwd = client_socket.recv(RECV_BUFFER)
				new_pwd = new_pwd.rstrip()
				file = open ('user_pass.txt', 'a') #write new user name and password to file
				file.write('\n')
				a = '%s %s' %(new_name, new_pwd)
				file.write(a)
				file.close()
				server_send(client_socket, 'Registration finished, please login!')
				tag = 2
	else:
		server_send(client_socket, 'Please login') #Login if registered user
		pass

    #get username and password combinations
	login_info = get_login_info('user_pass.txt')

	server_send(client_socket, '\nUsername: ')
	user_name = ""
	user_name = client_socket.recv(RECV_BUFFER)
	user_name = user_name.rstrip()
	while user_name not in login_info.keys() or user_name in usernames:
		server_send(client_socket, 'Invalid username.')
		server_send(client_socket, '\nUsername: ')
		user_name = client_socket.recv(RECV_BUFFER)
		user_name = user_name.rstrip()

	# Appends the username to the active users directory.
	usernames.append(user_name)
	clients[user_name] = [0, client_socket, addr[1], addr[0], 0]

	#check if user has been blocked for too many wrong password tries
	if user_name in blocked_users.keys():
		if addr[0] == blocked_users[user_name][1]:
			_blocked_time = (datetime.datetime.now() - blocked_users[user_name][0]).total_seconds()
			if _blocked_time > BLOCK_TIME:
				pass
			else:
				server_send(client_socket, 'You are still blocked! Try again later!')
				logout(client_socket, user_name)

	try:
		#Password authentication
		_password = ""
		server_send(client_socket, 'Password: ')
		_password = client_socket.recv(RECV_BUFFER)
		_password = _password.rstrip()
		while login_info[user_name] != _password and clients[user_name][0] < 2:
			server_send(client_socket, 'Incorrect password. Attempts left: ' + str(2 - clients[user_name][0]))
			server_send(client_socket, '\nPassword: ')
			_password = client_socket.recv(RECV_BUFFER)
			_password = _password.rstrip()
			clients[user_name][0] += 1

		# Lock user if password entered incorectly 3 times
		if login_info[user_name] != _password:
			blocked_users[user_name] = [datetime.datetime.now(), addr[0]] #Log the time and ip address of user
			server_send(client_socket, 'No attempts left. You are now blocked for ' + str(BLOCK_TIME) + ' seconds.\n')
			logout(client_socket, user_name)

		server_send(client_socket, 'You have signed in!\n')

		# send offline messages.
		if user_name in offline_message.keys():
			server_send(client_socket, 'Other user has sent you offline messages:')
			for i in offline_message[user_name]:
				server_send(client_socket, i)
			del offline_message[user_name]
			server_send(client_socket, '\n')


		command = ""
		tag = True
		while tag:
			# Start timer to check if user times out before giving a command.
			t = Timer(TIME_OUT, kick, (client_socket,user_name,))
			t.start()
			server_send(client_socket, "Command: ")
			command = client_socket.recv(RECV_BUFFER)
			t.cancel()

			# If received message from user, cancel timer

			flag = 0
			while flag == 0:
				if command.strip() == '':
					print 'null'
					server_send(client_socket, 'null command')
					server_send(client_socket, '\nCommand: ')
					command = client_socket.recv(RECV_BUFFER)
				elif command != '':
					flag = 1
					command = command
					command = command.rstrip()
					raw_command = command.split()

					#recoganizing commands
					if raw_command[0] == 'logout':
						command_word = ['logout']
						tag = False
					elif raw_command[0] == 'wholast':
						command_word = ['wholast']
					elif raw_command[0] == 'whoelse':
						command_word = ['whoelse']
					elif raw_command[0] == 'broadcast' and raw_command[1] != 'user':
						command_word = ['broadcast message']
					elif raw_command[0] == 'message':
						command_word = ['message']
					elif raw_command[0] == 'broadcast' and raw_command[1] == 'user':
						command_word = ['broadcast user']

					else:
						server_send(client_socket, 'No such command!\n')
						server_send(client_socket, '\nCommand: ')
						flag = 0
						command = client_socket.recv(RECV_BUFFER)


			try:
				if any(s in command_word for s in COMMANDS):
					key = command_word[0]
					input_commands(key, command, client_socket, user_name)
				else:
					server_send(client_socket, 'Invalid command ! Please try again! \n')
			except:
				server_send(client_socket, 'Command error! \n')

	except:
		#user log off abnormally using ctrl+c
		print 'client socket already closed'
		logout_record[user_name] = datetime.datetime.now()
		client_socket.close()
		connections.remove(client_socket) #remove relavent information
		usernames.remove(user_name)
		#_client_socket.close
		print "A client " + str(addr) + " has logged off."
		server_socket.close()

#server initiaion
def initiate_server(server_socket):
	flag = True
	while flag:
			try:
				ready_read, ready_write, in_error = select.select(connections, [], [])
			except KeyboardInterrupt:
				flag = False
				print '\nUser used ctrl +c to exit' # gracefully logout

			except:
				time.sleep(0.1)

			for s in ready_read:
				if s == server_socket:
					#new connection
					client_socket, addr = server_socket.accept()
					print addr, 'is online now'
					server_send(client_socket, 'connected')
					connections.append(client_socket)
					start_new_thread(client_thread, (client_socket, addr))

	server_socket.close()


if __name__ == "__main__":
	if len(sys.argv) != 2 or not sys.argv[1].isdigit():
		print "This is a python chat room server"

	PORT = int(sys.argv[1])
	connections	= []
	COMMANDS = ["whoelse", "wholast", "broadcast message", "message", "broadcast user", "logout", "ctrlc"]
	usernames = []
	clients = {}
	logout_record = {}
	offline_message = {}
	blocked_users = {}
	all_user = []

	#initialize changable values
	BLOCK_TIME = 60
	TIME_OUT = 1800
	RECV_BUFFER = 1024
	LAST_HOUR = 60

	# Set up the initial socket object
	server_socket = socket.socket()
	host = socket.gethostbyname(socket.gethostname())
	server_socket.bind((host, PORT)) #bind
	print 'server initiated ' + host
	server_socket.listen(0)
	print 'Socket is listening ...'
	connections.append(server_socket)

	initiate_server(server_socket)
