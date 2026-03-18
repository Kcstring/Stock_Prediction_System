from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.backtest_service import latest_realized_comparison, run_backtest
from app.services.data_service import fetch_news, fetch_stock_history
from app.services.indicator_service import add_indicators
from app.services.prediction_service import build_demo_prediction
from app.services.storage_service import (
    delete_symbol_data,
    get_data_summary,
    get_news_rows,
    get_stock_rows,
    init_db,
    list_symbols_summary,
    save_news_rows,
    save_stock_rows,
)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web"

app = FastAPI(
    title="Stock Causal-Multimodal Demo",
    description="Web API for stock/news fetching and visualization demo.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class DataFetchRequest(BaseModel):
    symbol: str = Field(..., description="Ticker symbol, e.g. AAPL")
    start: str | None = Field(default=None, description="Start date YYYY-MM-DD")
    end: str | None = Field(default=None, description="End date YYYY-MM-DD")
    news_limit: int = Field(default=20, ge=1, le=100)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()


@app.get("/")
async def index() -> FileResponse:
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "message": "service is running"}


def _parse_range(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    try:
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.utcnow()
        start_dt = (
            datetime.strptime(start, "%Y-%m-%d")
            if start
            else end_dt - timedelta(days=365)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD") from exc

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="start must be earlier than end")
    return start_dt, end_dt


@app.post("/api/data/fetch")
async def fetch_and_store_data(payload: DataFetchRequest) -> dict:
    symbol = payload.symbol.upper()
    start_dt, end_dt = _parse_range(payload.start, payload.end)

    stock_rows = fetch_stock_history(symbol=symbol, start=start_dt, end=end_dt)
    if not stock_rows:
        raise HTTPException(status_code=404, detail=f"No stock data found for {symbol}")

    try:
        news_items = fetch_news(symbol=symbol, limit=payload.news_limit)
    except Exception:
        news_items = []

    saved_stock = save_stock_rows(symbol=symbol, rows=stock_rows)
    saved_news = save_news_rows(symbol=symbol, items=news_items)
    summary = get_data_summary(symbol)

    return {
        "symbol": symbol,
        "saved_stock_rows": saved_stock,
        "saved_news_rows": saved_news,
        "total_stock_rows_in_db": summary["stock_rows"],
        "total_news_rows_in_db": summary["news_rows"],
        "message": "Data fetch completed and saved to database.",
    }


@app.get("/api/data/stocks")
async def get_stored_symbols() -> dict:
    items = list_symbols_summary()
    return {
        "count": len(items),
        "items": items,
    }


@app.delete("/api/data/stocks/{symbol}")
async def delete_stored_symbol(symbol: str) -> dict:
    target = symbol.upper()
    deleted = delete_symbol_data(target)
    if deleted["stock_deleted"] == 0 and deleted["news_deleted"] == 0:
        raise HTTPException(status_code=404, detail=f"No data found for {target}")
    return {
        "symbol": target,
        "deleted_stock_rows": deleted["stock_deleted"],
        "deleted_news_rows": deleted["news_deleted"],
        "message": "Data deleted from database.",
    }


@app.get("/api/visualization")
async def get_visualization(
    symbol: str = Query(..., description="Ticker symbol, e.g. AAPL"),
    start: str | None = Query(None, description="Start date: YYYY-MM-DD"),
    end: str | None = Query(None, description="End date: YYYY-MM-DD"),
    limit: int = Query(20, ge=1, le=100),
    train_ratio: float = Query(0.7, ge=0.5, le=0.95),
) -> dict:
    symbol = symbol.upper()
    start_dt, end_dt = _parse_range(start, end)
    rows = get_stock_rows(
        symbol=symbol,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No data found in database. Please run data fetch first.",
        )

    with_indicator = add_indicators(rows)
    total_rows = len(with_indicator)
    split_idx = max(2, int(total_rows * train_ratio))
    split_idx = min(split_idx, total_rows - 1)

    train_rows = with_indicator[:split_idx]
    test_rows = with_indicator[split_idx:]

    final_prediction = build_demo_prediction(with_indicator)
    backtest = run_backtest(with_indicator, start_index=split_idx)
    latest_compare = latest_realized_comparison(with_indicator)
    items = get_news_rows(symbol=symbol, limit=limit)

    return {
        "symbol": symbol,
        "rows": with_indicator,
        "dataset_split": {
            "train_ratio": train_ratio,
            "total_rows": total_rows,
            "train_rows": len(train_rows),
            "test_rows": len(test_rows),
            "train_start_date": train_rows[0]["date"] if train_rows else None,
            "train_end_date": train_rows[-1]["date"] if train_rows else None,
            "test_start_date": test_rows[0]["date"] if test_rows else None,
            "test_end_date": test_rows[-1]["date"] if test_rows else None,
        },
        "final_prediction": {
            **final_prediction,
            "target": "next_trading_day",
            "has_ground_truth": False,
            "note": "Final prediction targets the next trading day and has no realized label yet.",
        },
        "latest_realized_comparison": latest_compare,
        "backtest": backtest,
        "count": len(items),
        "items": items,
    }


@app.post("/api/model/train")
async def train_model_placeholder() -> dict:
    return {
        "status": "pending",
        "message": "Model processing module placeholder only. "
        "Training implementation is pending.",
    }
