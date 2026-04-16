# 适用于LoRa网络的数据包级别通用仿真器LoRaNetSim

LoRaNetSim是一个基于simpy的适用于LoRa网络的数据包级别仿真器，可以实现MAC信道接入协议仿真、参数分配方法仿真、动态网络仿真、ADR仿真、能耗相关仿真，同时提供仿真器性能测试例程和自动化测试脚本例程与对应实验结果的可视化例程。

## 参考文献

[1]LoRa网络上行容量扩展方法研究（硕士论文待发表）

[2]BOR M C, ROEDIG U, VOIGT T, et al. Do LoRa low-power wide-area networks scale?[C]//ACM International Conference on Modeling, Analysis and Simulation of Wireless and Mobile Systems (MSWiM). Malta Malta: ACM, 2016: 59-67.

[3]GAMAGE A, LIANDO J C, GU C, et al. LMAC: efficient carrier-sense multiple access for LoRa[C]//Annual International Conference on Mobile Computing and Networking (MobiCom). London United Kingdom: ACM, 2020: 1-13.

[4]GAMAGE A, LIANDO J, GU C, et al. LMAC: efficient carrier-sense multiple access for LoRa[J]. ACM Transactions on Sensor Networks, 2023, 19(2): 1-27.

[5]MARINI R, CERRONI W, BURATTI C. A Novel Collision-Aware Adaptive Data Rate Algorithm for LoRaWAN Networks[J]. IEEE Internet of Things Journal, 2021, 8(4): 2670-2680.



## 项目结构

### 1、应用层

```
test_MAC.py                 -> MAC协议测试例程
test_DynamicNet.py          -> 动态网络与区间统计功能测试例程
test_parameter.py           -> 不同初始参数分配方法测试例程
test_ADR.py                 -> ADR测试例程
test_SN.py                  -> 仿真器性能测试例程
```

### 2、仿真控制层

#### Simulator.py       

实现simpy离散事件的创建、实验数据统计、动态调整网络负载、区间统计网络性能



#### GlobalCfg.py

全局参数的定义



### 3、核心功能实现层

#### Node.py

实现Node类，类属性为节点通信参数配置、协议参数配置和相关统计数据的定义

```
Node.Transmit() 节点发送数据包的事件函数，采用泊松分布的数据包产生频率，集成MAC层信道接入协议，可选ALOHA\LMAC\DS-LoRa。

Node.Calculate_distance2me() 计算任意坐标位置到节点的距离

Node.CheckDownLink() 查看网关下行数据，ADR功能
```



#### Packet.py

实现Packet类，类属性为数据包通信参数、TOA、RSS等

```
Packet.getSNR() \ Packet.getRSS() 获取数据包传输到某个距离时的信号强度 
```



#### Channel.py

实现LoRaChannel类，类属性里包含一个以逻辑信道分组的正在传输的数据包列表

```
LoRaChannel.TX() 实现数据包开始发送时注册到对应逻辑信道，传输结束后释放数据包并向网关推送

LoRaChannel.ChannelActivityDetection() CAD功能实现，可选信道感知的可靠性为100%或者实测可靠性
```



#### Gateway.py

实现GW类，类属性包含实验统计相关变量

```
GW.ReceivePkt() 实现数据包接收功能，以及ADR功能
```



#### NodeMap.py

实现NodeMap类，用于生成带有初始参数分配的节点分布文件，预分配的节点数量通常很多，仿真时根据节点数目的需求，从文件中随机抽取。此文件可以单独运行用于生成初始分布或者可视化指定分布文件

```
NodeMap.CreateMaxMap() 创建预分配的节点分布，包含通信参数的初始化

NodeMap.GetNodeMap() 获取指定节点数目和参数分配方法的节点分布

NodeMap.showMap() 可视化指定分布
```



#### ParameterAllocation.py

不同参数分配方法的具体实现



#### CoverageModule.py

定义路径损耗模型，该文件可以单独运行，可视化路径损耗模型

```
CoverageModule.rss() 计算某一发射功率的信号在某个距离时的信号强度

CoverageModule.getCoverage() 计算某个SF,TP组合下的最远传输距离
```



#### LifetimeModule.py

定义功耗模型，计算TOA，TP向电流转化

```
LifetimeModule.dBmToCurrent() TP向电流转化

LifetimeModule.TOACalculate() 计算TOA
```



## 其他

与LoRaSim的对比评估，CPU主频为2.4GHz，8核16线程

![](https://github.com/PANJUN-T/LoRaNetSim/blob/main/src/Pictrue/SimunlatorPRR.png?raw=true)

![](https://github.com/PANJUN-T/LoRaNetSim/blob/main/src/Pictrue/SimunlatorTime.png?raw=true)

