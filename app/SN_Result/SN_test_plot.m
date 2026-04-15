%% ===================== 基础配置 =====================
clear; clc; 
Time_List = {'1h', '2h', '4h', '8h'};
SN_List = {'SN1', 'SN2', 'SN3'};

% 高区分度配色 + 线型 + 标记（与Python完全一致）
SN_STYLE = containers.Map;
SN_STYLE('SN1') = struct('color', [31/255, 119/255, 180/255], 'marker', 'o', 'linestyle', '-');
SN_STYLE('SN2') = struct('color', [255/255, 127/255, 14/255], 'marker', 's', 'linestyle', '-');
SN_STYLE('SN3') = struct('color', [44/255, 160/255, 44/255], 'marker', '^', 'linestyle', '-');

% 时间序列专用配色（4个时间 → 4种颜色）
TIME_COLORS = [
    31/255, 119/255, 180/255;   % #1f77b4
    255/255, 127/255, 14/255;   % #ff7f0e
    44/255, 160/255, 44/255;    % #2ca02c
    214/255, 39/255, 40/255     % #d62728
];

%% ===================== 图1：PRR =====================
fig1 = figure('Position', [600, 300, 580, 450]);  
subplot('position', [0.10 0.11 0.86 0.86]);
time = Time_List{1};  

fid = fopen(fullfile(time, 'PRR_LoRaNetSim.json'), 'r', 'n', 'UTF-8');
json_str = fread(fid, '*char')';
fclose(fid);
DER_LoRaNetSim = jsondecode(json_str);

fid = fopen(fullfile(time, 'PRR_LoRaSim.json'), 'r', 'n', 'UTF-8');
json_str = fread(fid, '*char')';
fclose(fid);
DER_LoRaSim = jsondecode(json_str);

hold on; 
% LoRaNetSim：实线 + 实心标记
for i = 1:length(SN_List)
    sn = SN_List{i};
    style = SN_STYLE(sn);
    x = DER_LoRaNetSim.(sn).nodes;
    y = DER_LoRaNetSim.(sn).prr;
    plot(x, y, 'Marker', style.marker, 'LineStyle', style.linestyle, ...
         'Color', style.color, 'LineWidth', 2, 'MarkerSize', 7, ...
         'DisplayName', sprintf('%s-LoRaNetSim', sn));
end

% LoRaSim：虚线 + 空心标记
for i = 1:length(SN_List)
    sn = SN_List{i};
    style = SN_STYLE(sn);
    x = DER_LoRaSim.(sn).nodes;
    y = DER_LoRaSim.(sn).prr;
    plot(x, y, 'Marker', style.marker, 'LineStyle', '--', ...
         'Color', style.color, 'LineWidth', 2, 'MarkerSize', 7, ...
         'MarkerFaceColor', 'w',  ...
         'DisplayName', sprintf('%s-LoRaSim', sn));
end

xlim([0, 2751]);
xlabel('Node', 'FontSize', 12);
ylabel('PRR', 'FontSize', 12);

h_legend = legend('Location', 'southeast', 'FontSize', 12, 'NumColumns', 2);
pos = get(h_legend, 'Position');
pos(1) = pos(1);  pos(2) = pos(2) + 0.1; 
set(h_legend, 'Position', pos); 

grid on; box on;
set(gca, 'FontName', 'Arial', 'FontSize', 12)

% saveas(fig1, 'Simunlator_PRR.emf', 'emf');


%% ===================== 图2：Run Time (误差棒) =====================
fig2 = figure('Position', [600, 300, 580, 450]);
subplot('position', [0.10 0.11 0.86 0.86]);
TARGET_SN = 'SN2';
hold on;

for idx = 1:length(Time_List)
    time = Time_List{idx};
    color = TIME_COLORS(idx, :);
    
    % 读取JSON文件
    fid = fopen(fullfile(time, 'TIME_LoRaNetSim.json'), 'r', 'n', 'UTF-8');
    json_str = fread(fid, '*char')';
    fclose(fid);
    Time_LoRaNetSim = jsondecode(json_str);
    
    fid = fopen(fullfile(time, 'TIME_LoRaSim.json'), 'r', 'n', 'UTF-8');
    json_str = fread(fid, '*char')';
    fclose(fid);
    Time_LoRaSim = jsondecode(json_str);
    
    nodes = Time_LoRaNetSim.(TARGET_SN).nodes;
    
    % LoRaNetSim：圆圈 + 实线 + 误差棒
    times_list = Time_LoRaNetSim.(TARGET_SN).times_list;  % 转为矩阵
    mean_NetSim = mean(times_list, 1);
    std_NetSim = std(times_list, 0, 1);
    errorbar(nodes, mean_NetSim, std_NetSim, ...
             'LineStyle', '-', 'Marker', 'o', 'CapSize', 6, ...
             'Color', color, 'LineWidth', 2, 'MarkerSize', 3, ...
             'DisplayName', sprintf('%s-LoRaNetSim', time));
    
    % LoRaSim：星形 + 点线 + 误差棒
    times_list = Time_LoRaSim.(TARGET_SN).times_list;
    mean_Sim = mean(times_list, 1);
    std_Sim = std(times_list, 0, 1);
    errorbar(nodes, mean_Sim, std_Sim, ...
             'LineStyle', '--', 'Marker', 'o', 'CapSize', 6, ...
             'Color', color, 'LineWidth', 2, 'MarkerSize', 3, ...
             'DisplayName', sprintf('%s-LoRaSim', time));
end

ylim([0, 22]);
xlim([0, 2751]);

xlabel('Node', 'FontSize', 12);
ylabel('Run Time (s)', 'FontSize', 12);

legend('Location', 'northwest', 'FontSize', 12, 'NumColumns', 2);


grid on; box on;
set(gca, 'FontName', 'Arial', 'FontSize', 12)

% saveas(fig2, 'Simunlator_Time.emf', 'emf');
