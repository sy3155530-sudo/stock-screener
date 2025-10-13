import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt

# === 参数 ===
MIN_MARKET_CAP = 1_000_000_000   # 最小市值：10亿美元
TODAY = dt.date.today()

# === 获取美股主板股票（NASDAQ + NYSE + AMEX） ===
import pandas as pd

def get_us_tickers():
    # 从维基百科获取 S&P 500 股票列表
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    tickers = tables[0]["Symbol"].tolist()
    return tickers

# === 分析逻辑（简化示例） ===
def analyze_ticker(symbol):
    try:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if len(data) < 60:
            return None
        data["EMA20"] = data["Close"].ewm(span=20).mean()
        data["EMA60"] = data["Close"].ewm(span=60).mean()
        data["EMA120"] = data["Close"].ewm(span=120).mean()
        cond = (
            (data["EMA20"].iloc[-1] > data["EMA60"].iloc[-1]) and
            (data["EMA60"].iloc[-1] > data["EMA120"].iloc[-1])
        )
        if cond:
            info = yf.Ticker(symbol).info
            if info.get("marketCap", 0) > MIN_MARKET_CAP:
                return {
                    "Symbol": symbol,
                    "MarketCap(USD)": info.get("marketCap", 0),
                    "Close": round(data["Close"].iloc[-1], 2)
                }
    except Exception:
        return None
    return None

# === 主程序 ===
def main():
    print(f"🚀 开始分析股票（截至 {TODAY}）...")
    tickers = get_us_tickers()
    results = []

    for symbol in tickers:
        res = analyze_ticker(symbol)
        if res:
            results.append(res)

    if results:
        df = pd.DataFrame(results)
        df.to_csv("results.csv", index=False)
        print(f"✅ 分析完成，共找到 {len(df)} 支股票。结果已保存为 results.csv")
    else:
        print("😅 没有符合条件的股票。")

if __name__ == "__main__":
    main()
