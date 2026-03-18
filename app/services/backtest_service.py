import math


def run_backtest(rows: list[dict], start_index: int = 1) -> dict:
    """
    A simple rolling backtest for the demo signal engine.
    Signal at t-1 is applied to return at t.
    """
    if len(rows) < 3 or start_index >= len(rows):
        return {
            "metrics": {
                "accuracy": 0.0,
                "total_return": 0.0,
                "benchmark_return": 0.0,
                "excess_return": 0.0,
                "sharpe": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "trade_days": 0,
            },
            "series": {
                "dates": [],
                "strategy_cum_returns": [],
                "benchmark_cum_returns": [],
                "signal_accuracy_flags": [],
            },
        }

    dates: list[str] = []
    strategy_daily_returns: list[float] = []
    benchmark_daily_returns: list[float] = []
    signal_accuracy_flags: list[int] = []

    strategy_equity = 1.0
    benchmark_equity = 1.0
    strategy_curve: list[float] = []
    benchmark_curve: list[float] = []

    active_trade_days = 0
    win_days = 0
    directional_cases = 0
    directional_hits = 0

    for idx in range(max(1, start_index), len(rows)):
        prev_row = rows[idx - 1]
        row = rows[idx]

        signal = _signal_from_row(prev_row)
        position = {"buy": 1.0, "sell": -1.0, "hold": 0.0}.get(signal, 0.0)

        day_ret = float(row.get("daily_return") or 0.0)
        strategy_ret = position * day_ret

        strategy_equity *= 1.0 + strategy_ret
        benchmark_equity *= 1.0 + day_ret

        date_value = str(row.get("date") or "")
        dates.append(date_value)
        strategy_daily_returns.append(strategy_ret)
        benchmark_daily_returns.append(day_ret)
        strategy_curve.append(strategy_equity - 1.0)
        benchmark_curve.append(benchmark_equity - 1.0)

        if position != 0:
            active_trade_days += 1
            if strategy_ret > 0:
                win_days += 1

        pred_dir = _signal_to_direction(signal)
        actual_dir = _return_to_direction(day_ret)
        if pred_dir in ("up", "down"):
            directional_cases += 1
            is_hit = 1 if pred_dir == actual_dir else 0
            directional_hits += is_hit
            signal_accuracy_flags.append(is_hit)
        else:
            signal_accuracy_flags.append(0)

    accuracy = directional_hits / directional_cases if directional_cases else 0.0
    total_return = strategy_curve[-1] if strategy_curve else 0.0
    benchmark_return = benchmark_curve[-1] if benchmark_curve else 0.0
    excess_return = total_return - benchmark_return
    win_rate = win_days / active_trade_days if active_trade_days else 0.0
    sharpe = _annualized_sharpe(strategy_daily_returns)
    max_drawdown = _max_drawdown(strategy_curve)

    return {
        "metrics": {
            "accuracy": round(accuracy, 6),
            "total_return": round(total_return, 6),
            "benchmark_return": round(benchmark_return, 6),
            "excess_return": round(excess_return, 6),
            "sharpe": round(sharpe, 6),
            "max_drawdown": round(max_drawdown, 6),
            "win_rate": round(win_rate, 6),
            "trade_days": active_trade_days,
            "test_points": len(dates),
        },
        "series": {
            "dates": dates,
            "strategy_cum_returns": strategy_curve,
            "benchmark_cum_returns": benchmark_curve,
            "signal_accuracy_flags": signal_accuracy_flags,
        },
    }


def latest_realized_comparison(rows: list[dict]) -> dict:
    """
    Compare yesterday's predicted direction with today's realized direction.
    """
    if len(rows) < 2:
        return {
            "available": False,
            "message": "Not enough data to compare realized outcome.",
        }

    prev_row = rows[-2]
    current_row = rows[-1]
    signal = _signal_from_row(prev_row)
    predicted = _signal_to_direction(signal)
    actual = _return_to_direction(float(current_row.get("daily_return") or 0.0))
    matched = predicted in ("up", "down") and predicted == actual

    return {
        "available": True,
        "as_of_date": str(current_row.get("date") or ""),
        "predicted_direction": predicted,
        "actual_direction": actual,
        "matched": matched,
        "signal": signal,
    }


def _signal_from_row(row: dict) -> str:
    close = float(row.get("close") or 0.0)
    sma_10 = float(row.get("sma_10") or close)
    rsi_14 = float(row.get("rsi_14") or 50.0)
    macd = float(row.get("macd") or 0.0)
    macd_signal = float(row.get("macd_signal") or 0.0)

    score = 0.0
    score += 0.35 if close >= sma_10 else -0.35
    score += 0.25 if macd >= macd_signal else -0.25
    score += 0.2 if rsi_14 < 70 else -0.2
    score += 0.2 if rsi_14 > 30 else -0.2

    up_prob = max(0.0, min(1.0, 0.5 + score * 0.5))
    down_prob = 1.0 - up_prob
    if up_prob >= 0.6:
        return "buy"
    if down_prob >= 0.6:
        return "sell"
    return "hold"


def _signal_to_direction(signal: str) -> str:
    if signal == "buy":
        return "up"
    if signal == "sell":
        return "down"
    return "neutral"


def _return_to_direction(day_ret: float) -> str:
    if day_ret > 0:
        return "up"
    if day_ret < 0:
        return "down"
    return "neutral"


def _annualized_sharpe(returns: list[float], annual_factor: int = 252) -> float:
    if len(returns) < 2:
        return 0.0
    mean_ret = sum(returns) / len(returns)
    var = sum((x - mean_ret) ** 2 for x in returns) / (len(returns) - 1)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean_ret / std) * math.sqrt(annual_factor)


def _max_drawdown(curve_returns: list[float]) -> float:
    if not curve_returns:
        return 0.0

    equity_values = [1.0 + x for x in curve_returns]
    peak = equity_values[0]
    mdd = 0.0
    for value in equity_values:
        peak = max(peak, value)
        drawdown = 0.0 if peak == 0 else (value - peak) / peak
        mdd = min(mdd, drawdown)
    return abs(mdd)
