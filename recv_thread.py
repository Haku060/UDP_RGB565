import numpy as np
import UDP_socket
import threading
import queue
import time
import cv2
import os

frame_queue = queue.Queue()  # 创建一个队列用于存储接收到的帧数据
line_cnt = 0
line_read = 0


def read_from_queue(_queue, size):
    data = b''
    while len(data) < size:
        try:
            chunk = _queue.get()  # 从队列中获取数据，设置超时时间为1秒
        except queue.Empty:
            break  # 如果队列为空，则退出循环
        data += chunk
    return data


def convert_rgb565_to_rgb(rgb565_data, width, height):
    # 将RGB565数据转换为RGB格式
    rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
    rgb_data[:, :, 0] = rgb565_data[:, :, 0] & 0xF8
    rgb_data[:, :, 1] = (((rgb565_data[:, :, 0] & 0x07) << 3) | ((rgb565_data[:, :, 1] & 0xE0) >> 5)) << 2
    rgb_data[:, :, 2] = ((rgb565_data[:, :, 1] & 0x1F) << 3)
    return rgb_data


class RecvThread(threading.Thread):
    def __init__(self, threadID, addr, port, height, width):
        threading.Thread.__init__(self)
        self.DATAGRAM_SIZE = int(os.environ.get('DATAGRAM_SIZE', default='65507'))
        self.threadID = threadID
        self.height = height
        self.width = width
        self.addr = addr
        self.port = port
        self.call = True


    def run(self) -> None:
        global line_cnt, line_read
        recv_state = 0
        old_recv_cnt = 0
        recv_cnt = 0
        print("开始接收线程,threadID=" + str(self.threadID))
        udp_socket = UDP_socket.UDP_Init(self.addr, self.port)  # 初始化UDP套接字

        while True:
            chunk = UDP_socket.UDP_Receive(udp_socket, self.DATAGRAM_SIZE)  # 从UDP套接字接收数据
            recv_cnt = recv_cnt + 1  # 计数
            if len(chunk) == 2564:  # 判断包头
                print(chunk[:4])
                print(recv_cnt)
                if recv_state == 1:  # 如果接受到另一个包头
                    line_cnt = recv_cnt - old_recv_cnt
                    # print(line_cnt)
                    if line_cnt == self.height:
                        if self.call:
                            ShowPic_Thread(threadID=2, width=self.width, height=self.height).start()  # 启动显示图片子线程
                            self.call = False
                    else:
                        line_read = line_read + 1

                old_recv_cnt = recv_cnt
                frame_queue.put(chunk[4:])
                recv_state = 1  # 进入接受模式
            elif recv_state == 1:  # 接收过程
                frame_queue.put(chunk)  # 将接收到的数据放入队列中
        print("停止接收线程,threadID=" + str(self.threadID))


class ShowPic_Thread(threading.Thread):
    def __init__(self, threadID, height, width):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.last_frame_time = time.perf_counter()
        self.frame_times = []
        self.height = height
        self.width = width

    def run(self) -> None:
        global line_cnt, line_read
        line_read_done = 0
        print("开始显示线程,threadID=" + str(self.threadID))
        while ~frame_queue.empty():
            if line_cnt == self.height:
                # self._cntfps()
                show_data = read_from_queue(frame_queue, (self.height * self.width * 2))  # 从队列中读取帧数据
                built_data = np.frombuffer(show_data, dtype=np.uint8).reshape((self.height, self.width, 2))  # 转换为图像数据
                data = convert_rgb565_to_rgb(built_data, self.width, self.height)
                data = cv2.flip(data, 1)
                try:
                    if line_read == line_read_done:
                        cv2.imshow('RGB Image', data)  # 显示图片
                        cv2.waitKey(1)  # 等待1毫秒，接收键盘输入
                except:
                    print("Show_False")
            elif ~(line_cnt == self.height) and line_read != line_read_done:
                read_from_queue(frame_queue, (line_cnt * self.width * 2))  # 从队列中读取帧数据
                line_read_done = line_read_done + 1
                print(line_read_done)

        print("结束显示线程,threadID=" + str(self.threadID))


    def _cntfps(self):
        current_time = time.perf_counter()  # 记录现在的时间
        self.frame_times.append(current_time - self.last_frame_time)  # 计算出当前图片帧的接收时间，将其添加到frame_times列表中
        if len(self.frame_times) > int(os.environ.get('AVERAGE_SPAN', default='100')):
            self.frame_times = self.frame_times[1:]
        self.last_frame_time = current_time  # 更新last_frame_time变量的值为当前的时间
        fps = len(self.frame_times) / sum(self.frame_times)  # 计算出平均的帧率，即列表的长度除以列表的元素之和
        print(f"fps:{fps:.2f} fps")   # 打印出帧率和接收数量的信息
