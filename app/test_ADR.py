from datetime import datetime
from multiprocessing import Process
from multiprocessing import Manager

import json

from collections import defaultdict
import os

from src import GlobalCfg as GCfg
from src.Simulator import LoRaSimulationEnv
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # 全局参数配置
    cfg = {
        "new_SimulationDuration": 60000 * 60 * 1,    # 仿真时间 小时
        "new_lamuda": 0.1,                           # 泊松分布λ
        "new_ADR": True,                             # ADR
        "new_SimModule": "ADR",                      # 仿真模式
        "new_Actual_CADe": False,                    # 实测CAD效率 or 100%可靠性
        "new_AutoSaveResult": False                  # 自动保存结果
    }
    GCfg.GlobalConfig(**cfg)
    # 仿真参数
    NodeNum = 100                             # 节点数量
    LoRaMac = GCfg.LoRaMAC.ALOHA              # MAC协议
    NodeMap = GCfg.ParameterOptimization.ADR  # 初始参数分配方法/节点分布
    # 启动仿真
    LoRaSim = LoRaSimulationEnv(NodeNum, LoRaMac, GCfg.ParameterOptimization.ADR)
    LoRaSim.run()
    # LoRaSim.Show_Results()
