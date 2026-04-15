import math
import numpy as np
from .Packet import Packet
from collections import deque
from typing import Dict, Tuple, Deque

from src import GlobalCfg as GCfg

import random


class LoRaChannel:
    def __init__(self, env, gw):
        self.env = env
        self.gw = gw
        self.ch_list = GCfg.LoRaParameter.CH_List
        self.sf_list = GCfg.LoRaParameter.SF_List
        # 字典定义信道中正在传输中的数据包,键为逻辑信道，键值为队列，存放注册的数据包 # TODO 扩展可选带宽时，逻辑信道索引加入BW
        self.sending_pkts: Dict[Tuple[int, int], Deque] = {}

        # 初始化所有CH/SF组合为deque，不考虑带宽B作为逻辑信道索引，LoRaWAN规范中上行信道只使用125KHz
        for ch in self.ch_list:
            for sf in self.sf_list:
                LogicalChannel_Index = (ch, sf)
                self.sending_pkts[LogicalChannel_Index] = deque()  # 正在传输的数据包

    def TX(self, node, pkt):  # 传输packet类，数据包实体
        # print("debug: send: pid-{}, nid-{}, sf-{}, ch-{}".format(pkt.pid, pkt.node, pkt.sf, pkt.ch))

        # 碰撞检测
        self.CollisionDetection(pkt)

        # 注册到对应逻辑信道
        ChannelIndex = (pkt.ch, pkt.sf)
        self.sending_pkts[ChannelIndex].append(pkt)

        # 记录发送数据包数量与能耗
        node.send_sum += 1
        node.energy_sum += pkt.pktenergy
        node.sent_in_interval += 1  # 区间统计

        # TOA
        yield self.env.timeout(pkt.TOA)

        # 移除数据包,网关处理
        self.sending_pkts[ChannelIndex].remove(pkt)  # 清除信道中的数据包
        self.gw.ReceivePkt(pkt)  # 网关处理

    def ChannelActivityDetection(self, node, packet):
        # 记录CAD次数与能量消耗
        node.cad_sum += 1
        node.energy_sum += packet.cadenergy

        # 逻辑信道索引 ChannelIndex
        ChannelIndex = (packet.ch, packet.sf)
        pkt_list = list(self.sending_pkts[ChannelIndex])  # 相同逻辑信道中正在传输数据包

        if not pkt_list:  # 逻辑信道中数据包队列为空, 信道空闲
            return False
        else:
            if GCfg.Actual_CADe:  # 实测CAD检测效率 TODO 待验证
                # 当存在多个数据包时，只考虑最高信噪比的数据包
                active_pkt = pkt_list[0]
                MinD = node.Calculate_distance2me(active_pkt.node.X, active_pkt.node.Y)
                for temp_pkt in pkt_list:
                    d = node.Calculate_distance2me(temp_pkt.node.X, temp_pkt.node.Y)
                    if d < MinD:
                        MinD = d
                        active_pkt = temp_pkt

                # 计算CAD效率
                snr = active_pkt.getSNR(MinD)
                sf = packet.sf
                CADp = GCfg.sigmoid(snr, GCfg.CADe[sf - 7][0], GCfg.CADe[sf - 7][1])

                # CADp为0~1，以CADp为概率，有CADp的概率返回True,否者函数返回False
                random_num = random.random()  # 生成0~1之间的随机浮点数
                result = random_num <= CADp  # 比较随机数和CADp：随机数≤CADp则返回True，否则False
                return result
            else:  # 100%CAD检测效率
                return True

    def CollisionDetection(self, pkt):
        # 逻辑信道索引
        ChannelIndex = (pkt.ch, pkt.sf)
        # 碰撞检测(标记自己与其他碰撞包) TODO 待加入捕获效应（但捕获效应在多数据包碰撞场景几乎不起作用，可不考虑捕获效应）
        if len(self.sending_pkts[ChannelIndex]) > 0:  # 有正在活跃的数据包，碰撞！
            pkt.collided = True  # 标记自己
            for active_pkt in self.sending_pkts[ChannelIndex]:
                active_pkt.collided = True  # 标记正在传输的包
