import json
import os

import numpy as np
from matplotlib import pyplot as plt

if __name__ == "__main__":
    current_file_dir = os.path.dirname(os.path.abspath(__file__))

    path = "2026-04-15_20-18"
    fpath = os.path.join(current_file_dir, path)
    file = os.path.join(fpath, "data.json")

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 检查并替换键名
    if "DSLoRa-A" in data:
        data["DS-LoRa"] = data.pop("DSLoRa-A")

    # 🔶画图
    # 协议指定颜色
    PROTOCOL_COLORS = {
        'ALOHA': '#1f77b4',  # 蓝色
        'LMAC-1': '#ff7f0e',  # 橙色
        'LMAC-2': '#2ca02c',  # 绿色
        'CSMA-LoRa': '#8c564b',  # 棕色
        'DS-LoRa': '#d62728',  # 红色
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

    # EnergyEfficiency
    fig3 = plt.figure(figsize=(6, 4.5))
    for proto in data:
        plt.plot(data[proto]['nodes'], data[proto]['EnergyEfficiency'], 'o-',
                 color=PROTOCOL_COLORS[proto], label=proto)
    # plt.axvspan(50, 1050, color='lightgray', alpha=0.8, zorder=0)
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
    # plt.axvspan(50, 1050, color='lightgray', alpha=0.8, zorder=0)
    plt.grid(True, alpha=0.4, linestyle="--", color="gray")  # 网格
    plt.xlabel("Node", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.ylabel("Delay Time per Frame (s)", fontdict={'size': 12}, labelpad=10, loc='center')
    plt.legend(loc='upper left')
    plt.tight_layout()

    # fig1.savefig("goodput.svg", dpi=300, bbox_inches="tight", format='svg')
    # fig2.savefig("prr.svg", dpi=400, bbox_inches="tight", format='svg')
    # fig3.savefig("EnergyEfficiency.svg", dpi=400, bbox_inches="tight", format='svg')
    # fig4.savefig("CADsPerFrame.svg", dpi=400, bbox_inches="tight", format='svg')
    # fig5.savefig("DelayTimePerFrame.svg", dpi=400, bbox_inches="tight", format='svg')

    plt.show()  # 显示图片
