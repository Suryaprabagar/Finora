import yfinance as yf
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_eod_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetches the End-of-Day (EOD) closing prices for a list of symbols.
    For Indian stocks, it automatically appends '.NS' if not present and the symbol doesn't contain a dot.
    Always uses the most recent Close price for consistency (BUG-029 fix: avoid using Open price
    during market hours, which is stale from the morning opening).
    """
    if not symbols:
        return {}

    # Format symbols for Yahoo Finance
    formatted_symbols = []
    symbol_mapping = {}  # Map formatted symbol back to original symbol

    for symbol in symbols:
        original = symbol
        # Basic check to append .NS for Indian stocks if no suffix exists
        if "." not in symbol:
            symbol = f"{symbol}.NS"
        formatted_symbols.append(symbol)
        symbol_mapping[symbol] = original

    logger.info(f"Fetching EOD prices for: {formatted_symbols}")

    try:
        tickers = " ".join(formatted_symbols)

        # BUG-015 fix: yf.download() is synchronous and blocking. Offload to a thread
        # pool executor so the FastAPI async event loop is not blocked.
        # BUG-029 fix: always use the most recent Close price — using Open during market hours
        # is stale data. A live price requires yf.Ticker.fast_info which is a separate call.
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: yf.download(tickers, period='5d', group_by='ticker', auto_adjust=True, progress=False)
        )

        results = {}

        # yfinance download returns a pandas DataFrame.
        # With group_by='ticker', it always returns a MultiIndex where the top level is the ticker symbol.
        for sym in formatted_symbols:
            if sym in data:
                sym_data = data[sym]
                if not sym_data.empty and 'Close' in sym_data:
                    last_price = sym_data['Close'].dropna().iloc[-1]
                    results[symbol_mapping[sym]] = float(last_price)

        return results

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return {}
