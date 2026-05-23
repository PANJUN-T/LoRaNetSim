import json
import matplotlib.pyplot as plt
import numpy as np

# ===================== 基础配置 =====================
Time_List = ["1h", "2h", "4h", "8h"]
SN_List = ["SN1", "SN2", "SN3"]

# 高区分度配色 + 线型 + 标记（完全不重复）
SN_STYLE = {
    'SN1': {'color': '#1f77b4', 'marker': 'o', 'linestyle': '-'},
    'SN2': {'color': '#ff7f0e', 'marker': 's', 'linestyle': '-'},
    'SN3': {'color': '#2ca02c', 'marker': '^', 'linestyle': '-'},
}

# 时间序列专用配色（4个时间 → 4种颜色）
TIME_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

# ===================== 图1：DER =====================
fig1 = plt.figure(figsize=(6.5, 5))
time = Time_List[0]

with open(str(time + r"\PRR_LoRaNetSim.json"), "r", encoding="utf-8") as f:
    DER_LoRaNetSim = json.load(f)


for sn in SN_List:
    style = SN_STYLE[sn]
    # LoRaNetSim：实线 + 实心标记
    plt.plot(DER_LoRaNetSim[sn]['nodes'], DER_LoRaNetSim[sn]['prr'],
             marker=style['marker'], linestyle=style['linestyle'],
             color=style['color'], linewidth=2, markersize=7,
             label=f"{sn}-LoRaNetSim")




# 图表美化
plt.grid(True, alpha=0.4, linestyle="--", color="gray")
plt.xlabel("Node", fontsize=12)
plt.ylabel("PRR", fontsize=12)
plt.legend(loc=(0.37, 0.16), fontsize=10, ncol=2)
plt.tight_layout()

# ===================== 图2：Run Time (误差棒) =====================
fig2 = plt.figure(figsize=(6.5, 5))
TARGET_SN = "SN2"

for idx, time in enumerate(Time_List):
    color = TIME_COLORS[idx]

    with open(str(time + r"\TIME_LoRaNetSim.json"), "r", encoding="utf-8") as f:
        Time_LoRaNetSim = json.load(f)


    nodes = Time_LoRaNetSim[TARGET_SN]['nodes']

    # LoRaNetSim：圆圈 + 实线
    data = Time_LoRaNetSim[TARGET_SN]
    times_list = np.array(data["times_list"])
    mean_NetSim = np.mean(times_list, axis=0)
    std_NetSim = np.std(times_list, axis=0)
    plt.errorbar(nodes, mean_NetSim, yerr=std_NetSim,
                 linestyle='-', marker='o', capsize=5, capthick=2,
                 color=color, linewidth=2, markersize=7,
                 label=f"{time}-LoRaNetSim")



plt.grid(True, alpha=0.4, linestyle="--")
plt.xlabel("Number of Nodes", fontsize=12)
plt.ylabel("Run Time (s)", fontsize=12)
plt.legend(loc="upper left", fontsize=10, ncol=2)
plt.tight_layout()

plt.show()


