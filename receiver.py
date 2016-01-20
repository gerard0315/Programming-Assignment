#!/usr/bin/env python

__author__ = 'yiran_tao'
import mytcp
import sys

#receiver<filename><listening_port><sender_IP><sender_port><log_filename>
if len(sys.argv) != 6:
    print 'Arguments Illegal'
    sys.exit()

listen_port=int(sys.argv[2])
sender_ip=sys.argv[3]
sender_port=int(sys.argv[4])
log_file=sys.argv[5]
filename=sys.argv[1]

recvlink = mytcp.MyTcpLink1('', sender_ip,listen_port , 0, 32125, sender_port, 20, log_file)

try:
    with open(filename, 'wb') as fout:
        while True:
            ret = recvlink.recv()
            if ret is None:
                break
            fout.write(ret)
            fout.flush()
    recvlink.close()
    sys.exit()
except KeyboardInterrupt as e:
    pass
