import math

from src.CoverageModule import CoverageModule
from ctrl import GlobalCfg as GCfg


class ParamAlloc:
    @classmethod
    def findBestParam(cls, maxR, distance, method):
        tpList = GCfg.LoRaParameter.TP_List
        sfList = GCfg.LoRaParameter.SF_List

        if method == "Equidistant":
            sfCount = len(sfList)
            # 计算每个SF对应的距离区间
            segment = maxR / sfCount

            idx = int(math.ceil(distance / segment)) - 1
            idx = max(0, min(idx, sfCount - 1))  # 边界处理

            return sfList[idx], max(tpList)

        if method == "minTOA":
            bSF = max(sfList)
            bTP = max(tpList)
            # 逆序搜索，记录最后一个值
            for sf in reversed(sfList):
                for tp in reversed(tpList):
                    # 计算传输距离
                    if CoverageModule.getCoverage(sf, tp) >= distance:
                        bSF = sf
                        bTP = tp
            return bSF, bTP

        if method == "ADR":
            return max(sfList), max(tpList)
