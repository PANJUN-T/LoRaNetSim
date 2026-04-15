import math
import random

from .CoverageModule import CoverageModule


from .LifetimeModule import LifetimeModule


class Packet:
    def __init__(self, node, distance, bs):
        # self.pid = generate(size=16)  # 生成唯一ID作为数据包的索引
        self.node = node
        self.sf = node.SF
        self.bw = node.BW
        self.cr = node.CR
        self.ch = node.CH
        self.tp = node.TP
        self.UpMsg = None   # 扩展数据包中可定义的负载信息，若要使用，作为初始化参数传入
        self.pl = node.PL  # 负载长度

        # 用于MACX
        self.first_try = True
        # 用于碰撞标记
        self.collided = False

        # TOA / CAD
        self.Tcad = (2.0 ** self.sf) / self.bw * 2  # ms
        self.TOA = self.TimeOnAir(self.sf, self.cr, self.pl, self.bw)  # ms
        self.cadenergy = 3.3 * 11 * self.Tcad / 1000        # 默认CAD电流11mA
        self.pktenergy = self.PktEnergy(self.tp, self.TOA)  # mJ

        # 数据包达到网关时的信号强度
        self.GW_RSS = self.getRSS(distance)  # 信号强度
        self.GW_SNR = self.getSNR(distance)  # 信噪比

        # 网关下行信息，需要扩展时自定义 （将网关对节点的下行抽象成对数据包的下行，节点在该数据包上行之后检查下行信息）
        self.ACK = False  # 网关反馈标志位
        self.DownMsg = None

    # 数据包在某个距离时的SNR
    def getSNR(self, distance):
        RSSI = CoverageModule.rss(distance, self.tp)
        SNR = CoverageModule.snr(RSSI)
        return SNR

    def getRSS(self, distance):
        RSSI = CoverageModule.rss(distance, self.tp)
        return RSSI

    @staticmethod
    def PktEnergy(tp, toa):
        dBm = max(min(tp, 17), 2)
        # 3次函数拟合发射功率与电流的对应关系
        p = [0.00339772068746518, 0.148986494020688, 1.25166517120003, 36.2777443411981]
        Current = p[0] * (dBm ^ 3) + p[1] * (dBm ^ 2) + p[2] * dBm + p[3]  # mA
        energy = 3.3 * Current * toa / 1000  # mJ
        return energy

    @staticmethod
    def TimeOnAir(sf, cr, pl, bw):
        TOA = LifetimeModule.TOACalculate(bw, sf, cr, pl)
        return TOA

