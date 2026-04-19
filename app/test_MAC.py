import json
from multiprocessing import Process
from multiprocessing import Manager
import matplotlib.pyplot as plt
import numpy as np

from src import GlobalCfg as GCfg
from src.Simulator import LoRaSimulationEnv

from collections import defaultdict
import os
from datetime import datetime


def show_result(res_dict):
    # 🔶 数据预处理：
    # 按协议分组并排序
    data = defaultdict(lambda: {'nodes': [], 'throughput': [], 'prr': [],
                                'EnergyEfficiency': [], 'CADsPerFrame': [],
                                'DelayTimePerFrame': []})
    for ((protocol, node_count),
         (throughput, prr, EnergyEfficiency, CADsPerFrame, DelayTimePerFrame)) in res_dict.items():  # 填充数据
        data[protocol]['nodes'].append(node_count)
        data[protocol]['throughput'].append(throughput)
        data[protocol]['prr'].append(prr)
        data[protocol]['EnergyEfficiency'].append(EnergyEfficiency)
        data[protocol]['CADsPerFrame'].append(CADsPerFrame)
        data[protocol]['DelayTimePerFrame'].append(DelayTimePerFrame)

    for proto in data:  # 排序
        sorted_data = sorted(zip(
            data[proto]['nodes'],
            data[proto]['throughput'],
            data[proto]['prr'],
            data[proto]['EnergyEfficiency'],
            data[proto]['CADsPerFrame'],
            data[proto]['DelayTimePerFrame']
        ))
        nodes, throughput, prr, EnergyEfficiency, CADsPerFrame, DelayTimePerFrame = zip(*sorted_data)
        data[proto]['nodes'] = list(nodes)
        data[proto]['throughput'] = list(throughput)
        data[proto]['prr'] = list(prr)
        data[proto]['EnergyEfficiency'] = list(EnergyEfficiency)
        data[proto]['CADsPerFrame'] = list(CADsPerFrame)
        data[proto]['DelayTimePerFrame'] = list(DelayTimePerFrame)

    # 🔶画图
    # 协议指定颜色
    PROTOCOL_COLORS = {
        'ALOHA': '#1f77b4',  # 蓝色
        'LMAC-1': '#ff7f0e',  # 橙色
        'LMAC-2': '#2ca02c',  # 绿色
        'CSMA-LoRa': '#8c564b',  # 棕色
    }

    # 吞吐量
    fig1 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], data[proto]['throughput'], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
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
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("PRR", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend()
    plt.tight_layout()

    # EnergyEfficiency
    fig3 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], data[proto]['EnergyEfficiency'], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("Energy Efficiency", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend()
    plt.tight_layout()

    # CADsPerFrame
    fig4 = plt.figure(figsize=(9, 5))
    filtered_data = {k: v for k, v in data.items() if k != 'ALOHA'}
    proto_count = len(filtered_data)  # 参与绘图的协议数量
    first_proto_nodes = next(iter(filtered_data.values()))['nodes']  # 取第一个协议的节点列表
    node_count = len(first_proto_nodes)  # 节点数量
    node_spacing = np.mean(np.diff(first_proto_nodes))  # 节点间的平均间距
    # 自适应柱宽：节点间距 / (协议数 * 1.2) → 1.2 是预留的间隙比例（可调整）
    bar_width = node_spacing / (proto_count * 1.2)
    # 限制柱宽范围（避免过宽/过窄）
    bar_width = max(0.5, min(bar_width, node_spacing * 0.8))  # 最小0.5，最大为节点间距的80%

    x_ticks = []  # 存储最终的X轴刻度位置
    x_tick_labels = []  # 存储X轴刻度标签
    for idx, proto in enumerate(filtered_data.keys()):
        nodes = filtered_data[proto]['nodes']
        # 计算每个协议的柱子偏移：节点位置 + (idx - 协议数/2) * 柱宽 → 让同节点的柱子居中
        x_offset = [pos + (idx - proto_count / 2) * bar_width for pos in nodes]
        plt.bar(x_offset, filtered_data[proto]['CADsPerFrame'],
                width=bar_width, label=proto, color=PROTOCOL_COLORS[proto], edgecolor='white')
        # 记录X轴刻度（仅在第一个协议时记录，保证刻度居中）
        if idx == 0:
            x_ticks = nodes
            x_tick_labels = [str(n) for n in nodes]

    # 设置X轴刻度（修正偏移后的刻度显示）
    plt.xticks(x_ticks, x_tick_labels, fontsize=12)
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("Average Number of CAD per Frame", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.tight_layout()
    plt.legend()

    # DelayTimePerFrame
    fig5 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], [d / 1000 for d in data[proto]['DelayTimePerFrame']], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("Delay Time per Frame (s)", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend(loc='upper left')
    plt.tight_layout()

    # 🔶保存数据
    if GCfg.AutoSaveResult:
        res_folder = "MAC_Result"
        date_folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M")
        date_folder_path = os.path.join(res_folder, date_folder_name)
        os.makedirs(date_folder_path, exist_ok=True)

        # 保存原始数据
        with open(str(date_folder_path + r"\data.json"), "w", encoding="utf-8") as f:  # 保存原始数据
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()  # 清空Python级别的缓冲区
            os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘

        # 保存图片
        fig1.savefig(date_folder_path + r"\goodput.png", dpi=400, bbox_inches="tight")
        fig2.savefig(date_folder_path + r"\prr.png", dpi=400, bbox_inches="tight")
        fig3.savefig(date_folder_path + r"\EnergyEfficiency.png", dpi=400, bbox_inches="tight")
        fig4.savefig(date_folder_path + r"\CADsPerFrame.png", dpi=400, bbox_inches="tight")
        fig5.savefig(date_folder_path + r"\DelayTimePerFrame.png", dpi=400, bbox_inches="tight")
        # svg
        fig1.savefig(date_folder_path + r"\goodput.svg", dpi=300, bbox_inches="tight", format='svg')
        fig2.savefig(date_folder_path + r"\prr.svg", dpi=400, bbox_inches="tight", format='svg')
        fig3.savefig(date_folder_path + r"\EnergyEfficiency.svg", dpi=400, bbox_inches="tight", format='svg')
        fig4.savefig(date_folder_path + r"\CADsPerFrame.svg", dpi=400, bbox_inches="tight", format='svg')
        fig5.savefig(date_folder_path + r"\DelayTimePerFrame.svg", dpi=400, bbox_inches="tight", format='svg')


def CDFtest(nNode):
    # 全局参数配置
    cfg = {
        "new_SimulationDuration": 60000 * 2,  # 仿真时间 分钟
        "new_lamuda": 0.1,  # 泊松分布λ
        "new_ADR": False,  # ADR
        "new_SimModule": "MAC",  # 仿真模式
        "new_Actual_CADe": False,  # 实测CAD效率 or 100%可靠性
        "new_AutoSaveResult": True  # 自动保存结果
    }
    GCfg.GlobalConfig(**cfg)

    # 单次测试, 评估PRR分布特性
    result = defaultdict(dict)
    for LoRaMAC in GCfg.LoRaMAC:
        LoRaSim = LoRaSimulationEnv(nNode, LoRaMAC, GCfg.ParameterOptimization.minTOA)
        LoRaSim.run()
        result[LoRaMAC.value] = {"PRRs": LoRaSim.PRRs}
    # 不同协议下的PRR分布CDF对比图
    fig1 = plt.figure(figsize=(8, 5))
    # 协议固定配色
    PROTOCOL_COLORS = {
        'ALOHA': '#1f77b4',  # 蓝色
        'LMAC-1': '#ff7f0e',  # 橙色
        'LMAC-2': '#2ca02c',  # 绿色
        'CSMA-LoRa': '#8c564b',  # 棕色
    }

    for mac_name, data in result.items():
        prrs = np.sort(data["PRRs"])
        cdf = np.arange(1, len(prrs) + 1) / len(prrs)
        # 从字典取对应协议颜色，无匹配则用灰色
        color = PROTOCOL_COLORS.get(mac_name, '#7f7f7f')
        plt.plot(prrs, cdf, linewidth=2.5, color=color, label=mac_name)

    plt.grid(True, alpha=0.5)
    plt.legend(fontsize=12)
    plt.xlabel("PRR", fontsize=12)
    plt.ylabel("CDF", fontsize=12)
    plt.tight_layout()


    # 🔶保存数据
    if GCfg.AutoSaveResult:
        res_folder = "MAC_Result"
        os.makedirs(res_folder, exist_ok=True)
        # 保存原始数据
        with open(str(res_folder + r"\prr-cdf-{}.json".format(nNode)), "w", encoding="utf-8") as f:  # 保存原始数据
            json.dump(result, f, ensure_ascii=False, indent=4)
            f.flush()  # 清空Python级别的缓冲区
            os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘

        # 保存图片
        fig1.savefig(res_folder + r"\prr-cdf-{}.svg".format(nNode), dpi=400, bbox_inches="tight", format='svg')

    plt.show()


def func(mac, nNode, optimization, r_dict, cfg):
    # 多进程相互独立，也需要更新全局参数
    GCfg.GlobalConfig(**cfg)

    # 可自定义参数：节点数、仿真时长
    LoRaSim = LoRaSimulationEnv(nNode, mac, optimization)
    LoRaSim.run()

    # 结果
    dict_key = (mac.value, nNode)
    r_dict[dict_key] = [float(LoRaSim.Goodput), float(LoRaSim.PRR),
                        float(LoRaSim.EnergyEfficiency), int(LoRaSim.CADsPerFrame),
                        int(LoRaSim.DelayTimePerFrame)]


if __name__ == "__main__":
    # 全局参数配置
    cfg = {
        "new_SimulationDuration": 60000 * 2,  # 仿真时间 分钟
        "new_lamuda": 0.1,  # 泊松分布λ
        "new_ADR": False,  # ADR
        "new_SimModule": "MAC",  # 仿真模式
        "new_Actual_CADe": False,  # 实测CAD效率 or 100%可靠性
        "new_AutoSaveResult": True  # 自动保存结果
    }
    GCfg.GlobalConfig(**cfg)

    # 单次测试, 评估PRR分布特性
    # CDFtest(1000)

    # 批量测试例程
    process_list = []  # 进程池
    manager = Manager()  # ？
    result_dict = manager.dict()
    NodeMap = GCfg.ParameterOptimization.minTOA  # 初始参数分配方法/节点分布
    num_list = range(50, 3300, 250)
    for LoRaMAC in GCfg.LoRaMAC:
        for NodeNum in num_list:
            p = Process(target=func, args=(LoRaMAC, NodeNum, NodeMap, result_dict, cfg))
            p.start()
            process_list.append(p)

        for i in process_list:
            i.join()
    # 可视化结果
    show_result(result_dict)
    plt.show()  # 显示图片
    print('end')
