#!/usr/bin/env python3

""" 
client.py - Main code for sending/receiving TM and TC via TCP socket
"""

import argparse
from asyncio.windows_events import NULL
from enum import Enum
import socket
import struct
from ctypes import *
from threading import Thread
from time import sleep
import encodageTC
import decodageTM
import localCom
import paho.mqtt.client as mqtt

## Supported protocol
class Protocol(Enum):
    MQTT_e = 0
    TCP_e = 1

## Choose protocol to use
mode = Protocol.MQTT_e


class client_tcp:
    """
    Static main class. Contains the entry functions.
    """
    ## Socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @staticmethod
    def client_init(ip, port):
        """
        Create a tcp socket connecting to zybo addr and port 64000
        If the tcp server is active on zybo, this function will connect to the tcp server 
        and send the specified message

        Args:
            ip : string representing the IP address.
                ex : 192.168.1.21
            port : string containing the int of the port.
                ex : 64000.

        Return:
            The socket.
        """
        # Connection parameters
        server_addr = (ip, port)
        try:
            client_tcp.s.connect(server_addr)
            localCom.sendToCs(
                "Connected to {:s}".format(repr(server_addr)))
        except AttributeError as ae:
            localCom.sendToCs("Error creating the socket: {}".format(ae))
        except socket.error as se:
            localCom.sendToCs("Exception on socket: {}".format(se))
        return client_tcp.s

    @staticmethod
    def tcp_client_send():
        """
        Polling called.
        This method get all the TC (using encodage_tc) and send it by the socket.
        """
        msg = encodageTC.encode_tc()
        if(client_tcp.s == NULL):
            localCom.sendToCs("Socket not init.")
            return
        # Connected and send msg, wait for ack
        for tc in msg:
            # localCom.writeInPipe("send " + tc)
            client_tcp.s.send(tc.encode())
        # Close connection after ack

    @staticmethod
    def tcp_client_receive():
        """
        Launch in a thread.
        This method wait for receiving a TM, and then call decodageTM to process it.
        """
        localCom.sendToCs("In thread tcp_client_receive")
        while(1):
            buff = client_tcp.recv_TM(client_tcp.s)
            if buff:
                # localCom.writeInPipe("received TM, len = " + len(buff))
                decodageTM.decodeTM(buff)

    def recvall(sock, n):
        """
        Keep receiving data while length<n.
        Must use because TCP work with stream and not data.

        Args:
            sock : socket.
            n : size in bytes to receive.
        
        Return:
            The bytes packet containing the n data.
        """
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = None
            try:
                packet = sock.recv(n - len(data))
            except:
                localCom.sendToCs("Time out")
                return None
            finally:
                if not packet:
                    return None
                data.extend(packet)
        return data

    def recv_TM(sock):
        """
        Get the first 5 bytes.
        The first one contains the OP code.
        The next 4 ones contains the size in bytes.
        
        Args:
            sock : the socket.
            
        Return:
            The data packet containing the 5 first bytes and the data content.
        """
        # Read message length and unpack it into an integer
        TM_header_size = 5
        raw_TM_header = client_tcp.recvall(sock, TM_header_size)
        if not raw_TM_header:
            return None
        TM_content_size = struct.unpack('>I', raw_TM_header[1:5])[0]

        # Read the message data with timeout
        sock.settimeout(3.0)
        raw_TM_content = client_tcp.recvall(sock, TM_content_size)
        sock.settimeout(None)
        if raw_TM_content == None:
            return None
        
        return raw_TM_header + raw_TM_content

def callback_on_TM(client, userdata, message) :
    localCom.sendToCs("In the callback !")
    decodageTM.decodeTM(message)

def main():
    """
    Main function.
    Use argument as :
        ip : the string containing the ip.
        port : the int containing the port.
    
    After initializing the connection, the process will run a thread to deal with TM.
    Then, in a loop of 1 second, it will run a new thread to deal with TC.
    """
    localCom.sendToCs("In python client main...")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", type=str,
                        required=True, help="take IpV4 format addr")
    parser.add_argument("-p", "--port", type=int,
                        required=False, help="port of the server")
    args = parser.parse_args()

    if (mode == Protocol.MQTT_e) :
        localCom.sendToCs("Start MQTT communication...")
        client = mqtt.Client()
        client.on_message = callback_on_TM
        client.connect(args.ip)
        # Callback to get the TM
        client.subscribe("A-Eye/toClient",0)
        localCom.sendToCs("Callback set !")
        # TC is send by C#
        while(1):
            sleep(.1)
            # localCom.writeInPipe("Still there...")
    elif (mode == Protocol.TCP_e):
        localCom.sendToCs("Start TCP communication...")
        client_tcp.client_init(args.ip, args.port)
        # Thread receive
        receiver = Thread(target=client_tcp.tcp_client_receive)
        receiver.start()
        while(1):
            sender = Thread(target=client_tcp.tcp_client_send)
            sender.start()
            sleep(.1)
    else :
        localCom.sendToCs("Unsupported mode !")


if __name__ == "__main__":
    main()
