import os
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Manager

import json
import matplotlib.pyplot as plt
import numpy as np

from src import GlobalCfg as GCfg
from src.NodeMap import NodeMap
from src.Simulator import LoRaSimulationEnv

from collections import defaultdict


def show_result(prr, goodput):
    # 生成X轴数据
    data_points = len(prr)
    x = np.arange(0.5, data_points * 0.5 + 0.1, 0.5)  # 从0.5开始，步长0.5

    fig1, ax1 = plt.subplots(figsize=(6, 4))
    # 左轴：PRR
    color_prr = '#F18F01'
    line_prr = ax1.plot(x, prr, 'o-', linewidth=2.5, markersize=8,
                        color=color_prr, label='PRR')

    ax1.set_xlabel('Time (min)', fontsize=12)
    ax1.set_ylabel('PRR', fontsize=12, color=color_prr)
    # ax1.set_xticks(x)
    ax1.tick_params(axis='y', labelcolor=color_prr)
    ax1.set_ylim(0, 1.1)  # PRR范围0-1.1，突出微小波动
    # ax1.grid(True, alpha=0.5)

    # 右轴：Goodput
    ax2 = ax1.twinx()
    color_throughput = '#A23B72'
    line_throughput = ax2.plot(x, goodput, 's-', linewidth=2.5, markersize=8,
                               color=color_throughput, label='Goodput')
    ax2.set_ylabel('Goodput (B/s)', fontsize=12, color=color_throughput, fontweight='medium')
    ax2.tick_params(axis='y', labelcolor=color_throughput)
    if goodput:
        min_gp, max_gp = min(goodput), max(goodput)
        margin = (max_gp - min_gp) * 0.05 if max_gp != min_gp else 1
        ax2.set_ylim(min_gp - margin, max_gp + margin)

    # 合并图例
    lines = line_prr + line_throughput
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='best', fontsize=12)

    plt.tight_layout()

    res_folder = "DynamicNet_Result"
    os.makedirs(res_folder, exist_ok=True)
    fig1.savefig(str(res_folder + r"\PRR&goodput.svg"), dpi=300, bbox_inches="tight", format='svg')


if __name__ == "__main__":
    # 全局参数配置
    GCfg.GlobalConfig(
        new_SimulationDuration=60000 * 20,  # 仿真时间 分钟
        new_lamuda=0.2,  # 泊松分布λ
        new_ADR=False,  # ADR
        new_SimModule="Dynamic",  # 仿真模式
        new_Actual_CADe=False,  # 实测CAD效率 or 100%可靠性
        new_AutoSaveResult=True  # 自动保存结果
    )

    # 仿真参数
    NodeNum = 10                                 # 节点数量
    LoRaMac = GCfg.LoRaMAC.ALOHA                 # MAC协议
    NodeMap = GCfg.ParameterOptimization.minTOA  # 初始参数分配方法/节点分布
    # 启动仿真
    LoRaSim = LoRaSimulationEnv(NodeNum, LoRaMac, NodeMap)
    LoRaSim.run()
    # 可视化结果
    show_result(LoRaSim.temp_PRR, LoRaSim.temp_Goodput)
    plt.show()
