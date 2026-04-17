# from .GlobalCfg import *
from src import GlobalCfg as GCfg
from .Packet import Packet
from src.CoverageModule import CoverageModule

class GW:
    def __init__(self, env, gid):
        # 仿真环境
        self.env = env
        # 属性
        self.ID = gid
        self.X = 0
        self.Y = 0
        # 统计
        self.rec_energy_sum = 0
        self.receive_sum = 0
        self.receive_in_interval = 0  # 区间统计
        self.c = 0



    def ReceivePkt(self, pkt):
        RSS = pkt.GW_RSS  # 数据包在网关处信号强度
        SNR = pkt.GW_SNR  # 数据包在网关处信噪比
        sf_idx = pkt.node.SF - 7
        # 数据包接收条件判断 (数据包未碰撞且信道强度大于接收阈值), (仿真器性能测试模式只检测碰撞)
        if (not pkt.collided) if GCfg.SimModule == "SN" else (not pkt.collided and RSS >= CoverageModule.sensi[sf_idx]):
            self.receive_sum += 1  # 接收+1
            self.receive_in_interval += 1
            self.rec_energy_sum += pkt.pktenergy
            # print("debug: Node-{}, SF-{}, CH-{}".format(rec_packet.node, rec_packet.sf, rec_packet.ch))

            # ACK / DownLink
            pkt.ACK = True
            pkt.DownMsg = None  # 可扩展下行消息

            # ADR：下行调参算法 (根据信噪比调整节点通信参数)
            if GCfg.ADR:
                node = pkt.node
                node.SNRList.append(SNR)
                # if len(node.SNRList) >= node.SNR_NUM:
                if len(node.SNRList) >= node.SNR_NUM and not node.ADR_adjusted:
                    SNRmin = CoverageModule.SNR_Req[node.SF - 7]
                    M = 4
                    SNRmax = max(node.SNRList)
                    SNRmargin = SNRmax - SNRmin - M
                    Nstep = int(SNRmargin // 3)

                    SF_List = list(GCfg.LoRaParameter.SF_List)
                    min_sf = min(SF_List)

                    if Nstep > 0:
                        while Nstep > 0:
                            if node.SF > min_sf:
                                node.SF -= 1
                                Nstep -= 1
                            elif node.TP > 2:
                                node.TP = max(node.TP - 3, 2)
                                Nstep -= 1
                            else:
                                break
                    elif Nstep < 0:
                        if node.TP < 20:
                            while Nstep < 0:
                                node.TP = min(node.TP + 3, 20)
                                Nstep += 1
                    # node.SNRList.clear()
                    # node.ADR_adjusted = True

