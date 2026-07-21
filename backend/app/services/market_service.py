import yfinance as yf
import logging

logger = logging.getLogger(__name__)

async def fetch_eod_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetches the End-of-Day (EOD) closing prices for a list of symbols.
    For Indian stocks, it automatically appends '.NS' if not present and the symbol doesn't contain a dot.
    """
    if not symbols:
        return {}

    # Format symbols for Yahoo Finance
    formatted_symbols = []
    symbol_mapping = {} # Map formatted symbol back to original symbol
    
    for symbol in symbols:
        original = symbol
        # Basic check to append .NS for Indian stocks if no suffix exists
        if "." not in symbol:
            symbol = f"{symbol}.NS"
        formatted_symbols.append(symbol)
        symbol_mapping[symbol] = original

    logger.info(f"Fetching EOD prices for: {formatted_symbols}")
    
    try:
        from datetime import datetime
        import pytz
        
        # Check current time in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist_tz)
        
        # Indian market hours: 9:15 AM to 3:30 PM (15:30)
        # Weekdays: Monday(0) to Friday(4)
        is_market_open = False
        if now_ist.weekday() < 5:
            current_time = now_ist.time()
            market_start = datetime.strptime("09:15", "%H:%M").time()
            market_end = datetime.strptime("15:30", "%H:%M").time()
            if market_start <= current_time <= market_end:
                is_market_open = True
                
        price_col = 'Open' if is_market_open else 'Close'
        logger.info(f"Market is open: {is_market_open}. Using price column: {price_col}")

        # Bulk fetch using yfinance. We request 5 days to ensure we get the last closing price even over weekends/holidays.
        tickers = " ".join(formatted_symbols)
        data = yf.download(tickers, period='5d', group_by='ticker', auto_adjust=True, progress=False)
        
        results = {}
        
        # yfinance download returns a pandas DataFrame.
        # With group_by='ticker', it always returns a MultiIndex where the top level is the ticker symbol.
        for sym in formatted_symbols:
            if sym in data:
                sym_data = data[sym]
                if not sym_data.empty and price_col in sym_data:
                    last_price = sym_data[price_col].dropna().iloc[-1]
                    results[symbol_mapping[sym]] = float(last_price)
                    
        return results

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return {}
