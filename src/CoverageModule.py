import math
import os

import numpy as np
from matplotlib import pyplot as plt



class CoverageModule:
    # SF7~SF12 对应的接收灵敏度 (125KHz带宽, dBm)
    sensi = list(np.array([-126.5, -128.75, -131.25, -132.75, -134.5, -135.25]))
    SNR_Req = list(np.array([-7.5, -10, -12.5, -15, -17.5, -20]))

    # 对数路径损耗模型相关参数
    gamma = 2.32  # 路径损耗指数
    d0 = 1000.0  # 参考距离 (m)
    Lpld0 = 128.95  # 参考距离路径损耗 (dB)
    GL = 0  # 增益 (dB)
    std = 0  # 路径损耗标准差 (dB)

    # 计算PRR时的重复实验次数
    REPETITION_NUM = 1

    # 路径损耗模型选择
    MODULE = "Log"  # "Okumura"

    @classmethod
    def rss(cls, distance, tp):
        if distance == 0:
            return tp

        # 对数路径损耗模型
        if cls.MODULE == "Log":
            Lpl = cls.Lpld0 + 10 * cls.gamma * np.log10(distance / cls.d0) + np.random.normal(0, cls.std)
        elif cls.MODULE == "Okumura":
            # TODO 奥村模型
            pass
        Prx = tp + cls.GL - Lpl
        return Prx

    @classmethod
    def snr(cls, rss):
        # 噪声底噪计算 (125KHz带宽)
        noise_floor = -174 + 10 * np.log10(125e3)  # 热噪声底噪 (dBm)
        return rss - noise_floor

    @classmethod
    def getCoverage(cls, sf, tp):
        left = 1  # 下界
        right = 20000  # 上界
        precision = 1  # 距离精度
        coverage = 0
        while right - left > precision:  # 二分法迭代求解
            mid = (left + right) / 2
            rss = cls.rss(mid, tp)
            # 满足灵敏度要求
            if rss >= cls.sensi[sf - 7]:
                coverage = mid
                left = mid
            else:
                right = mid

        return coverage

    @classmethod
    def getPRR(cls, sf, tp, distance):
        target_sensi = cls.sensi[sf - 7]

        success_count = 0
        for _ in range(cls.REPETITION_NUM):
            current_rssi = cls.rss(distance, tp)
            current_snr = cls.snr(current_rssi)
            # 同时满足灵敏度和SNR要求则收包成功
            if current_rssi >= target_sensi:
                success_count += 1
        # 计算收包率（百分比）
        prr = (success_count / cls.REPETITION_NUM) * 100
        return prr

    @classmethod
    def plot_rss(cls):
        tp = 12
        # 生成距离数组（线性分布）
        Distances = list(np.linspace(10, 10000, 1000))
        RSS_all = []
        RSS_mean = []
        for d in Distances:
            # 计算无阴影衰落的理论路径损耗
            Lpl = cls.Lpld0 + 10 * cls.gamma * np.log10(d / cls.d0)
            rss_mean_val = tp + cls.GL - Lpl
            RSS_mean.append(rss_mean_val)

            # 生成带阴影衰落的路径损耗（n_sim次仿真）
            shadow_fading = np.random.normal(0, cls.std, 50)  # 对数正态分布阴影衰落
            pl_sim = rss_mean_val + shadow_fading  # 阴影衰落叠加（损耗增加）
            RSS_all.append(pl_sim)
        RSS_all = np.array(RSS_all)

        plt.figure(figsize=(6, 4))
        # 阴影衰落
        for idx, d in enumerate(Distances):
            plt.plot([d / 1000] * 50, RSS_all[idx], color='b')
        # 绘制均值曲线
        plt.plot([d / 1000 for d in Distances], RSS_mean, color='darkred', linewidth=2, label='Mean RSS')
        # 灵敏度阈值
        plt.axhline(y=cls.sensi[-1], linestyle='--', linewidth=2, label='GW sensitivity')
        # CAD阈值
        # plt.axhline(y=cls.sensi[-1], linestyle='--', linewidth=2, label='GW sensitivity')

        plt.xlabel('distance (km)', fontsize=12)
        plt.ylabel('RSS (dBm)', fontsize=12)
        plt.legend(loc='upper right', fontsize=11)

        plt.tight_layout()  # 紧凑布局


if __name__ == "__main__":

    # 添加阴影衰落
    CoverageModule.std = 1.5
    CoverageModule.REPETITION_NUM = 500

    for i in range(6):
        sf = 7 + i
        tp = 15
        dist = CoverageModule.getCoverage(30000, sf, tp)
        print("({}, {}): {}米".format(sf, tp, dist))

    print("最远传输距离：{}米".format(CoverageModule.getCoverage(30000, 12, 20)))

    tp = 15
    prrData = dict()
    for sf in [7, 8, 9, 10, 11, 12]:
        for d in range(50, 15000, 100):
            prr = CoverageModule.getPRR(sf, tp, d)
            prrData[(sf, d)] = prr
    fig1 = plt.figure(figsize=(6, 4))
    for sf in [7, 8, 9, 10, 11, 12]:
        dists = range(50, 15000, 100)
        prr = [prrData[(sf, d)] for d in dists]
        plt.plot([d / 1000 for d in dists], [p / 100 for p in prr], 'o-', label=f"SF={sf}")

    # 图表样式
    plt.xlabel("Distance (km)", fontsize=12, labelpad=10)
    plt.ylabel("PRR", fontsize=12, labelpad=10)
    plt.legend(loc='upper right', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # RSS
    CoverageModule.plot_rss()
    plt.show()
