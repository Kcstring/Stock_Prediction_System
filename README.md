# 股票走势预测系统 Web Demo

一个面向中期答辩/演示的可运行原型，核心目标是先打通完整流程：

- 数据获取（行情 + 新闻）
- 数据入库和管理
- 模型处理入口占位
- 可视化展示和基础回测评估

当前预测为规则基线（无训练），便于后续无缝替换为真实模型推理。

## 功能总览

系统按页面模块分为 4 部分：

1. 数据获取与入库  
   从 Yahoo Finance 获取股票历史行情，从 Yahoo RSS 获取新闻，写入本地 SQLite。
2. 数据管理  
   查看数据库中已存股票、条数和时间范围，支持按股票删除。
3. 模型处理（占位）  
   预留训练/推理按钮与后端接口，当前不执行真实训练。
4. 可视化与回测  
   展示价格和技术指标，并按训练/测试切分做回测与指标评估。

## 技术栈

- 后端：FastAPI
- 数据处理：pandas + numpy
- 数据源：yfinance + Yahoo Finance RSS
- 前端：HTML + JavaScript + Plotly
- 数据库：SQLite (`data/stock_system.db`)

## 目录结构

```text
app/
  main.py                     # API 入口与路由
  services/
    data_service.py           # 外部数据抓取
    storage_service.py        # SQLite 读写与管理
    indicator_service.py      # 技术指标计算
    prediction_service.py     # 简单规则预测（占位）
    backtest_service.py       # 回测与评估指标
web/
  index.html                  # 页面结构
  app.js                      # 前端逻辑
  styles.css                  # 页面样式
data/
  stock_system.db             # 运行时数据库（自动生成）
start_web.bat                 # 一键启动并打开网页
stop_web.bat                  # 一键停止服务
requirements.txt
```

## 快速开始

### 方式一：命令行启动

1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

2. 启动服务

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

3. 浏览器访问

```text
http://127.0.0.1:8000
```

### 方式二：Windows 一键脚本

- 双击 `start_web.bat`
  - 新开终端运行服务
  - 自动打开网页
- 双击 `stop_web.bat`
  - 关闭 `8000` 端口上的服务进程

## 使用流程建议

1. 在模块 1 中填写股票代码、时间区间，执行“获取数据并存入数据库”
2. 在模块 1.5 检查数据库是否已有目标股票数据（必要时删除旧数据）
3. 点击模块 3“加载可视化结果”
4. 观察以下结果：
   - 数据切分信息（训练/测试区间）
   - 最终预测（下一交易日）
   - 最近一次已实现对比（预测方向 vs 真实方向）
   - 回测指标和收益曲线

## API 概览

- `GET /api/health`  
  健康检查。

- `POST /api/data/fetch`  
  抓取行情 + 新闻并写入数据库。

- `GET /api/data/stocks`  
  查询已入库股票概览（每个 symbol 的条数和日期范围）。

- `DELETE /api/data/stocks/{symbol}`  
  删除指定股票的已入库数据（行情 + 新闻）。

- `GET /api/visualization`  
  从数据库读取并返回可视化数据。  
  关键参数：
  - `symbol`
  - `start`, `end`
  - `limit`（新闻条数）
  - `train_ratio`（默认 `0.7`，范围 `0.5-0.95`）

  关键返回字段：
  - `dataset_split`：训练/测试样本数和区间
  - `backtest`：仅基于测试区间计算的评估结果
  - `final_prediction`：下一交易日预测（暂无真实标签）
  - `latest_realized_comparison`：最近一次已实现对比

- `POST /api/model/train`  
  模型处理占位接口（当前未实现）。

## 回测说明（当前版本）

- 回测只在测试区间执行，避免与训练段混用。
- 信号逻辑来自规则基线（非训练模型），用于流程演示。
- 当前指标包括：
  - Accuracy
  - Strategy Return / Benchmark Return / Excess Return
  - Sharpe
  - Max Drawdown
  - Win Rate
  - Trade Days

## 已知边界

- 预测模块尚未接入真实训练模型，仅为占位基线。
- 新闻数据依赖公开 RSS，可用性受外部源影响。
- 默认未计入交易手续费、滑点、停牌等实盘因素。

## 后续接入真实模型建议

1. 用真实训练/推理结果替换 `prediction_service.py`
2. 在 `POST /api/model/train` 接入训练任务和状态管理
3. 将预测输出持久化到数据库，形成模型版本对比
4. 在回测中加入交易成本、滑点和风险约束
