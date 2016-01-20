__author__ = 'yiran_tao'
import os
import sys
import socket
import struct
import time
from select import select
from time import sleep
from threading import Lock
from threading import Thread

"""calculate checksum"""
def calc_checksum(s):
    chksum = 0
    for i in range(len(s)):
        if i % 2 == 0:
            chksum = chksum + (ord(s[i]) << 8)
        elif i % 2 == 1:
            chksum = chksum + ord(s[i])
    return  (65535 - (chksum % 65535))


"""write log message"""
class Logger():
    def __init__(self, link, filename):
        self.link = link
        self.filename = filename
        if os.access(filename, os.R_OK) is True:
            os.remove(filename)
        src = self.link.src
        if src == '':
            src = 'localhost'
        header = 'Time   . source host/sport . remote host/dport . seq# . ack# [. RTT] \n'
        if self.filename == 'stdout':
            print header
        else:
            with open(self.filename,'a+') as fout:
                fout.write(header)

    """write receiving log"""
    def receive_log(self, packet):
        fmt = '%d . %s/%d . %s/%d . %d# . %d#'
        
        src = self.link.src
        if src == '':
            src = 'localhost'
        
        if self.filename == 'stdout':
            print fmt % (time.time(), src, self.link.src_port,
                         self.link.dst, self.link.dst_port, packet.seq_num,
                         packet.ack_num)
        else:
            try:
                with open(self.filename, 'a+') as fout:
                    fout.write(fmt % (time.time(), self.link.src, self.link.src_port,
                                      self.link.dst, self.link.dst_port, packet.seq_num,
                                      packet.ack_num))
                    fout.write('\n')
            except IOError as e:
                print 'Unable to Log : %s' % e

    def log_trans_info(self):
        print 'transmission result                 : %s' % self.link.trans_result
        print 'The number of packets sent          : %d' % self.link.sent_count
        print 'The number of packets retransmitted : %d' % self.link.retrans_count

    def send_log(self, packet):
        fmt = '%d . %s/%d . %s/%d . %d# . %d# . %lfms'
        
        src = self.link.src
        if src == '':
            src = 'localhost'
        
        if self.filename == 'stdout':
            print fmt % (time.time(), src, self.link.src_port,
                         self.link.dst, self.link.dst_port, packet.seq_num,
                         packet.ack_num, packet.timer.passed*1000)
        else:
            try:
                with open(self.filename, 'a+') as fout:
                    fout.write(fmt % (time.time(), self.link.src, self.link.src_port,
                               self.link.dst, self.link.dst_port, packet.seq_num,
                               packet.ack_num, packet.timer.passed))
                    fout.write('\n')
            except IOError as e:
                print 'Unable to Log : %s' % e


"""send packet class"""
class MyTcpLinkSending():
    def __init__(self, mytcplink):
        self.mytcplink = mytcplink
        self.win_start = 0
        self.win_slide = 0
        self.win_size = mytcplink.win_size

        self.packet_list = MyTcpPacketSafeQueue('sending')
        self.ack_list = MyTcpPacketSafeQueue('recvack')

        self.sock = self.mytcplink.sock
        self._thread = Thread(target=MyTcpLinkSending.run, args=[self])
        self._thread.setDaemon(True)
        self._thread.start()
    
    """when user call the close function , a fin segment will be put into packet list
       when  we get this segment, we will enter fin_wait state"""
    def enter_fin_wait(self):
        """ ack all received packet"""
        while self.ack_list.count() > 0 or self.packet_list.count() > 0:
            sleep(0.001)
            self.ack_all_packet()
            self.resend_all_timeout_packet()
        
        """send a FIN segment to remote host"""
        pkt = MyTcpPacket(self.mytcplink)
        pkt.flag = MyTcpPacket.flag = MyTcpPacket.FLAG_FIN
        pkt.seq_num = self.win_slide
        pkt.win_size = self.win_size
        self.sock.sendto(pkt.pack(), (self.mytcplink.dst, self.mytcplink.dst_port))
        pkt.sent()
        self.packet_list.append(pkt)
        self.win_slide += 1
        sleep(1)

        """enter FIN_WAIT2 state"""
        self.mytcplink.state = MyTcpLink1.STATE_FIN_WAIT2

        print 'sending exit fin_wait'
    
    """get a new packet from send buffer"""
    def pop(self):
        return self.mytcplink.sending_need_a_new_packet()
    
    """ack all successfully received packets"""
    def ack_all_packet(self):
        while True:
            ack = self.ack_list.pop()
            if ack is None:
                break
            pkt = self.packet_list.pop_by_seq_num(ack.seq_num)
            if pkt is not None:
                self.mytcplink.logger.send_log(pkt)
                pkt.acked()
                self.win_start += 1

    """check if the packets in sending is timeout"""
    def resend_all_timeout_packet(self):
        for item in self.packet_list.packet_list:
            if item.timer.timeout() is True:
                if item.timer.interval >= self.mytcplink.max_timeout:
                    self.mytcplink.link_down()
                    break
                else:
                    self.mytcplink.retrans_count += 1
                    #item.timer.interval *= 2
                    self.sock.sendto(item.pack(), (self.mytcplink.dst, self.mytcplink.dst_port))
                    item.timer.start()

    def send_next_window(self):
        """if has left packet need to be sent , do it right here"""
        """if the previous window is still not finished , just return"""
        if self.win_start < self.win_slide:
            return
        
        """send packet"""
        for seq in range(self.win_start, self.win_start + self.win_size):
            pkt = self.pop()
            if pkt is None:
                break
            if pkt.flag == MyTcpPacket.FLAG_FIN:
                self.mytcplink.state = MyTcpLink1.STATE_FIN_WAIT
                break
            pkt.win_size = self.win_size
            self.sock.sendto(pkt.pack(), (self.mytcplink.dst, self.mytcplink.dst_port))
            pkt.sent()
            self.mytcplink.sent_count += 1
            self.win_slide += 1
            self.packet_list.append(pkt)
    
    """sending packets loop"""
    def run(self):
        while self.mytcplink.state == MyTcpLink1.STATE_RUN:
            sleep(0.001)
            self.resend_all_timeout_packet()
            self.ack_all_packet()
            self.send_next_window()

        self.enter_fin_wait()
        print('sending thread exit')


class MyTcpLinkRecving():
    def __init__(self, mytcplink):
        self.mytcplink = mytcplink
        self.win_available = mytcplink.win_size
        self.packet_list = MyTcpPacketSafeQueue('recving')
        self.win_available = mytcplink.win_size
        self.sock = self.mytcplink.sock
        self.wanna_seq = 0 
        self.pop_seq = 0
        self._thread = Thread(target=MyTcpLinkRecving.run, args=[self])
        self._thread.setDaemon(True)
        self._thread.start()

    """send back a fin segment"""
    def enter_fin_wait2(self):
        pkt = MyTcpPacket(self.mytcplink)
        pkt.flag = MyTcpPacket.flag = MyTcpPacket.FLAG_FIN
        self.sock.sendto(pkt.pack(), (self.mytcplink.dst, self.mytcplink.dst_port))
        pkt.sent()
    
    """append received packet to received buffer"""
    def append(self, packet):
        self.ack_packet(packet)
        self.packet_list.insert_in_order(packet)
        if packet.seq_num == self.wanna_seq:
            self.wanna_seq += 1
        while True:
            pkt = self.packet_list.pick(self.wanna_seq)
            if pkt is None:
                break
            self.wanna_seq += 1

    """check if a packet has been received"""
    def duplicated(self, packet):
        if packet.seq_num < self.wanna_seq:
            return True
        elif self.packet_list.pick(packet.seq_num) is not None:
            return True
    
    def duplicated_handler(self, packet):
        self.ack_packet(packet)
    
    def corrupted(self, data, chksum):
        return chksum != calc_checksum(data[2:])

    def corrupted_handler(self, packet):
        pass

    def accept_ack(self, packet):
        pkt = self.packet_list.pick(packet.seq_num)
        if pkt is not None:
            pkt.acked()
    
    """ack a packet"""
    def ack_packet(self, packet):
        pkt = MyTcpPacket(self.mytcplink)
        pkt.seq_num = packet.seq_num
        pkt.flag = MyTcpPacket.FLAG_ACK
        pkt.ack_num = self.wanna_seq
        self.mytcplink.ack_sock.sendto(pkt.pack(), (self.mytcplink.dst, self.mytcplink.ack_dst_port))
    
    """pop a packet from received packet list by order"""
    def pop(self):
        if self.pop_seq >= self.wanna_seq:
            return None
        pkt = self.packet_list.pop_by_seq_num(self.pop_seq)
        if pkt is not None:
            self.pop_seq += 1
        return pkt

    def run(self):
        resu = [None] * 24
        while self.mytcplink.state != MyTcpLink1.STATE_FIN_WAIT2:
            result = select([self.sock, self.mytcplink.ack_sock], [], [], 1)
            """process ack packets"""
            if self.mytcplink.ack_sock in result[0]:
                data, addr = self.mytcplink.ack_sock.recvfrom(1500)
                self.mytcplink.ack_dst_port = addr[1]
                packet = MyTcpPacket(self.mytcplink)
                packet.unpack(data)
                self.mytcplink.get_an_ack(packet)
            
            if self.sock not in result[0]:
                continue

            data, addr = self.sock.recvfrom(1500)
            self.mytcplink.dst_port = addr[1]
            packet = MyTcpPacket(self.mytcplink)
            packet.unpack(data)
            
            if self.corrupted(data, packet.checksum) is True:
                self.corrupted_handler(packet)
                continue

            if packet.flag == MyTcpPacket.FLAG_FIN:
                print 'i got fin'
                self.mytcplink.state = MyTcpLink1.STATE_FIN_WAIT2
                break
            
            if self.duplicated(packet) is True:
                self.duplicated_handler(packet)
                continue
            
            #self.packet_list.print_list()
            self.mytcplink.logger.receive_log(packet)
            self.append(packet)
        
        self.enter_fin_wait2()
        sleep(5)
        print('recv thread exit')


class MyTcpLinkRecv():
    def __init__(self, mytcplink):
        self.mytcplink = mytcplink
        self.packet_list = MyTcpPacketSafeQueue('recv')
        #self._thread = Thread(target=MyTcpLinkRecv.run, args=[self])
        #self._thread.setDaemon(True)
        #elf._thread.start()

    def pop(self):
        while self.mytcplink.state != MyTcpLink1.STATE_FIN:
            pkt = self.mytcplink.recv_need_a_new_packet()
            if pkt is None:
                sleep(0.001)
                continue
            if pkt.flag == MyTcpPacket.FLAG_FIN:
                return None
            return pkt.data


class MyTcpLinkSend():
    def __init__(self, mytcplink):
        self.seq_num = 0
        self.mytcplink = mytcplink
        self.packet_list = MyTcpPacketSafeQueue('send')

    def append(self, packet):
        packet.seq_num = self.seq_num
        self.seq_num += 1
        self.packet_list.append(packet)

    def pop(self):
        if self.packet_list.count() == 0:
            return None
        return self.packet_list.pop()


class MyTcpLink1():
    STATE_RUN = 0
    STATE_SENDING = 1
    STATE_FIN_WAIT = 2
    STATE_FIN_WAIT2 = 3
    STATE_FIN = 4
    STATE_DOWN = 5

    def __init__(self, sip, dip, sport, dport, ack_src_port, ack_dst_port, win_size, logfile):
        self.state = MyTcpLink1.STATE_RUN
        self.max_timeout = 10000000000
        self.win_size = win_size

        self.src = sip
        self.dst = dip
        self.src_port = sport
        self.dst_port = dport
        self.ack_src_port = ack_src_port
        self.ack_dst_port = ack_dst_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((sip, sport))

        self.ack_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ack_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ack_sock.bind((sip, self.ack_src_port))

        self.packet_list = MyTcpPacketSafeQueue('tcplink')

        self._send = MyTcpLinkSend(self)
        self._recv = MyTcpLinkRecv(self)
        self._recving = MyTcpLinkRecving(self)
        self._sending = MyTcpLinkSending(self)

        self.logger = Logger(self, logfile)
        self.trans_result = 'Success'
        self.retrans_count = 0
        self.sent_count = 0

    def recv_need_a_new_packet(self):
        return self._recving.pop()

    def sending_need_a_new_packet(self):
        return self._send.pop()

    def get_an_ack(self, packet):
        self._sending.ack_list.append(packet)

    def send(self, data):
        pkt = MyTcpPacket(self)
        pkt.flag = MyTcpPacket.FLAG_NORMAL
        pkt.set_data(data)
        self._send.append(pkt)

    def link_down(self):
        self.trans_result = 'Failed'
        self.state = MyTcpLink1.STATE_DOWN
        print 'Timeout too many times, Link down'
        self.logger.log_trans_info()
        sys.exit(0)

    def recv(self):
        return self._recv.pop()

    def close(self):
        pkt = MyTcpPacket(self)
        pkt.flag = MyTcpPacket.FLAG_FIN
        self._send.append(pkt)


class MyTimer():
    TIMER_RUN = 0
    TIMER_STOP = 1

    def __init__(self):
        self.state = MyTimer.TIMER_STOP
        self.interval = 2
        self.passed = 0
        self.starttime = 0
        self.count = time.time()
        self.count = 0

    def timeout(self):
        self.passed = time.time() - self.starttime
        return time.time() - self.count >= self.interval

    def start(self):
        self.count = time.time()
        self.state = MyTimer.TIMER_RUN

    def cancel(self):
        self.state = MyTimer.TIMER_STOP


class MyTcpPacket():
    FLAG_ACK = 1
    FLAG_FIN = 2
    FLAG_FIN_WAIT = 3
    FLAG_NORMAL = 4

    def __init__(self, mytcplink):
        self.flag = MyTcpPacket.FLAG_NORMAL
        self.data = ''
        self.len = 0
        self.checksum = 0
        self.ack_num = 0
        self.seq_num = 0
        self.timer = MyTimer()
        self.win_size = mytcplink.win_size
        self.mytcplink = mytcplink
        self.isacked = False
        self.need_resend = False

    def timeout(self):
        self.mytcplink.timeout_handler(self)

    def set_data(self, data):
        self.data = data
        self.len = len(self.data)

    def sent(self):
        self.timer.starttime = int(time.time())
        self.timer.start()

    def acked(self):
        self.timer.cancel()
        self.isacked = True

    def pack(self):
        self.checksum = 0
        fmt = 'HHHHHH%ds' % self.len
        packet = struct.pack(fmt,
                             self.checksum,
                             self.len,
                             self.seq_num,
                             self.ack_num,
                             self.win_size,
                             self.flag,
                             self.data
                             )
        self.checksum = calc_checksum(packet)
        fmt = 'H%ds' % len(packet[2:])
        return struct.pack(fmt ,self.checksum, packet[2:])

    def unpack(self, data):
        tp = struct.unpack('HH', data[:4])
        self.checksum = tp[0]
        self.len = tp[1]
        fmt = 'HHHH%ds' % self.len
        tp = struct.unpack(fmt, data[4:])
        self.seq_num = tp[0]
        self.ack_num = tp[1]
        self.win_size = tp[2]
        self.flag = tp[3]
        self.data = tp[4][:self.len]


class MyLock():
    def __init__(self, name):
        self.__lock = Lock()
        self.__name = name

    def lock(self):
        try:
            self.__lock.acquire()
        except:
            pass

    def unlock(self):
        try:
            self.__lock.release()
        except:
            pass


class MyTcpPacketSafeQueue():
    def __init__(self, name):
        self.name = name
        self.lock = MyLock('lock')
        self.packet_list = []
        if name == 'send':
            if os.access('file', os.R_OK) is True:
                os.remove('file')
    def append(self, (packet)):
        self.lock.lock()
        self.packet_list.append(packet)
        self.lock.unlock()

    def insert_in_order(self, packet):
        self.lock.lock()
        self.packet_list.append(packet)
        self.packet_list.sort(key=lambda p: p.seq_num)
        self.lock.unlock()
    
    def print_list(self):
        self.lock.lock()
        tmp = []
        for item in self.packet_list:
            tmp.append(item.seq_num)
        print tmp
        self.lock.unlock()
    
    """pop out the first packet"""
    def pop(self):
        self.lock.lock()
        packet = None
        if len(self.packet_list) > 0:
            packet = self.packet_list.pop(0)
        self.lock.unlock()

        return packet
    
    """pop out a packet according to it's seq num'"""
    def pop_by_seq_num(self, seq_num):
        self.lock.lock()
        packet = None
        for i in range(len(self.packet_list)):
            if seq_num == self.packet_list[i].seq_num:
                packet = self.packet_list.pop(i)
                break
        self.lock.unlock()

        return packet
    
    """pick a packet from queue , not remove it"""
    def pick(self, seq_num):
        self.lock.lock()
        packet = None
        for i in range(len(self.packet_list)):
            if seq_num == self.packet_list[i].seq_num:
                packet = self.packet_list[i]
        self.lock.unlock()
        return packet
    
    """packet count"""
    def count(self):
        return len(self.packet_list)
