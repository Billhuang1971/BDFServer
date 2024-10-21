# -*- coding: utf-8 -*-
import binascii
import ctypes
import datetime
import inspect
import pickle
import struct

import socket
import time

import select
import threading
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import pyqtSignal, QObject
from numpy.version import release


class socketServer(QObject):
    trainSig = pyqtSignal(list)
    def __init__(self, s_ip, s_port):
        super().__init__()
        self.ip = s_ip
        self.port = s_port
        self.appServers_tool = None
        self.sock =None
        #self.myserviceTimer = threading.Timer(1, self.serverTimer)
        self.trainSig.connect(self.run)
        self.inputs=None
        self.executor=None
        self.handle_mutex = threading.Lock()
    def sockServerStart(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((self.ip, self.port))
            self.sock.setblocking(False)
            self.sock.listen()
            self.inputs = [self.sock, ]
            self.myserviceTimer = threading.Thread(target=self.serverTimer)
            self.executor = ThreadPoolExecutor(max_workers=8)  # 设置线程池最大数量
            self.serverStart()
            self.myTip(0,['admin', '服务端启动...', '', ''])
            return None
        except Exception as e:
            self.myTip(0, ['admin', f'{e}', '', ''])
            return e

    def appMain(self, clientAddr, REQmsg):
        pass
    def handle_received_data(self, event, data):
        self.handle_mutex.acquire()
        addr = event.getpeername()
        print(f"服务端接收数据1：{addr} -cmd-{data[0]},id-{data[1]}")
        data2 = self.appMain(addr, data)
        dada0,len=self.send_msg(event, data2)
        print(f"服务端发送数据2：len:{len} -cmd-{data2[0]},id-{data2[1]}")
        self.handle_mutex.release()
    def serverStart(self):
        self.myserviceTimer.start()

    def serverTimer(self):
        try:
          while True:
            r_list, w_list, e_list = select.select(self.inputs, [], [])
            for event in r_list:
                if event in e_list:
                    addr = event.getpeername()
                    print(f"客户端{addr}断开连接e_list")
                    self.inputs.remove(event)
                    event.close()
                    continue
                if event == self.sock:
                    new_sock, addresses = event.accept()
                    self.inputs.append(new_sock)
                    print(f"新的客户端连接:{addresses}")
                else:
                    try:
                      data, msg_len = self.recv_msg(event)
                      if data:
                          if data[0] == 'modelTrain' and data[1] == 3:
                              self.trainSig.emit([event, data])
                          elif data[0] == 'auto' and data[1] == 7:
                              self.trainSig.emit([event, data])
                          elif data[0] == 'modelTest' and data[1] == 2:
                              self.trainSig.emit([event, data])
                          else:
                              self.executor.submit(self.handle_received_data, event, data)
                      else:
                          addr = event.getpeername()
                          print(f"客户端{addr}断开连接22")
                          self.inputs.remove(event)
                          event.close()
                    except Exception as e:
                            addr = event.getpeername()
                            print(f"e客户端{addr}断开连接11", e)
                            self.inputs.remove(event)
                            event.close()
                            break
        except Exception as e:
            print(f"eserverTimer() err:{e}")

         #self.myserviceTimer = threading.Timer(0.1, self.serverTimer)
         #self.myserviceTimer.start()
    def stop_myserviceTimer(self):
        self._async_raise(self.myserviceTimer.ident, SystemExit)
    def _async_raise(self, tid, exctype):
        try:
            tid = ctypes.c_long(tid)
            if not inspect.isclass(exctype):
                exctype = type(exctype)
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                tid, ctypes.py_object(exctype))
            if res == 0:
                raise ValueError("invalid thread id")
            elif res != 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
                raise SystemError("PyThreadState_SetAsyncExc failed")
        except Exception as err:
            print(err)
    def sockServerClose(self):
        self.stop_myserviceTimer()
        if self.executor != None:
            self.executor.shutdown(wait=False)
        if self.sock != None:
            self.sock.close()
            self.sock=None
        if self.inputs!=None:
           for event in self.inputs:
              event.close()
              self.inputs.remove(event)
           self.inputs.clear()
    def checksum(self,data):
        chksum = 0
        for byt in bin(data)[2:]:
            chksum += int(byt)
        return chksum & 0xffffffff

    def send_msg(self,conn, data):
        msg = pickle.dumps(data)
        chknum=self.checksum(len(msg))
        msg0 = struct.pack('>Ii', len(msg),chknum) + msg
        conn.sendall(msg0)
        return data, len(msg0)

    def recv_from(self,conn, n):
        data = b''
        handle_len = 0

        while handle_len < n:
            try:
                packet = conn.recv(n - handle_len)
                if not packet or packet == b'':
                    if n <= 8:
                        return None
                    print(f'网络掉包(' + str(handle_len) + "<" + str(n) + '), 纠验重置.')
                    continue
                    # return None
                handle_len += len(packet)
                data += packet
            except:
                if n <= 8:
                    return None
                if handle_len < n:
                    print(f'异常包(' + str(handle_len) + "<" + str(n) + '),纠验当前操作.')

        return data

    def recv_msg(self, conn):
        hd = self.recv_from(conn, 8)
        if not hd:
            return None, 0
        dd = struct.unpack('>Ii', hd)
        chknum = self.checksum(dd[0])
        if dd[1] != chknum:
            return None, 0
        msg_len = dd[0]
        msg = self.recv_from(conn, msg_len)
        msg = pickle.loads(msg)
        return msg, msg_len
    # def recv_from(self, conn, n):
    #     data = b''
    #     handle_len = 0
    #     stStime=None
    #     while handle_len < n:
    #         try:
    #             packet = conn.recv(n - handle_len)
    #             if not packet or packet == b'':
    #                 if n <= 8:
    #                     return None
    #                 print(f'网络掉包(' + str(handle_len) + "<" + str(n) + '), 纠验重置.')
    #                 if stStime is None:
    #                     stStime = datetime.datetime.now()
    #                 else:
    #                     now = datetime.datetime.now()
    #                     if int((now - stStime).total_seconds()) > 10:
    #                         return None
    #                 continue
    #                 # return None
    #             handle_len += len(packet)
    #             data += packet
    #             stStime = None
    #         except Exception as e:
    #             if n <= 8:
    #                 return None
    #             #return None
    #             if stStime is None:
    #                 stStime= datetime.now()
    #             else:
    #                 now=datetime.now()
    #                 if int((now - stStime).total_seconds())>10:
    #                     return None
    #             if handle_len < n:
    #                 print(f'异常包(' + str(handle_len) + "<" + str(n) + '),纠验当前操作.')
    #     return data
    #
    # def recv_msg(self, conn):
    #     hd = self.recv_from(conn, 8)
    #     if not hd:
    #         return None, 0
    #     dd = struct.unpack('>Ii', hd)
    #     chknum = self.checksum(dd[0])
    #     if dd[1] != chknum:
    #         return None, 0
    #     msg_len = dd[0]
    #     msg = self.recv_from(conn, msg_len)
    #     if msg is None:
    #         if self.hdpack is None or len(self.hdpack) < 2:
    #             return None, 0
    #         else:
    #             data = [self.hdpack[0], self.hdpack[1], self.hdpack[2], ['0', '1', '网络异常，接收数据不完整。']]
    #             return data, 4
    #     msg = pickle.loads(msg)
    #     return msg, msg_len


    def run(self, REPData):
        event = REPData[0]
        data = REPData[1]
        self.handle_received_data(event, data)