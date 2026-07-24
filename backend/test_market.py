import asyncio
import yfinance as yf

async def main():
    tickers = "TCS.NS"
    data = yf.download(tickers, period='5d', group_by='ticker', auto_adjust=True, progress=False)
    sym = 'TCS.NS'
    if sym in data:
        print(data[sym]['Open'].iloc[-1])
    else:
        print('sym not in data', data.columns)

asyncio.run(main())
