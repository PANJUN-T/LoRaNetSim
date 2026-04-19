import numpy as np
from enum import Enum
from typing import Dict, Tuple, Deque

# 🔸仿真时间
SimulationDuration = 60000 * 5  # 分钟
STATISTICS_INTERVAL = 60000 * 1  # 时间轴统计方式，1分钟统计一次

# 🔸泊松部分的数据包发送间隔
lamuda = 0.1

# 🔸定义仿真模式，便于批量修改仿真配置
# "MAC" : 信道接入协议仿真模式
# "ADR" : ADR仿真
# "Dynamic" : 动态网络仿真
# "Parameter" : 参数分配仿真
# "SN" : 仿真器性能仿真
SimModule = "Parameter"

# 🔸ADR功能
ADR = False


# 🔸自动保存测试结果
AutoSaveResult = False


# 🔸参数分配方法
class ParameterOptimization(Enum):
    Equidistant = "Equidistant"
    minTOA = "minTOA"
    ADR = "ADR"


# 🔸MAC协议选择
class LoRaMAC(Enum):
    ALOHA = "ALOHA"
    LMAC1 = "LMAC-1"
    LMAC2 = "LMAC-2"
    # CSMALoRa = "CSMA-LoRa"



# 🔸默认通信参数设置
class LoRaParameter:  # 默认数据包参数
    BW = 125
    CR = 1
    PL = 16  # 负载长度

    CH = 867100000
    SF = 7
    TP = 2

    SF_List = np.array([7, 8, 9, 10, 11, 12])
    CH_List = np.array([867100000, 867300000, 867500000, 867700000,
                        867900000, 868100000, 868300000, 868500000])
    TP_List = range(2, 21, 1)


# 🔸实测CAD效率
Actual_CADe = False  # Ture: 考虑CAD效率   False: 不考虑CAD效率


def sigmoid(x, a, b):
    return 1 / (1 + np.exp(-a * (x - b)))


# CAD效率与SNR拟合参数
CADe = [
    [0.83964361, -4.93300226],
    [0.79662497, -6.27272314],
    [0.82716479, -9.50598839],
    [0.91493329, -10.81475066],
    [0.99208078, -13.49842746],
    [0.88208809, -15.68983581]]

# 🔸各SF使用的节点数，DS-LoRa需要
SFNodes = dict()
for l_sf in LoRaParameter.SF_List:
    SFNodes[int(l_sf)] = 0


# 暂时不用
class EnergyParameter:
    BatterySize = 3000  # mAh
    NodeDutyCycle = 0.01


def GlobalConfig(
        new_SimulationDuration=None,
        new_lamuda=None,
        new_ADR=None,
        new_AorD=None,
        new_AutoSaveResult=None,
        new_Actual_CADe=None,
        new_SimModule=None,
):
    global SimulationDuration, lamuda
    global ADR, AutoSaveResult, Actual_CADe, SimModule

    if new_SimulationDuration is not None:
        SimulationDuration = new_SimulationDuration
    if new_lamuda is not None:
        lamuda = new_lamuda
    if new_ADR is not None:
        ADR = new_ADR
    if new_AutoSaveResult is not None:
        AutoSaveResult = new_AutoSaveResult
    if new_Actual_CADe is not None:
        Actual_CADe = new_Actual_CADe
    if new_SimModule is not None:
        SimModule = new_SimModule


# 仿真器性能测试相关配置 {tp,cf,sf,bw,cr,pl}
SN = {"SN1": [14, 868000000, 12, 125, 1, 20],
      "SN2": [14, 868000000, 9, 125, 1, 20],
      "SN3": [14, 868000000, 7, 125, 1, 20],
      }
SN_idx = None
