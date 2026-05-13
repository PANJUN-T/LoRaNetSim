from datetime import datetime
from multiprocessing import Process
from multiprocessing import Manager

import json
import matplotlib.pyplot as plt

from collections import defaultdict
import os

# from src.GlobalCfg import *
from ctrl import GlobalCfg as GCfg
from ctrl.Simulator import LoRaSimulationEnv


def show_result(res_dict):
    # 🔶 数据预处理：
    # 按协议分组并排序
    data = defaultdict(lambda: {'nodes': [], 'throughput': [], 'prr': []})
    for ((protocol, node_count), (throughput, prr)) in res_dict.items():  # 填充数据
        data[protocol]['nodes'].append(node_count)
        data[protocol]['throughput'].append(throughput)
        data[protocol]['prr'].append(prr)

    for proto in data:  # 排序
        sorted_data = sorted(zip(
            data[proto]['nodes'],
            data[proto]['throughput'],
            data[proto]['prr'],
        ))
        nodes, throughput, prr = zip(*sorted_data)
        data[proto]['nodes'] = list(nodes)
        data[proto]['throughput'] = list(throughput)
        data[proto]['prr'] = list(prr)

    # 🔶画图
    # 协议指定颜色
    PROTOCOL_COLORS = {
        'Equidistant': '#1f77b4',  # 蓝色
        'minTOA': '#ff7f0e',  # 橙色
        'minConflict': '#2ca02c',  # 绿色
    }

    # 吞吐量
    fig1 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], data[proto]['throughput'], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
    # plt.axvspan(50, 1050, color='lightgray', alpha=0.8, zorder=0)
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("Goodput (B/s)", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend()
    plt.tight_layout()

    # prr
    fig2 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], data[proto]['prr'], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
    # plt.axvspan(50, 1050, color='lightgray', alpha=0.8, zorder=0)
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("PRR", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend()
    plt.tight_layout()

    if GCfg.AutoSaveResult:
        res_folder = "Parameter_Result"
        date_folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
        date_folder_path = os.path.join(res_folder, date_folder_name)
        os.makedirs(date_folder_path, exist_ok=True)

        # 保存原始数据
        with open(date_folder_path + r"\parameter_test_dataset.json", "w", encoding="utf-8") as f:  # 保存原始数据
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()  # 清空Python级别的缓冲区
            os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘

        fig1.savefig(date_folder_path + r"\parameter_goodput.svg", dpi=300, bbox_inches="tight", format='svg')
        fig2.savefig(date_folder_path + r"\parameter_prr.svg", dpi=400, bbox_inches="tight", format='svg')

    plt.show()  # 显示图片


def func(mac, nNode, optimization, r_dict, cfg):
    # 多进程相互独立，也需要更新全局参数
    GCfg.GlobalConfig(**cfg)

    # 可自定义参数：节点数、仿真时长
    LoRaSim = LoRaSimulationEnv(nNode, mac, optimization)
    LoRaSim.run()

    # 结果
    dict_key = (optimization.value, nNode)
    r_dict[dict_key] = [float(LoRaSim.Goodput), float(LoRaSim.PRR)]


if __name__ == "__main__":
    # 全局变量配置
    cfg = {
        "new_SimulationDuration": 60000 * 5,  # 仿真时间 分钟
        "new_lamuda": 0.1,                    # 泊松分布λ
        "new_ADR": False,                     # ADR
        "new_SimModule": "Parameter",         # 仿真模式
        "new_Actual_CADe": False,             # 实测CAD效率 or 100%可靠性
        "new_AutoSaveResult": True           # 自动保存结果
    }
    GCfg.GlobalConfig(**cfg)

    process_list = []  # 进程池
    manager = Manager()  # ？
    result_dict = manager.dict()

    LoRaMAC = GCfg.LoRaMAC.ALOHA
    num_list = range(50, 1500, 100)
    for NodeMap in [o for o in GCfg.ParameterOptimization if o != GCfg.ParameterOptimization.ADR]:
        print("参数分配方法：{}".format(NodeMap.value))
        for NodeNum in num_list:
            p = Process(target=func, args=(LoRaMAC, NodeNum, NodeMap, result_dict, cfg))
            p.start()
            process_list.append(p)

        for i in process_list:
            i.join()

    show_result(result_dict)
    print('end')
