This is a Simple TCP-like transport layer protocol written in Python 2.7.3.

Written by Yiran Tao
Nov,11 2015


The assignment includes three parts:

    sender.py
    receiver.py
    mytcp.py
    sender_file.txt

(a) Requirement of this coursework:
    This assignment require to implement a simplified TCP-­like transport layer protocol. The protocol should provide reliable, in order delivery of a stream of bytes. It should recover from in­-network packet loss, packet corruption, packet duplication and packet reordering and should be able cope with dynamic network delays. Data is exchanged via a link emulator to provide a unreliable transmission. The acknowledgements should be directly sent from receiver to the sender without loss. Variable window size should also be supported


(b) Instructions:
1. sender.py is a data-sending-ack-receiving program. It can be invoked in the following manner:

   python sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size> 

   the programs uses the sending function in mytcp.py and send data to receiver side

2. receiver.py is a receiving data while sending ack response program. It can be invoked as below in the terminal:

   python receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>

   the programs uses the receiving function in mytcp.py and send data to receiver side


(c) Program descriptions:
1. Tcp segments structure:
   ————————————————————————————
   |  checksum  |   length    |
   ————————————————————————————
   |   seq num  |   acknum    |
   ————————————————————————————
   |    window  |     flag    |
   ————————————————————————————
   |        data              |
   |                          |
   |                          |
   ———————————————————————————-

   The total length of the header is 12 bytes.

2. Functions and realizations:
  mytcp.py consists all the functions used in sending and receiving. The program starts in two threads for sending and receiving.
  The class MyTcpLinkSending describs the sending class while MyTcpLinkRecving describs the the receiving class. MyTcpLinkSending
  is used to send data packet and MyTcpLinkRecving is used to receive packet and ACK and return ACK when data arrives at the receiving 
  end. Received ACK will be transfered to the sending object and enter loop to examine this ACK, it then clear the timer for a packet
  when confirmed. The packet will then be removed from the sending queue. The sender and receiving will send a FIN to perform handshake 
  to stop transmitting file. The program will at the same time write logfile at both ends.
  sliding window is realized by send packets of one window size, apply timers to each packet and wait until all packets are acknowledged
  while resend all unacknowledged packets. When all packtets are confirmed, start to transmit next window.
  At the end of transmission, total number of transmitted packets and resent packets are displayed in Terminal.

(d) Output Sample:
newudpl-1.4 darthvader$ ./newudpl -vv -i 192.168.0.8:* -o 192.168.0.8:4119 -d1.7 -B1000 -L20 -O40 

Network Emulator With UDP Link
 Copyright (c) 2001 by Columbia University; all rights reserved

Link established:
  192.168.0.8/***** ->
          Death-Star-VerAir.local(192.168.0.8)/41192
  /41193 ->
          192.168.0.8/4119

emulating speed  : 1000(kb/s)
delay            : 1.700000(sec)
ether net        : 10M(b/s)
queue buffer size: 8192(bytes)


error rate
    random packet loss: 20(1/100 per packet)
    bit error         : 1000(1/100000 per bit)
    out of order      : 40(1/100 per packet)


2. receiver
python receiver.py receiver_file.txt 411992.168.0.8 4118 receive_log.txt
i got fin
sending exit fin_wait
sending thread exit
recv thread exit

note that the receiver program must quit mannualy

3. sender:
python sender.py sender_file.txt 192.168.0.8 41192 4118 sender_log.txt 5
sending exit fin_wait
sending thread exit
transmission result                 : Success
The number of packets sent          : 159
The number of packets retransmitted : 256


4. Sample receive_log.txt
Time   . source host/sport . remote host/dport . seq# . ack# [. RTT] 
1447351421 . /4119 . 192.168.0.8/41193 . 0# . 0#
1447351421 . /4119 . 192.168.0.8/41193 . 1# . 0#
1447351423 . /4119 . 192.168.0.8/41193 . 2# . 0#
1447351423 . /4119 . 192.168.0.8/41193 . 4# . 0#
1447351425 . /4119 . 192.168.0.8/41193 . 3# . 0#
1447351426 . /4119 . 192.168.0.8/41193 . 8# . 0#
1447351428 . /4119 . 192.168.0.8/41193 . 5# . 0#
1447351428 . /4119 . 192.168.0.8/41193 . 7# . 0#
1447351430 . /4119 . 192.168.0.8/41193 . 6# . 0#
1447351432 . /4119 . 192.168.0.8/41193 . 9# . 0#
1447351434 . /4119 . 192.168.0.8/41193 . 14# . 0#
1447351434 . /4119 . 192.168.0.8/41193 . 13# . 0#
1447351436 . /4119 . 192.168.0.8/41193 . 11# . 0#

5. sender_log.txt
Time   . source host/sport . remote host/dport . seq# . ack# [. RTT] 
1447351421 . /32123 . 192.168.0.8/41192 . 0# . 0# . 2.267671
1447351421 . /32123 . 192.168.0.8/41192 . 1# . 0# . 2.267677
1447351423 . /32123 . 192.168.0.8/41192 . 2# . 0# . 4.271297
1447351423 . /32123 . 192.168.0.8/41192 . 4# . 0# . 4.271311
1447351425 . /32123 . 192.168.0.8/41192 . 3# . 0# . 6.271987
1447351426 . /32123 . 192.168.0.8/41192 . 8# . 0# . 1.982133
1447351428 . /32123 . 192.168.0.8/41192 . 5# . 0# . 3.978274
1447351428 . /32123 . 192.168.0.8/41192 . 7# . 0# . 3.980742
1447351430 . /32123 . 192.168.0.8/41192 . 6# . 0# . 5.981406
1447351432 . /32123 . 192.168.0.8/41192 . 9# . 0# . 7.985243
1447351434 . /32123 . 192.168.0.8/41192 . 14# . 0# . 2.693668
1447351434 . /32123 . 192.168.0.8/41192 . 13# . 0# . 2.695145
1447351436 . /32123 . 192.168.0.8/41192 . 11# . 0# . 4.695365
1447351440 . /32123 . 192.168.0.8/41192 . 10# . 0# . 8.693791


note that in both logfiles time are represented in the form of timestamp and all RTTs are only stored in sender side logfile.