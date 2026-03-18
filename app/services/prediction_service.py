def build_demo_prediction(rows: list[dict]) -> dict:
    """
    Placeholder prediction module:
    Replace this with your trained model inference later.
    """
    if not rows:
        return {
            "signal": "hold",
            "up_probability": 0.5,
            "down_probability": 0.5,
            "reason": "No data",
        }

    latest = rows[-1]
    close = latest.get("close") or 0.0
    sma_10 = latest.get("sma_10") or close
    rsi_14 = latest.get("rsi_14") or 50.0
    macd = latest.get("macd") or 0.0
    macd_signal = latest.get("macd_signal") or 0.0

    score = 0.0
    score += 0.35 if close >= sma_10 else -0.35
    score += 0.25 if macd >= macd_signal else -0.25
    score += 0.2 if rsi_14 < 70 else -0.2
    score += 0.2 if rsi_14 > 30 else -0.2

    up_prob = max(0.0, min(1.0, 0.5 + score * 0.5))
    down_prob = 1.0 - up_prob

    if up_prob >= 0.6:
        signal = "buy"
    elif down_prob >= 0.6:
        signal = "sell"
    else:
        signal = "hold"

    return {
        "signal": signal,
        "up_probability": round(up_prob, 4),
        "down_probability": round(down_prob, 4),
        "reason": "Demo rule-based output, replace with your model predictions.",
    }
