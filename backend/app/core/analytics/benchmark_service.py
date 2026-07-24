import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BenchmarkService:
    # Supported benchmarks mapping to Yahoo Finance symbols
    BENCHMARKS = {
        'Nifty 50': '^NSEI',
        'Sensex': '^BSESN',
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC',
        'MSCI World': 'URTH'  # Using iShares MSCI World ETF as proxy
    }
    
    # Simple in-memory cache
    _cache: Dict[str, Any] = {}
    _cache_time: datetime = datetime.min
    CACHE_TTL_HOURS = 24

    @classmethod
    def get_benchmarks_performance(cls) -> list[Dict[str, Any]]:
        """Fetches the 1-year performance of major benchmarks. Uses cache to avoid API limits."""
        now = datetime.now()
        
        # Return cache if valid
        if cls._cache and (now - cls._cache_time) < timedelta(hours=cls.CACHE_TTL_HOURS):
            return cls._cache.get("benchmarks", [])
            
        logger.info("Cache miss or expired. Fetching benchmark data from Yahoo Finance.")
        results = []
        
        symbols = list(cls.BENCHMARKS.values())
        tickers_str = " ".join(symbols)
        
        try:
            # Fetch 1 year of historical data to calculate 1Y returns
            # For simplicity, we just use the 1y period
            data = yf.download(tickers_str, period="1y", group_by="ticker", auto_adjust=True, progress=False)
            
            for name, symbol in cls.BENCHMARKS.items():
                if symbol in data:
                    sym_data = data[symbol]
                    if not sym_data.empty and 'Close' in sym_data:
                        closes = sym_data['Close'].dropna()
                        if len(closes) > 0:
                            current_price = closes.iloc[-1]
                            # Try to get the price from approx 1 year ago (first row of the 1y period)
                            year_ago_price = closes.iloc[0]
                            
                            if year_ago_price > 0:
                                return_pct = ((current_price - year_ago_price) / year_ago_price) * 100
                            else:
                                return_pct = 0.0
                                
                            results.append({
                                "name": name,
                                "return_pct": round(float(return_pct), 2),
                                "current_value": round(float(current_price), 2)
                            })
                            
            # Update cache
            cls._cache["benchmarks"] = results
            cls._cache_time = now
            
        except Exception as e:
            logger.error(f"Failed to fetch benchmarks: {e}")
            # If fetch fails but we have old cache, return old cache
            if cls._cache:
                return cls._cache.get("benchmarks", [])
                
        return results
