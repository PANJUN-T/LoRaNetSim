import math


class LifetimeModule:
    __RESTYPE_PARAMS = {"Y", "D", "H"}
    @classmethod
    def getLifetime(cls, bw, cr, sf, tx_power, n_Payload, battery, dutycycle, resType):
        if resType not in cls.__RESTYPE_PARAMS:
            raise ValueError(f"寿命单位可选：{cls.__RESTYPE_PARAMS}，而不是：{resType}")
        # 计算电池总能量 (mAh * V * 3600 → mJ)
        Q_Battery = battery * 3.7 * 3600  # 100mAh 3.7V  ->  mJ

        # 调用TOA计算函数（需补充TOACalculate实现）
        TOA = cls.TOACalculate(bw, sf, cr, n_Payload)

        # 发射电流/休眠电流配置  （测试）
        TX_Current = cls.dBmToCurrent(tx_power)  # 发射电流 (mA)
        Sleep_current = 0.006  # 休眠电流 (mA)

        # 占空比→周期/平均电流计算
        Tcycle = TOA / dutycycle  # 单个数据包循环周期 (秒)
        # 平均电流 = (休眠电流*休眠时间 + 发射电流*发射时间) / 总周期
        mean_current = (Sleep_current * Tcycle * (1 - dutycycle) + TX_Current * TOA) / Tcycle

        # 每秒能量消耗 (mA * V * 1s → mJ/s)
        Q_Consumption = mean_current * 3.3 * 1  # 平均电流*电压*1s  ->  mJ/秒

        # 计算使用寿命（不同单位）
        LifeTime_S = Q_Battery / Q_Consumption  # 秒
        LifeTime_Hour = LifeTime_S / 3600  # 小时
        LifeTime_Day = LifeTime_Hour / 24  # 天
        LifeTime_Year = LifeTime_Day / 360  # 年（按360天/年计算）

        # 返回天为单位的寿命
        if resType == "Y":
            LifeTime = LifeTime_Year
        elif resType == "D":
            LifeTime = LifeTime_Day
        elif resType == "H":
            LifeTime = LifeTime_Hour
        else:
            LifeTime = None

        return LifeTime

    @classmethod
    def dBmToCurrent(cls, tp):
        dBm = max(min(tp, 17), 2)
        # 实测拟合sx1278
        p = [0.00339772068746518, 0.148986494020688, 1.25166517120003, 36.2777443411981]
        Current = p[0] * (dBm ** 3) + p[1] ** (dBm ** 2) + p[2] * dBm + p[3]  # mA
        return Current

    @classmethod
    def TOACalculate(cls, bw, sf, cr, nPayload):
        H = 0  # implicit header disabled (H=0) or not (H=1)
        DE = 0  # low data rate optimization enabled (=1) or not (=0)
        Npream = 8  # number of preamble symbol (12.25  from Utz paper)
        bit_cyc = 16

        if bw == 125 and sf in [11, 12]:
            # low data rate optimization mandated for BW125 with SF11 and SF12
            DE = 1
        if sf == 6:
            # can only have implicit header with SF6
            H = 1

        Tsym = (2.0 ** sf) / bw  # Time of each symbol
        # self.Tcad = Tsym * 2  # 顺便记录CAD时间
        Tpream = (Npream + 4.25) * Tsym  # Time of the preamble
        # print ("sf", sf, " cr", cr, "pl", pl, "bw", bw)
        payloadSymbNB = 8 + max(
            math.ceil((8.0 * nPayload - 4.0 * sf + 28 + bit_cyc - 20 * H) / (4.0 * (sf - 2 * DE))) * (cr + 4),
            0)
        Tpayload = payloadSymbNB * Tsym  # Time of the payload

        return Tpream + Tpayload  # Airtime of the package = time of preamble + time of payload


if __name__ == "__main__":
    BW = 125  # 125kHz带宽
    CR = 1  # 编码率4/5

    SF = 7  # 扩频因子7
    TX_power = 14  # 14dBm发射功率
    Byte_Payload = 20  # 20字节载荷
    Battery = 1000  # 1000mAh电池
    Dutycycle = 0.01  # 1%占空比

    lifetime_days = LifetimeModule.getLifetime(BW, CR, SF, TX_power, Byte_Payload, Battery, Dutycycle, "D")
    print(f"设备使用寿命：{lifetime_days:.1f} 天")
