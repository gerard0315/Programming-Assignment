#!/usr/bin/env python
__author__ = 'yiran_tao'
import mytcp
import time
import sys

#sender<filename><remote_IP><remote_port><ack_port_num><log_filename><window_size>

filename = sys.argv[1]
remote_ip = sys.argv[2]
remote_port = int(sys.argv[3])
ack_port_num = int(sys.argv[4])
log_file = sys.argv[5]
win_size = int(sys.argv[6])

MAXSEGMENTSIZE = 400

mytcplink = mytcp.MyTcpLink1('', remote_ip, 32123,remote_port, ack_port_num, 0, win_size, log_file)

with open(filename, 'rb') as fin:
    while 1:
        data = fin.read(MAXSEGMENTSIZE)
        if len(data) == 0:
            break
        while mytcplink.send(data) is False:
            time.sleep(0.2)

mytcplink.close()

try:
    while mytcplink.state != mytcp.MyTcpLink1.STATE_FIN_WAIT2:
        time.sleep(1)

    mytcplink.logger.log_trans_info()

except KeyboardInterrupt as e:
    pass


sys.exit(0)
