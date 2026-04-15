import time
from datetime import datetime
from multiprocessing import Process
from multiprocessing import Manager

import json

from collections import defaultdict
import os

from src import GlobalCfg as GCfg
from src.Simulator import LoRaSimulationEnv


def SaveData(res_dict):
    # 按协议分组并排序
    data = defaultdict(lambda: {'nodes': [], 'prr': [], 't': []})
    for ((SN, node_count), (prr, t)) in res_dict.items():  # 填充数据
        data[SN]['nodes'].append(node_count)
        data[SN]['prr'].append(prr)
        data[SN]['t'].append(t)

    for sn in data:  # 排序
        sorted_data = sorted(zip(
            data[sn]['nodes'],
            data[sn]['prr'],
            data[sn]['t']
        ))
        nodes, prr, t = zip(*sorted_data)
        data[sn]['nodes'] = list(nodes)
        data[sn]['prr'] = list(prr)
        data[sn]['t'] = list(t)

    folder = "SN_Result"
    t = "{}h".format(int(GCfg.SimulationDuration / (60000 * 60)))
    res_folder = os.path.join(folder, t)
    os.makedirs(res_folder, exist_ok=True)

    try:
        with open(str(res_folder + r"\TIME_LoRaNetSim.json"), "r", encoding="utf-8") as f:
            pass
    except:
        with open(str(res_folder + r"\TIME_LoRaNetSim.json"), "w", encoding="utf-8") as f:
            f.write("{}")

    # 仿真时间追加写入
    for sn in data:
        with open(str(res_folder + r"\TIME_LoRaNetSim.json"), "r", encoding="utf-8") as f:
            time_data = json.load(f)

            if sn not in time_data:
                time_data[sn] = {"nodes": data[sn]['nodes'], "times_list": []}
            time_data[sn]["times_list"].append(data[sn]['t'])

        with open(str(res_folder + r"\TIME_LoRaNetSim.json"), "w", encoding="utf-8") as f:
            json.dump(time_data, f, indent=4, ensure_ascii=False)

    # PRR覆盖写入
    with open(str(res_folder + r"\PRR_LoRaNetSim.json"), "w", encoding="utf-8") as f:  # 保存原始数据
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.flush()  # 清空Python级别的缓冲区
        os.fsync(f.fileno())  # 强制操作系统将缓冲区写入磁盘


def func(mac, nNode, optimization, r_dict, SN_key, cfg):
    GCfg.GlobalConfig(**cfg)  # 配置全局参数

    GCfg.SN_idx = SN_key

    start_time = time.time()  # 记录开始时间
    # 可自定义参数：节点数、仿真时长
    LoRaSim = LoRaSimulationEnv(nNode, mac, optimization)
    LoRaSim.run()
    LoRaSim.Show_Results()

    run_time = time.time() - start_time  # 计算耗时（秒）

    # 结果
    dict_key = (SN_key, nNode)
    r_dict[dict_key] = [float(LoRaSim.PRR), round(run_time, 4)]
    print("SN:{}, Nodes:{}, PRR:{}, Time:{}"
          .format(SN_key, nNode, round(LoRaSim.PRR, 4), round(run_time, 4)))


if __name__ == "__main__":

    # 全局变量配置
    cfg = {
        "new_SimulationDuration": 60000 * 60 * 8,  # 仿真时间 小时
        "new_lamuda": 0.001,  # 泊松分布λ
        "new_ADR": False,  # ADR
        "new_SimModule": "SN",  # 仿真模式
        "new_Actual_CADe": False,  # 实测CAD效率 or 100%可靠性
        "new_AutoSaveResult": False  # 自动保存结果
    }
    GCfg.GlobalConfig(**cfg)

    result_dict = dict()
    LoRa_MAC = GCfg.LoRaMAC.ALOHA
    parameter_optimization = GCfg.ParameterOptimization.minTOA

    # 单次测试
    func(LoRa_MAC, 1000, parameter_optimization, result_dict, "SN1", cfg)

    # # 批量测试
    # for x in range(0, 10):
    #     cfg["new_SimulationDuration"] = 60000 * 60 * (2 ** x)
    #     GCfg.GlobalConfig(**cfg)
    #
    #     num_list = range(1, 3000, 250)
    #     for i in range(1, 10):
    #         print("时间:{}, 循环次数：{}".format(int(GCfg.SimulationDuration / (60000 * 60)), i))
    #         for SN_key, SN_value in GCfg.SN.items():
    #             for node_num in num_list:
    #                 func(LoRa_MAC, node_num, NodeMap, result_dict, SN_key, cfg)
    #         SaveData(result_dict)
