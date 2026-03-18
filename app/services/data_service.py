from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import yfinance as yf


def fetch_stock_history(symbol: str, start: datetime, end: datetime) -> list[dict]:
    ticker = yf.Ticker(symbol)
    try:
        frame = ticker.history(start=start.date(), end=end.date(), auto_adjust=False)
    except Exception:
        frame = yf.download(
            symbol,
            start=start.date(),
            end=end.date(),
            auto_adjust=False,
            progress=False,
        )

    if frame.empty:
        frame = yf.download(
            symbol,
            start=start.date(),
            end=end.date(),
            auto_adjust=False,
            progress=False,
        )

    if frame.empty:
        return []

    frame = frame.reset_index()
    rows: list[dict] = []
    for _, row in frame.iterrows():
        rows.append(
            {
                "date": row["Date"].strftime("%Y-%m-%d"),
                "open": _safe_float(row.get("Open")),
                "high": _safe_float(row.get("High")),
                "low": _safe_float(row.get("Low")),
                "close": _safe_float(row.get("Close")),
                "adj_close": _safe_float(row.get("Adj Close")),
                "volume": int(row.get("Volume", 0) or 0),
            }
        )
    return rows


def fetch_news(symbol: str, limit: int = 20) -> list[dict]:
    rss_url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}"
        "&region=US&lang=en-US"
    )
    xml_text = _download_text(rss_url)
    root = ElementTree.fromstring(xml_text)
    items = root.findall("./channel/item")

    results: list[dict] = []
    for item in items[:limit]:
        title = _xml_text(item, "title")
        link = _xml_text(item, "link")
        pub_date_raw = _xml_text(item, "pubDate")
        pub_date = ""
        if pub_date_raw:
            try:
                pub_date = parsedate_to_datetime(pub_date_raw).isoformat()
            except (TypeError, ValueError):
                pub_date = pub_date_raw

        results.append(
            {
                "title": title,
                "url": link,
                "published_at": pub_date,
                "source": "Yahoo Finance RSS",
            }
        )
    return results


def _download_text(url: str) -> str:
    # Lazy import to avoid requiring requests if this module is not used.
    import requests

    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (StockResearchBot/1.0)"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.text


def _xml_text(node: ElementTree.Element, tag: str) -> str:
    child = node.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _safe_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
