import json
import math
import os
import random

import numpy as np
from matplotlib.patches import Circle
from matplotlib.colors import LinearSegmentedColormap
from src.ParameterAllocation import ParamAlloc

from ctrl import GlobalCfg as GCfg
import matplotlib.pyplot as plt


def draw_gateway_and_circles(ax, max_r):
    ax.scatter(0, 0, c='red', s=250, marker='*', zorder=5, edgecolors='black', linewidth=2)

    circle_colors = ['#e0f7fa', '#b2ebf2', '#80deea', '#4dd0e1', '#26c6da', '#00bcd4', '#00acc1', '#0097a7',
                     '#00838f', '#006064']
    for i, r in enumerate(range(1000, int(max_r + 100), 1000)):
        color = circle_colors[i % len(circle_colors)]
        fill_circle = Circle((0, 0), r, color=color, alpha=0.1, fill=True)
        ax.add_patch(fill_circle)
        border_circle = Circle((0, 0), r, color='gray', zorder=5, fill=False, linewidth=1.2)
        ax.add_patch(border_circle)
        ax.text(
            r, 0, f"{r // 1000}km",
            ha='left', va='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'),
            zorder=5
        )


class NodeMap:
    DEFAULT_RADIUS = 8000  # 网络半径
    DEFAULT_NODE_NUM = 3500  # 最大节点数
    DEFAULT_METHOD = GCfg.ParameterOptimization  # 参数分配方法

    @classmethod
    def CreateMaxMap(cls):
        # 目录
        folder = "Nodes"
        PyFileDir = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(PyFileDir, folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # 按照不同参数分配方法创建节点分布
        for optimization in cls.DEFAULT_METHOD:
            # 一般分配方法
            MapData = dict()
            for nid in range(1, cls.DEFAULT_NODE_NUM + 1):
                # 随机R 平方根采样保证均匀分布
                r = cls.DEFAULT_RADIUS * math.sqrt(random.uniform(0, 1))
                theta = random.uniform(0, 2 * math.pi)
                # 极坐标转直角坐标
                x = r * math.cos(theta)
                y = r * math.sin(theta)
                margin = 0  # 传输距离的余量
                bp = ParamAlloc.findBestParam(cls.DEFAULT_RADIUS, r + margin, optimization.value)

                [bp_sf, bp_tp] = bp
                MapData[nid] = {
                    "x": x,
                    "y": y,
                    "distance": r,
                    "sf": int(bp_sf),
                    "tp": int(bp_tp),
                }
                print("debug: ID：{}, x:{:.0f}, y:{:.0f}, r:{:.0f}米, 参数:(SF{} {}dBm), 优化方案:{}"
                      .format(nid, x, y, r, bp_sf, bp_tp, optimization.value))
            # 保存
            fstr = str(cls.DEFAULT_NODE_NUM) + "-Nodes-" + str(cls.DEFAULT_RADIUS) + "m-" + optimization.value + ".json"
            FilePath = os.path.join(folder, fstr)
            with open(FilePath, "w", encoding="utf-8") as f:
                json.dump(MapData, f, ensure_ascii=False, indent=4)
                # 立即将数据写入磁盘
                f.flush()  # 清空Python级别的缓冲区
                os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘

    @classmethod
    def RandomChoice(cls, nNode, OptimizationType):
        data = NodeMap.ReadMap(cls.DEFAULT_NODE_NUM, OptimizationType)  # 读取最高节点数量的map
        randomChoice = random.sample(list(data.values()), nNode)
        new_map = {i + 1: randomChoice[i] for i in range(nNode)}  # 新字典，键从1开始
        return new_map

    @classmethod
    def GetNodeMap(cls, nNode, OptimizationType):
        # 读取节点map， 如果map文件存在，则从文件读取；如果map文件不存在，则从默认map中随机选取所需要的节点数量
        folder = "Nodes"
        fstr = str(nNode) + "-Nodes-" + str(NodeMap.DEFAULT_RADIUS) + "m-" + OptimizationType + ".json"
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_file_dir, folder, fstr)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                node_map = json.load(f)  # 读取节点分布
        else:
            # 随机选取
            node_map = cls.RandomChoice(nNode, OptimizationType)
            # 立即保存
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(node_map, f, ensure_ascii=False, indent=4)
                f.flush()  # 清空Python级别的缓冲区
                os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘
        return node_map

    @classmethod
    def ReadMap(cls, nNode, OptimizationType):
        folder = "Nodes"
        fstr = str(nNode) + "-Nodes-" + str(cls.DEFAULT_RADIUS) + "m-" + OptimizationType + ".json"
        PyFileDir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(PyFileDir, folder, fstr)

        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                Map = json.load(f)
            return Map
        else:
            raise ValueError("文件“{}”不存在！".format(fstr))

    @classmethod
    def showMap(cls, Map):
        # 画布
        fig, (ax_sf, ax_tp) = plt.subplots(1, 2, figsize=(12, 6), constrained_layout=True)  # 保持子图大小一致
        # 为功率分布图创建固定色条
        vmin, vmax = min(GCfg.LoRaParameter.TP_List), max(GCfg.LoRaParameter.TP_List)
        tp_cmap = LinearSegmentedColormap.from_list('tp_cmap', ['#1f77b4', '#ff7f0e', '#d62728'])
        sm = plt.cm.ScalarMappable(cmap=tp_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax_tp, shrink=0.8, pad=0.02)
        cbar.set_label('Transmitting power (dBm)', fontsize=12)

        # 解析数据
        x_coord, y_coord, sf_values, tp_values = [], [], [], []
        for nid, node_info in Map.items():
            x_coord.append(node_info["x"])
            y_coord.append(node_info["y"])
            sf_values.append(node_info["sf"])
            tp_values.append(node_info["tp"])
        max_r = max(info['distance'] for info in Map.values())

        # SF
        sf_mapping = {
            7: {'label': 'SF7', 'color': '#1f77b4'},
            8: {'label': 'SF8', 'color': '#ff7f0e'},
            9: {'label': 'SF9', 'color': '#2ca02c'},
            10: {'label': 'SF10', 'color': '#e377c2'},
            11: {'label': 'SF11', 'color': '#9467bd'},
            12: {'label': 'SF12', 'color': '#8c564b'}
        }

        # 绘制散点
        scatter_handles = []
        for sf in sorted(sf_mapping.keys()):
            sf_mask = np.array(sf_values) == sf  # 按SF分组画图
            if np.any(sf_mask):
                x = np.array(x_coord)[sf_mask]
                y = np.array(y_coord)[sf_mask]
                scatter = ax_sf.scatter(
                    x, y, c=sf_mapping[sf]['color'], s=50, alpha=0.8,
                    edgecolors='black', linewidths=0.5, label=sf_mapping[sf]['label'], zorder=5
                )
                scatter_handles.append(scatter)
        # 图例
        ax_sf.legend(
            handles=scatter_handles, loc='upper right', bbox_to_anchor=(0.99, 0.99),
            fontsize=10, frameon=True, shadow=True
        )

        # TP
        ax_tp.scatter(
            x_coord, y_coord, c=tp_values, cmap=tp_cmap, s=50, alpha=0.8,
            edgecolors='black', linewidths=0.5, zorder=5, vmin=vmin, vmax=vmax
        )

        # 网关 + 同心圆
        draw_gateway_and_circles(ax_tp, max_r)
        draw_gateway_and_circles(ax_sf, max_r)

        ax_sf.set_aspect('equal')
        ax_sf.axis('off')
        ax_tp.set_aspect('equal')
        ax_tp.axis('off')


if __name__ == "__main__":
    # 生成map
    # 目录
    folder = "Nodes"
    PyFileDir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(PyFileDir, folder)
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 删除原有文件
    print("正在删除“{}”文件夹下原有节点分布文件".format(folder))
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print("已删除：{}".format(file_path))
        except Exception as e:
            print(f"删除失败: {file_path}, 错误: {e}")
    # 创建预分配参数的节点分布
    NodeMap.CreateMaxMap()

    # 显示map
    n = 3500
    o = "minTOA"  # "Equidistant"  "minTOA"  "ADR"
    MAP = NodeMap.GetNodeMap(n, o)

    NodeMap.showMap(MAP)
    plt.show()
