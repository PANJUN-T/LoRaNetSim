import numpy as np
import simpy

# from .GlobalCfg import *
from ctrl import GlobalCfg as GCfg
from .Packet import Packet
import random
import math
from math import ceil
from collections import deque
from typing import Dict, Tuple, Deque

from .LifetimeModule import LifetimeModule


class Node:
    # 仿真环境, 信道实体, 网关实体, MAC协议, 发送间隔, 节点ID, X, Y , sf, tp
    def __init__(self, env, channel, bs, mac, nid, x, y, sf, tp):
        # 仿真环境
        self.env = env
        self.channel = channel
        # 基本属性
        self.MAC = mac
        self.BS = bs
        self.ID = nid
        self.X = x
        self.Y = y
        self.To_GW_Distance = self.Calculate_distance2me(self.BS.X, self.BS.Y)
        # 配置
        self.CH = random.choice(GCfg.LoRaParameter.CH_List)  # 随机信道
        self.SF = sf
        self.TP = tp
        self.BW = GCfg.LoRaParameter.BW
        self.CR = GCfg.LoRaParameter.CR
        self.PL = GCfg.LoRaParameter.PL
        if GCfg.SimModule == "SN":
            self.CH = GCfg.SN[GCfg.SN_idx][1]
            self.SF = GCfg.SN[GCfg.SN_idx][2]
            self.TP = GCfg.SN[GCfg.SN_idx][0]
            self.BW = GCfg.SN[GCfg.SN_idx][3]
            self.CR = GCfg.SN[GCfg.SN_idx][4]
            self.PL = GCfg.SN[GCfg.SN_idx][5]
            self.CH = GCfg.LoRaParameter.CH_List[0]

        # ADR ACK List
        # 上行ADR
        self.ACK_COUNT = 0
        self.ACK_NUM = 10  # 每10个数据包判断一次是否需要调整参数
        self.ACKList = deque(maxlen=self.ACK_NUM)
        # 下行ADR
        self.SNR_NUM = 20
        self.SNRList = deque(maxlen=self.SNR_NUM)
        self.ADR_adjusted = False

        # LMAC
        self.DIFS_NUM = 12
        self.MAX_NBO = 64

        # 统计
        self.total_delay = 0
        self.avg_delay = 0
        self.send_sum = 0
        self.cad_sum = 0
        self.energy_sum = 0
        self.aflewer = 0  # 成功送达到网关的计数器，用于统计节点分布性能

        # 区间统计
        self.sent_in_interval = 0

        # LMAC-2 需要用到的信道占用情况 节点视图
        self.channel_state: Dict[Tuple[int, int], float] = {}  # 信道状态
        for ch in self.channel.ch_list:
            for sf in self.channel.sf_list:
                key = (ch, sf)
                self.channel_state[key] = 0

        self.resource = simpy.Resource(self.env, capacity=1)  # 待发送数据包队列
        self.timer_process = self.env.process(self.Timer())

    def Timer(self):
        # DS_LoRa 退避时隙数量上限确定
        self.MaxSlot = max(math.ceil(GCfg.SFNodes[int(self.SF)] / len(GCfg.LoRaParameter.CH_List)), 1)
        self.MaxSlot = max(min(self.MaxSlot - 1, 80), 1)

        # 泊松分布的数据包产生
        while True:
            timeval = random.expovariate(GCfg.lamuda) * 1000  # ms
            yield self.env.timeout(timeval)

            # 获取数据包实体
            # self.PL = random.randint(5, 25)  # 随机负载长度
            packet = self.Generate_Packet()

            # 发送数据包
            self.env.process(self.Transmit(packet))

    def Transmit(self, packet):
        # 队列形式的数据包发送任务，不丢弃旧包
        with self.resource.request() as req:
            yield req  # 等待本节点信道空闲

            # MAC层
            try_time = self.env.now
            # 🔶1、ALOHA，随机选择信道发送
            if self.MAC.value == "ALOHA":
                pass
            # 🔶2、LMAC-1，CAD+退避
            elif self.MAC.value == "LMAC-1":
                # ---> DIFS
                while True:
                    _is_busy = False
                    for _ in range(self.DIFS_NUM):
                        _is_busy |= self.channel.ChannelActivityDetection(self, packet)
                        yield self.env.timeout(packet.Tcad)
                    if not _is_busy:  # DIFS期间所有CAD都空闲，跳出DIFS，进入退避阶段
                        break
                # ---> NBO
                NBO = random.randint(4, self.MAX_NBO)
                while NBO > 0:
                    CADResult = self.channel.ChannelActivityDetection(self, packet)
                    yield self.env.timeout(packet.Tcad)
                    if not CADResult:  # 信道空闲 减退避值
                        NBO -= 1
                    else:
                        # ---> DIFS
                        while True:
                            _is_busy = False
                            for _ in range(self.DIFS_NUM):  # CAD
                                _is_busy |= self.channel.ChannelActivityDetection(self, packet)
                                yield self.env.timeout(packet.Tcad)
                            if not _is_busy:  # DIFS期间所有CAD都空闲，跳出DIFS
                                break
            # 3、🔶LMAC-2, CAD+退避+信道切换
            elif self.MAC.value == "LMAC-2":
                a = 0.2
                # 新信道，记录清零
                cad_total, cad_failed = 0, 0
                # ---> DIFS
                while True:
                    _is_busy = False  # self.channel.ChannelActivityDetection(self, packet)
                    for _ in range(self.DIFS_NUM):
                        CADResult = self.channel.ChannelActivityDetection(self, packet)
                        yield self.env.timeout(packet.Tcad)
                        _is_busy |= CADResult
                        # 记录
                        if CADResult:
                            cad_failed += 1
                        cad_total += 1
                    if not _is_busy:  # DIFS期间所有CAD都空闲，跳出DIFS
                        break
                    else:  # 切换更好的信道
                        key = (packet.ch, packet.sf)
                        # 记录当前信道结果
                        self.channel_state[key] = a * self.channel_state[key] + (1 - a) * cad_failed / cad_total
                        # 冒泡排序，寻找同SF下更优的CH
                        lowest_idx = key
                        lowest = self.channel_state[key]
                        for ch in self.channel.ch_list:
                            key = (ch, packet.sf)
                            if self.channel_state[key] < lowest:
                                lowest = self.channel_state[key]
                                lowest_idx = key  # 记录信道索引
                        # 切换信道 TODO 是否同步更新节点信道?
                        packet.ch = lowest_idx[0]
                        self.CH = packet.ch
                        cad_total, cad_failed = 0, 0
                # ---> NBO
                NBO = random.randint(4, self.MAX_NBO)
                while NBO > 0:
                    CADResult = self.channel.ChannelActivityDetection(self, packet)
                    yield self.env.timeout(packet.Tcad)
                    # 记录
                    if CADResult:
                        cad_failed += 1
                    cad_total += 1
                    if not CADResult:  # 信道空闲 减退避值
                        NBO -= 1
                    else:  # 切换更好的信道
                        key = (packet.ch, packet.sf)
                        # 记录当前信道结果
                        self.channel_state[key] = a * self.channel_state[key] + (1 - a) * cad_failed / cad_total
                        # 冒泡排序，寻找同SF下更优的CH
                        lowest_idx = key
                        lowest = self.channel_state[key]
                        for ch in self.channel.ch_list:
                            key = (ch, packet.sf)
                            if self.channel_state[key] < lowest:
                                lowest = self.channel_state[key]
                                lowest_idx = key  # 记录信道索引
                        # 切换信道
                        packet.ch = lowest_idx[0]
                        self.CH = packet.ch
                        cad_total, cad_failed = 0, 0
                        # ---> DIFS
                        while True:
                            _is_busy = False
                            for _ in range(self.DIFS_NUM):  # CAD
                                CADResult = self.channel.ChannelActivityDetection(self, packet)
                                yield self.env.timeout(packet.Tcad)
                                _is_busy |= CADResult
                                # 记录
                                if CADResult:
                                    cad_failed += 1
                                cad_total += 1
                            if not _is_busy:  # DIFS期间所有CAD都空闲，跳出DIFS
                                break
                            else:  # 切换更好的信道
                                key = (packet.ch, packet.sf)
                                # 记录当前信道结果
                                self.channel_state[key] = (a * self.channel_state[key] +
                                                           (1 - a) * cad_failed / cad_total)
                                # 冒泡排序，寻找同SF下更优的CH
                                lowest_idx = key
                                lowest = self.channel_state[key]
                                for ch in self.channel.ch_list:
                                    key = (ch, packet.sf)
                                    if self.channel_state[key] < lowest:
                                        lowest = self.channel_state[key]
                                        lowest_idx = key  # 记录信道索引
                                # 切换信道
                                packet.ch = lowest_idx[0]
                                self.CH = packet.ch
                                cad_total, cad_failed = 0, 0

            # 4、🔶CSMA-LORA-new, 扩展DIFS时间到TOA
            elif self.MAC.value == "CSMA-LoRa":
                DIFS_CAD_NUM = 9
                maxTOA = LifetimeModule.TOACalculate(packet.bw, packet.sf, packet.cr, 25)
                DelayTime = maxTOA / (DIFS_CAD_NUM - 1)
                CAD_Counter = 0
                # ---> DIFS
                while True:
                    # CAD
                    _is_busy = self.channel.ChannelActivityDetection(self, packet)
                    yield self.env.timeout(packet.Tcad)
                    CAD_Counter += 1
                    if not _is_busy:
                        # DIFS期间，连续CAD报告空闲，退出DIFS，发送数据
                        if CAD_Counter == DIFS_CAD_NUM:
                            break
                        # 信道空闲，等待执行下一个CAD
                        yield self.env.timeout(DelayTime)
                    else:
                        # 信道繁忙，休眠TOA时间
                        yield self.env.timeout(maxTOA)
                        CAD_Counter = 0  # 重启CAD计数

            Success_time = self.env.now

            # 发送
            yield self.env.process(self.channel.TX(self, packet))

            # 记录平均时延
            self.total_delay += (Success_time - try_time)
            self.avg_delay = self.total_delay / self.send_sum

            self.CheckDownLink(packet)  # 检查下行

    def Generate_Packet(self):
        packet = Packet(self, self.To_GW_Distance, self.BS)
        return packet

    def Calculate_distance2me(self, x, y):
        x0 = self.X
        y0 = self.Y
        distance = np.sqrt((x0 - x) * (x0 - x) + (y0 - y) * (y0 - y))
        return distance

    def CheckDownLink(self, packet):
        # ACK\NACK
        if packet.ACK:
            self.aflewer += 1
        # 记录ACK（只有未碰撞的包才记录）,去除因为碰撞引起的丢包,只考虑信噪比丢包
        if not packet.collided:
            self.ACKList.append(packet.ACK)
            # self.ACK_COUNT += 1
        # 上行ADR
        # if GCfg.ADR:
        #     if self.ACK_COUNT % self.ACK_NUM == 0:  # 达到最高上行尝试次数
        #         failed_num = self.ACKList.count(False)
        #         if failed_num == self.ACK_NUM:
        #             max_sf = max(GCfg.LoRaParameter.SF_List)
        #             if self.SF < max_sf:
        #                 self.SF += 1
