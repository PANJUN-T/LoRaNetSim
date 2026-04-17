import json
import os
import time
from datetime import datetime

import simpy
import random

from .Channel import LoRaChannel
from .Gateway import GW

from .NodeMap import NodeMap
from .Node import Node
from .DynamicShowMap import DynamicShowMap

from src import GlobalCfg as GCfg


class LoRaSimulationEnv:
    def __init__(self, node_num, mac, optimization):
        self.env = simpy.Environment()  # simpy环境
        self.sim_duration = GCfg.SimulationDuration  # 仿真时长（ms）
        self.run_time = None
        # 仿真配置
        self.Parameter_Optimization = optimization.value  # 单节点参数优化方案
        self.MAC = mac  # MAC协议选择
        self.node_num = node_num  # 节点数量
        self._max_node_id = 0
        # 实体
        self.Nodes = []  # 节点实体
        self.GW = GW(self.env, 1)  # 网关实体
        self.CHANNEL = LoRaChannel(self.env, self.GW)  # 信道实体
        self.map = None
        # 仿真结果
        self.PRR = None
        self.Goodput = None
        self.EnergyEfficiency = None
        self.CADsPerFrame = None
        self.DelayTimePerFrame = None
        self.PRRs = []  # 节点PRR分布
        # 区间仿真结果
        self.temp_PRR = []
        self.temp_Goodput = []
        # ADR调参计时
        self.ADR_all_adjusted = False
        self.ADR_adjustment_time = 0
        self.ADR_stop_event = simpy.Event(self.env)

    def run(self):
        # 获取节点分布
        self.map = NodeMap.GetNodeMap(self.node_num, self.Parameter_Optimization)
        # 创建节点
        for nid in self.map.keys():
            node = Node(self.env, self.CHANNEL, self.GW, self.MAC,
                        int(nid), self.map[nid]['x'], self.map[nid]['y'], self.map[nid]['sf'], self.map[nid]['tp'])
            self.Nodes.append(node)
            self._max_node_id = int(nid)
            GCfg.SFNodes[int(node.SF)] += 1  # # 统计每个SF使用的节点数量

        # 动态自适应仿真时开启
        if GCfg.SimModule == "Dynamic":
            self.env.process(self.monitor())  # 区间统计
            # self.env.process(self.upnode())  # 动态节点数量

        # ADR仿真时开启
        if GCfg.SimModule == "ADR":
            self.env.process(self.DynamicShowMap())  # 动态显示地图

        start_time = time.time()  # 记录开始时间
        self.env.run(until=self.sim_duration)  # 开始仿真
        self.run_time = time.time() - start_time  # 计算耗时（秒）

        self.Show_Results()

    def upnode(self):
        yield self.env.timeout(GCfg.STATISTICS_INTERVAL * 5 * 1)
        # 添加节点
        n = 1500
        map_temp = NodeMap.GetNodeMap(n, self.Parameter_Optimization)
        for info in map_temp.values():
            nid = self._max_node_id + 1
            node = Node(self.env, self.CHANNEL, self.GW, self.MAC,
                        int(nid), info['x'], info['y'], info['sf'], info['tp'])
            self.Nodes.append(node)
            self._max_node_id = nid

        yield self.env.timeout(GCfg.STATISTICS_INTERVAL * 5 * 1)
        n = 1500
        map_temp = NodeMap.GetNodeMap(n, self.Parameter_Optimization)
        for info in map_temp.values():
            nid = self._max_node_id + 1
            node = Node(self.env, self.CHANNEL, self.GW, self.MAC,
                        int(nid), info['x'], info['y'], info['sf'], info['tp'])
            self.Nodes.append(node)
            self._max_node_id = nid

        # 删除节点
        # yield self.env.timeout(STATISTICS_INTERVAL * 5 * 2)
        # n = 2000
        # del_nodes = random.sample(self.Nodes, n)
        # for node in del_nodes:
        #     if node.ID != 1:
        #         node.send_process.interrupt()
        #         self.Nodes.remove(node)

    def monitor(self):
        while True:
            yield self.env.timeout(GCfg.STATISTICS_INTERVAL / 2)
            print("time: {:.1f}s".format(self.env.now / 60000))
            # 每隔一段时间统计网络性能
            sumSend = 0
            for node in self.Nodes:
                sumSend += node.sent_in_interval
                node.sent_in_interval = 0

            sumReceive = self.GW.receive_in_interval
            self.GW.receive_in_interval = 0

            # PRR
            self.temp_PRR.append(0 if sumSend == 0 else min(sumReceive / sumSend, 1.0))
            # Goodput
            self.temp_Goodput.append((sumReceive * GCfg.LoRaParameter.PL) / (GCfg.STATISTICS_INTERVAL / 2 / 1000))

    def DynamicShowMap(self):
        DynamicMap = {}
        DM = DynamicShowMap()  # 动态地图

        while True:
            # 重建地图字典
            for node in self.Nodes:
                DynamicMap[node.ID] = {
                    'x': node.X,
                    'y': node.Y,
                    'd': node.To_GW_Distance,
                    'sf': node.SF,
                    'tp': node.TP
                }
            DM.ShowMap(DynamicMap)  # 更新图像
            print("time: {:.1f}s".format(self.env.now / 60000))
            yield self.env.timeout(GCfg.STATISTICS_INTERVAL)  # 刷新率

    def Show_Results(self):
        SumReceive = self.GW.receive_sum
        SumReceiveEnergy = self.GW.rec_energy_sum

        SumSend = 0
        SumCAD = 0
        SumSendEnergy = 0
        sumDelayTime = 0
        for node in self.Nodes:
            SumSend += node.send_sum
            SumCAD += node.cad_sum
            SumSendEnergy += node.energy_sum
            sumDelayTime += node.avg_delay
            self.PRRs.append(0 if (node.send_sum == 0) else round(node.aflewer / node.send_sum, 4))

        # 注意异常数据处理：不能除0
        # PRR
        self.PRR = 0 if (SumSend == 0) else (SumReceive / SumSend)
        # Goodput
        self.Goodput = (SumReceive * GCfg.LoRaParameter.PL) / (self.sim_duration / 1000)
        # EnergyEfficiency
        self.EnergyEfficiency = 0 if (SumSendEnergy == 0) else (SumReceiveEnergy / SumSendEnergy)
        # 每成功发送一帧需要的CAD数量
        self.CADsPerFrame = 0 if (SumSend == 0) else int(SumCAD / SumSend)
        # 传输一帧的平均时延
        self.DelayTimePerFrame = sumDelayTime / self.node_num

        if GCfg.SimModule != "SN" and GCfg.SimModule != "ADR":
            print("{}, nNode:{}, Send:{}, Receive:{}, CADs/Frame:{}, PRR:{:.1f}%, Goodput:{:.1f}B/s, "
                  "eta:{:.1f}%, DT:{:.0f}, RunTime:{:.4f}"
                  .format(self.MAC.value, self.node_num, SumSend, SumReceive, self.CADsPerFrame,
                          self.PRR * 100, self.Goodput, self.EnergyEfficiency * 100, self.DelayTimePerFrame,
                          self.run_time))
