const symbolInput = document.getElementById("symbolInput");
const startInput = document.getElementById("startInput");
const endInput = document.getElementById("endInput");
const newsLimitInput = document.getElementById("newsLimitInput");
const trainRatioInput = document.getElementById("trainRatioInput");
const fetchBtn = document.getElementById("fetchBtn");
const refreshDbBtn = document.getElementById("refreshDbBtn");
const modelBtn = document.getElementById("modelBtn");
const visualBtn = document.getElementById("visualBtn");
const fetchStatus = document.getElementById("fetchStatus");
const dbStatus = document.getElementById("dbStatus");
const modelStatus = document.getElementById("modelStatus");
const visualStatus = document.getElementById("visualStatus");
const dbTableBody = document.getElementById("dbTableBody");

const signalText = document.getElementById("signalText");
const probText = document.getElementById("probText");
const reasonText = document.getElementById("reasonText");
const splitInfoList = document.getElementById("splitInfoList");
const latestCompareText = document.getElementById("latestCompareText");
const latestCompareMeta = document.getElementById("latestCompareMeta");
const indicatorList = document.getElementById("indicatorList");
const newsList = document.getElementById("newsList");
const backtestMetrics = document.getElementById("backtestMetrics");

const today = new Date();
const oneYearAgo = new Date();
oneYearAgo.setFullYear(today.getFullYear() - 1);
startInput.value = toDateInput(oneYearAgo);
endInput.value = toDateInput(today);

fetchBtn.addEventListener("click", () => {
  void fetchAndStoreData();
});
refreshDbBtn.addEventListener("click", () => {
  void loadDbSummary();
});
modelBtn.addEventListener("click", () => {
  void runModelPlaceholder();
});
visualBtn.addEventListener("click", () => {
  void loadVisualization();
});
void loadDbSummary();

async function fetchAndStoreData() {
  const symbol = symbolInput.value.trim().toUpperCase() || "AAPL";
  const start = startInput.value;
  const end = endInput.value;
  const newsLimit = Number(newsLimitInput.value || 20);
  const trainRatio = Number(trainRatioInput.value || 0.7);

  fetchBtn.disabled = true;
  fetchBtn.textContent = "获取中...";
  fetchStatus.textContent = "正在抓取行情与新闻，并写入数据库...";

  try {
    const response = await fetch("/api/data/fetch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symbol, start, end, news_limit: newsLimit }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "数据获取失败");
    }

    const result = await response.json();
    fetchStatus.textContent =
      `完成：本次保存行情 ${result.saved_stock_rows} 条，新闻 ${result.saved_news_rows} 条。` +
      `数据库累计行情 ${result.total_stock_rows_in_db} 条，新闻 ${result.total_news_rows_in_db} 条。`;
    await loadDbSummary();
  } catch (error) {
    fetchStatus.textContent = `失败：${String(error)}`;
  } finally {
    fetchBtn.disabled = false;
    fetchBtn.textContent = "获取数据并存入数据库";
  }
}

async function loadDbSummary() {
  refreshDbBtn.disabled = true;
  refreshDbBtn.textContent = "加载中...";
  dbStatus.textContent = "正在读取数据库内容...";
  try {
    const response = await fetch("/api/data/stocks");
    if (!response.ok) {
      throw new Error("数据库读取失败");
    }
    const result = await response.json();
    renderDbTable(result.items || []);
    dbStatus.textContent = `当前已入库股票数量：${result.count}`;
  } catch (error) {
    dbStatus.textContent = `失败：${String(error)}`;
  } finally {
    refreshDbBtn.disabled = false;
    refreshDbBtn.textContent = "查看当前数据库内容";
  }
}

function renderDbTable(items) {
  if (!items.length) {
    dbTableBody.innerHTML = '<tr><td colspan="5">暂无数据</td></tr>';
    return;
  }
  dbTableBody.innerHTML = items
    .map(
      (item) => `
      <tr>
        <td>${escapeHtml(item.symbol)}</td>
        <td>${item.stock_rows ?? 0}</td>
        <td>${item.news_rows ?? 0}</td>
        <td>${escapeHtml(item.start_date || "-")} ~ ${escapeHtml(item.end_date || "-")}</td>
        <td>
          <button class="btn-danger" data-symbol="${escapeHtml(item.symbol)}">删除</button>
        </td>
      </tr>
    `
    )
    .join("");

  dbTableBody.querySelectorAll("button[data-symbol]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const symbol = btn.getAttribute("data-symbol");
      if (symbol) void deleteSymbolData(symbol);
    });
  });
}

async function deleteSymbolData(symbol) {
  const confirmed = window.confirm(`确认删除 ${symbol} 的全部已入库数据吗？`);
  if (!confirmed) return;

  dbStatus.textContent = `正在删除 ${symbol} 数据...`;
  try {
    const response = await fetch(`/api/data/stocks/${encodeURIComponent(symbol)}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "删除失败");
    }
    const result = await response.json();
    dbStatus.textContent =
      `已删除 ${result.symbol}：行情 ${result.deleted_stock_rows} 条，新闻 ${result.deleted_news_rows} 条。`;
    await loadDbSummary();
  } catch (error) {
    dbStatus.textContent = `失败：${String(error)}`;
  }
}

async function runModelPlaceholder() {
  modelBtn.disabled = true;
  modelBtn.textContent = "处理中...";
  modelStatus.textContent = "正在调用模型处理模块（占位）...";

  try {
    const response = await fetch("/api/model/train", { method: "POST" });
    if (!response.ok) {
      throw new Error("模型模块调用失败");
    }
    const result = await response.json();
    modelStatus.textContent = `状态：${result.status}。${result.message}`;
  } catch (error) {
    modelStatus.textContent = `失败：${String(error)}`;
  } finally {
    modelBtn.disabled = false;
    modelBtn.textContent = "启动模型处理（暂未实现）";
  }
}

async function loadVisualization() {
  const symbol = symbolInput.value.trim().toUpperCase() || "AAPL";
  const start = startInput.value;
  const end = endInput.value;
  const newsLimit = Number(newsLimitInput.value || 20);
  const trainRatio = Number(trainRatioInput.value || 0.7);

  visualBtn.disabled = true;
  visualBtn.textContent = "加载中...";
  visualStatus.textContent = "正在从数据库读取并生成可视化...";

  try {
    const response = await fetch(
      `/api/visualization?symbol=${symbol}&start=${start}&end=${end}&limit=${newsLimit}&train_ratio=${trainRatio}`
    );
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "可视化加载失败");
    }
    const result = await response.json();

    renderSignal(result.final_prediction);
    renderSplitInfo(result.dataset_split);
    renderLatestComparison(result.latest_realized_comparison);
    renderIndicators(result.rows);
    renderChart(result.symbol, result.rows);
    renderBacktest(result.symbol, result.backtest);
    renderNews(result.items || []);
    visualStatus.textContent = `完成：读取 ${result.rows.length} 条行情数据并完成可视化。`;
  } catch (error) {
    renderBacktest("-", null);
    visualStatus.textContent = `失败：${String(error)}`;
  }
  finally {
    visualBtn.disabled = false;
    visualBtn.textContent = "加载可视化结果";
  }
}

function renderSignal(prediction) {
  if (!prediction) {
    signalText.textContent = "-";
    probText.textContent = "-";
    reasonText.textContent = "-";
    return;
  }
  const map = {
    buy: "BUY / 买入",
    sell: "SELL / 卖出",
    hold: "HOLD / 观望",
  };
  signalText.textContent = map[prediction.signal] || prediction.signal;
  probText.textContent = `上涨概率: ${(prediction.up_probability * 100).toFixed(
    1
  )}% | 下跌概率: ${(prediction.down_probability * 100).toFixed(1)}%`;
  reasonText.textContent = prediction.reason || "";
}

function renderSplitInfo(split) {
  if (!split) {
    splitInfoList.innerHTML = "<li>暂无数据</li>";
    return;
  }
  const items = [
    `总样本数: ${split.total_rows}`,
    `训练集: ${split.train_rows} (${(split.train_ratio * 100).toFixed(0)}%)`,
    `测试集: ${split.test_rows} (${(100 - split.train_ratio * 100).toFixed(0)}%)`,
    `训练区间: ${split.train_start_date || "-"} ~ ${split.train_end_date || "-"}`,
    `测试区间: ${split.test_start_date || "-"} ~ ${split.test_end_date || "-"}`,
  ];
  splitInfoList.innerHTML = items.map((x) => `<li>${x}</li>`).join("");
}

function renderLatestComparison(info) {
  if (!info || !info.available) {
    latestCompareText.textContent = "暂无可比较结果";
    latestCompareMeta.textContent = info?.message || "";
    return;
  }
  latestCompareText.textContent = `预测方向: ${dirText(info.predicted_direction)} | 实际方向: ${dirText(info.actual_direction)} | ${
    info.matched ? "匹配" : "不匹配"
  }`;
  latestCompareMeta.textContent = `比较日期: ${info.as_of_date}`;
}

function renderIndicators(rows) {
  if (!rows.length) {
    indicatorList.innerHTML = "<li>暂无数据</li>";
    return;
  }

  const last = rows[rows.length - 1];
  const items = [
    `收盘价: ${fmt(last.close)}`,
    `SMA(10): ${fmt(last.sma_10)}`,
    `RSI(14): ${fmt(last.rsi_14)}`,
    `MACD: ${fmt(last.macd)} / Signal: ${fmt(last.macd_signal)}`,
    `20日波动率: ${pct(last.volatility_20)}`,
  ];
  indicatorList.innerHTML = items.map((x) => `<li>${x}</li>`).join("");
}

function renderChart(symbol, rows) {
  const x = rows.map((r) => r.date);
  const open = rows.map((r) => r.open);
  const high = rows.map((r) => r.high);
  const low = rows.map((r) => r.low);
  const close = rows.map((r) => r.close);
  const sma10 = rows.map((r) => r.sma_10);
  const rsi = rows.map((r) => r.rsi_14);
  const macd = rows.map((r) => r.macd);
  const macdSignal = rows.map((r) => r.macd_signal);

  const data = [
    {
      x,
      open,
      high,
      low,
      close,
      type: "candlestick",
      name: `${symbol} K线`,
      yaxis: "y1",
    },
    {
      x,
      y: sma10,
      type: "scatter",
      mode: "lines",
      name: "SMA10",
      line: { color: "#22d3ee", width: 1.5 },
      yaxis: "y1",
    },
    {
      x,
      y: rsi,
      type: "scatter",
      mode: "lines",
      name: "RSI14",
      line: { color: "#f59e0b", width: 1.2 },
      yaxis: "y2",
    },
    {
      x,
      y: macd,
      type: "scatter",
      mode: "lines",
      name: "MACD",
      line: { color: "#a78bfa", width: 1.2 },
      yaxis: "y3",
    },
    {
      x,
      y: macdSignal,
      type: "scatter",
      mode: "lines",
      name: "MACD Signal",
      line: { color: "#f43f5e", width: 1.2 },
      yaxis: "y3",
    },
  ];

  const layout = {
    paper_bgcolor: "#111827",
    plot_bgcolor: "#111827",
    font: { color: "#e2e8f0" },
    xaxis: { domain: [0, 1], rangeslider: { visible: false } },
    yaxis: { domain: [0.4, 1], title: "Price" },
    yaxis2: { domain: [0.2, 0.35], title: "RSI", range: [0, 100] },
    yaxis3: { domain: [0.0, 0.15], title: "MACD" },
    legend: { orientation: "h" },
    margin: { l: 50, r: 20, t: 20, b: 40 },
  };

  Plotly.newPlot("priceChart", data, layout, { responsive: true });
}

function renderNews(items) {
  if (!items.length) {
    newsList.innerHTML = "<li>暂无相关新闻</li>";
    return;
  }

  newsList.innerHTML = items
    .map(
      (n) =>
        `<li><a href="${n.url}" target="_blank" rel="noreferrer">${escapeHtml(
          n.title
        )}</a><br /><small>${escapeHtml(n.published_at || "")}</small></li>`
    )
    .join("");
}

function renderBacktest(symbol, backtest) {
  if (!backtest || !backtest.metrics || !backtest.series) {
    backtestMetrics.innerHTML = '<div class="metric-item"><div class="label">状态</div><div class="value">暂无数据</div></div>';
    Plotly.newPlot(
      "backtestChart",
      [],
      {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        font: { color: "#e2e8f0" },
        xaxis: { title: "Date" },
        yaxis: { title: "Return" },
      },
      { responsive: true }
    );
    return;
  }

  const m = backtest.metrics;
  const metricItems = [
    ["Accuracy", pct(m.accuracy)],
    ["Sharpe", num(m.sharpe)],
    ["Strategy Return", pct(m.total_return)],
    ["Benchmark Return", pct(m.benchmark_return)],
    ["Excess Return", pct(m.excess_return)],
    ["Max Drawdown", pct(m.max_drawdown)],
    ["Win Rate", pct(m.win_rate)],
    ["Trade Days", String(m.trade_days ?? 0)],
  ];

  backtestMetrics.innerHTML = metricItems
    .map(
      ([label, value]) =>
        `<div class="metric-item"><div class="label">${label}</div><div class="value">${value}</div></div>`
    )
    .join("");

  const s = backtest.series;
  const traces = [
    {
      x: s.dates || [],
      y: s.strategy_cum_returns || [],
      type: "scatter",
      mode: "lines",
      name: `${symbol} Strategy`,
      line: { color: "#22c55e", width: 2 },
    },
    {
      x: s.dates || [],
      y: s.benchmark_cum_returns || [],
      type: "scatter",
      mode: "lines",
      name: `${symbol} Buy&Hold`,
      line: { color: "#60a5fa", width: 2 },
    },
  ];

  const layout = {
    paper_bgcolor: "#111827",
    plot_bgcolor: "#111827",
    font: { color: "#e2e8f0" },
    legend: { orientation: "h" },
    margin: { l: 50, r: 20, t: 20, b: 40 },
    xaxis: { title: "Date" },
    yaxis: { title: "Cumulative Return" },
  };
  Plotly.newPlot("backtestChart", traces, layout, { responsive: true });
}

function toDateInput(d) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function fmt(v) {
  if (v == null || Number.isNaN(Number(v))) return "-";
  return Number(v).toFixed(2);
}

function num(v) {
  if (v == null || Number.isNaN(Number(v))) return "-";
  return Number(v).toFixed(3);
}

function pct(v) {
  if (v == null || Number.isNaN(Number(v))) return "-";
  return `${(Number(v) * 100).toFixed(2)}%`;
}

function dirText(direction) {
  const map = { up: "上涨", down: "下跌", neutral: "中性" };
  return map[direction] || direction;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
