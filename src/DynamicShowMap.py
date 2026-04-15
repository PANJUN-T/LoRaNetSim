import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle


def draw_gateway_and_circles(ax, max_r):
    ax.scatter(0, 0, c='red', s=250, marker='*', zorder=5, edgecolors='black', linewidth=2)

    circle_colors = ['#e0f7fa', '#b2ebf2', '#80deea', '#4dd0e1', '#26c6da', '#00bcd4', '#00acc1', '#0097a7',
                     '#00838f', '#006064']
    for i, r in enumerate(range(1000, int(max_r + 500), 1000)):
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


class DynamicShowMap:
    def __init__(self):
        plt.ion()  # 开启交互模式

        # 画布
        self.fig, (self.ax_sf, self.ax_tp) = plt.subplots(
            1, 2, figsize=(12, 6),
            constrained_layout=True  # 保持子图大小一致
        )

        # 为功率分布图创建色条
        vmin, vmax = 2, 20
        tp_cmap = LinearSegmentedColormap.from_list('tp_cmap', ['#1f77b4', '#ff7f0e', '#d62728'])
        sm = plt.cm.ScalarMappable(cmap=tp_cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])

        cbar = self.fig.colorbar(sm, ax=self.ax_tp, shrink=0.8, pad=0.02)
        cbar.set_label('Transmitting power (dBm)', fontsize=12)

    def ShowMap(self, node_map):
        # 刷新左右子图
        self.Disp_SF(node_map, self.ax_sf)
        self.Disp_TP(node_map, self.ax_tp)

        # 全局刷新
        self.fig.canvas.draw()
        plt.pause(0.01)

    def Disp_SF(self, map, ax):
        ax.clear()

        ax.set_title("SF Distribution", fontsize=14)
        plt.rcParams['axes.unicode_minus'] = False
        # SF 颜色映射
        sf_mapping = {
            7: {'label': 'SF7', 'color': '#1f77b4'},
            8: {'label': 'SF8', 'color': '#ff7f0e'},
            9: {'label': 'SF9', 'color': '#2ca02c'},
            10: {'label': 'SF10', 'color': '#e377c2'},
            11: {'label': 'SF11', 'color': '#9467bd'},
            12: {'label': 'SF12', 'color': '#8c564b'}
        }

        # 解析数据
        x_coord, y_coord, sf_values = [], [], []
        for nid, node_info in map.items():
            x_coord.append(node_info["x"])
            y_coord.append(node_info["y"])
            sf_values.append(node_info["sf"])
        max_r = max(info['d'] for info in map.values())

        # 绘制散点
        scatter_handles = []
        for sf in sorted(sf_mapping.keys()):
            sf_mask = np.array(sf_values) == sf  # 按SF分组画图
            if np.any(sf_mask):
                x = np.array(x_coord)[sf_mask]
                y = np.array(y_coord)[sf_mask]
                scatter = ax.scatter(
                    x, y, c=sf_mapping[sf]['color'], s=50, alpha=0.8,
                    edgecolors='black', linewidths=0.5, label=sf_mapping[sf]['label'], zorder=5
                )
                scatter_handles.append(scatter)

        # 网关 + 同心圆
        draw_gateway_and_circles(ax, max_r)

        # 图例
        ax.legend(
            handles=scatter_handles, loc='upper right', bbox_to_anchor=(0.99, 0.99),
            fontsize=10, frameon=True, shadow=True
        )
        ax.set_aspect('equal')
        ax.axis('off')

    def Disp_TP(self, map, ax):
        ax.clear()
        ax.set_title("TP Distribution", fontsize=14)

        # 解析数据
        x_coord, y_coord, tp_values = [], [], []
        for nid, node_info in map.items():
            x_coord.append(node_info["x"])
            y_coord.append(node_info["y"])
            tp_values.append(node_info["tp"])
        max_r = max(info['d'] for info in map.values())

        # 固定配色
        vmin, vmax = 2, 20
        tp_cmap = LinearSegmentedColormap.from_list('tp_cmap', ['#1f77b4', '#ff7f0e', '#d62728'])

        # 绘制散点
        ax.scatter(
            x_coord, y_coord, c=tp_values, cmap=tp_cmap, s=50, alpha=0.8,
            edgecolors='black', linewidths=0.5, zorder=5, vmin=vmin, vmax=vmax
        )

        # 网关 + 同心圆
        draw_gateway_and_circles(ax, max_r)
        ax.set_aspect('equal')
        ax.axis('off')
