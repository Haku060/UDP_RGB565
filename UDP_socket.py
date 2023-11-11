import socket


def UDP_Init(addr, port):
    # 创建一个udp套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536*16384)
    LocalAddr = (addr, port)
    sock.bind(LocalAddr)
    return sock


def UDP_Receive(udp_socket, length):
    # udp接收数据
    recv_data = udp_socket.recv(length)
    return recv_data


def UDP_Close(udp_socket):
    # 关闭UDP套接字
    udp_socket.close()
