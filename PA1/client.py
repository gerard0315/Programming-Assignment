#!/usr/bin/python2
import os
import socket
import sys
import select
import string

if __name__ == "__main__":
	if len(sys.argv) != 3 or not sys.argv[2].isdigit():
		print("Usage: client.py <server_IP_address> <port>")

	# Connects to the server socket.
	connect_socket = socket.socket()
	PORT = int(sys.argv[2])
	HOST = sys.argv[1]
	connect_socket.connect((HOST, PORT))

	print 'Connection Succeeded.'

	while True:
		try:
			socket_list = [sys.stdin, connect_socket]
			ready_read, ready_write, in_error = select.select(socket_list, [], [])

			for s in ready_read:
				if s == connect_socket: #inbox data given from server
					data = s.recv(1024)
					if not data:
						print '\nYou have disconnected'
						sys.exit()
					else:
						sys.stdout.write(data)
						sys.stdout.flush()

				else:#inbox data from client
					data = sys.stdin.readline()
					connect_socket.send(data)
					sys.stdout.flush()
		except KeyboardInterrupt:
			time.sleep(1)
			print '\nUser used ctrl+c to exit'
			sys.exit()
