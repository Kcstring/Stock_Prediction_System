import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "stock_system.db"


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_prices (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                published_at TEXT,
                source TEXT,
                fetched_at TEXT DEFAULT (datetime('now')),
                UNIQUE(symbol, url, published_at)
            )
            """
        )
        conn.commit()


def save_stock_rows(symbol: str, rows: list[dict]) -> int:
    if not rows:
        return 0

    payload = [
        (
            symbol,
            row.get("date"),
            row.get("open"),
            row.get("high"),
            row.get("low"),
            row.get("close"),
            row.get("adj_close"),
            row.get("volume"),
        )
        for row in rows
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT INTO stock_prices(symbol, date, open, high, low, close, adj_close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                adj_close=excluded.adj_close,
                volume=excluded.volume
            """,
            payload,
        )
        conn.commit()
    return len(payload)


def save_news_rows(symbol: str, items: list[dict]) -> int:
    if not items:
        return 0

    payload = [
        (
            symbol,
            item.get("title") or "",
            item.get("url"),
            item.get("published_at"),
            item.get("source"),
        )
        for item in items
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO news_items(symbol, title, url, published_at, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            payload,
        )
        conn.commit()
    return len(payload)


def get_stock_rows(symbol: str, start: str, end: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT date, open, high, low, close, adj_close, volume
            FROM stock_prices
            WHERE symbol = ? AND date >= ? AND date <= ?
            ORDER BY date ASC
            """,
            (symbol, start, end),
        ).fetchall()

    return [dict(row) for row in rows]


def get_news_rows(symbol: str, limit: int = 20) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT title, url, published_at, source
            FROM news_items
            WHERE symbol = ?
            ORDER BY published_at DESC, id DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def get_data_summary(symbol: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        stock_count = conn.execute(
            "SELECT COUNT(*) FROM stock_prices WHERE symbol = ?",
            (symbol,),
        ).fetchone()[0]
        news_count = conn.execute(
            "SELECT COUNT(*) FROM news_items WHERE symbol = ?",
            (symbol,),
        ).fetchone()[0]
    return {"stock_rows": stock_count, "news_rows": news_count}


def list_symbols_summary() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT
                sp.symbol AS symbol,
                COUNT(sp.date) AS stock_rows,
                MIN(sp.date) AS start_date,
                MAX(sp.date) AS end_date,
                (
                    SELECT COUNT(*)
                    FROM news_items ni
                    WHERE ni.symbol = sp.symbol
                ) AS news_rows
            FROM stock_prices sp
            GROUP BY sp.symbol
            ORDER BY sp.symbol ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def delete_symbol_data(symbol: str) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        stock_deleted = conn.execute(
            "DELETE FROM stock_prices WHERE symbol = ?",
            (symbol,),
        ).rowcount
        news_deleted = conn.execute(
            "DELETE FROM news_items WHERE symbol = ?",
            (symbol,),
        ).rowcount
        conn.commit()
    return {"stock_deleted": stock_deleted, "news_deleted": news_deleted}
