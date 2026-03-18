import numpy as np
import pandas as pd


def add_indicators(rows: list[dict]) -> list[dict]:
    if not rows:
        return rows

    frame = pd.DataFrame(rows)
    close = frame["close"].astype(float)

    frame["sma_10"] = close.rolling(10).mean()
    frame["ema_12"] = close.ewm(span=12, adjust=False).mean()
    frame["ema_26"] = close.ewm(span=26, adjust=False).mean()
    frame["macd"] = frame["ema_12"] - frame["ema_26"]
    frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False).mean()
    frame["rsi_14"] = _compute_rsi(close, period=14)
    frame["daily_return"] = close.pct_change().fillna(0.0)
    frame["volatility_20"] = frame["daily_return"].rolling(20).std()

    frame = frame.replace({np.nan: None})
    return frame.to_dict(orient="records")


def _compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)
