from flask import Flask, render_template_string
import pandas as pd
import yfinance as yf
import datetime

app = Flask(__name__)

MIN_MARKET_CAP = 1_000_000_000  # 最小市值：10亿美元
TODAY = datetime.date.today()

def get_us_tickers():
    """获取标普500股票代码"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    return tables[0]['Symbol'].tolist()

def analyze_ticker(symbol):
    """分析股票：EMA20 > EMA40"""
    try:
        data = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if len(data) < 60:
            return None
        data["EMA20"] = data["Close"].ewm(span=20).mean()
        data["EMA40"] = data["Close"].ewm(span=40).mean()
        if data["EMA20"].iloc[-1] > data["EMA40"].iloc[-1]:
            info = yf.Ticker(symbol).info
            if info.get('marketCap', 0) >= MIN_MARKET_CAP:
                return {
                    "Symbol": symbol,
                    "MarketCap(USD)": round(info.get('marketCap', 0) / 1e9, 2),
                    "Close": round(data["Close"].iloc[-1], 2)
                }
    except Exception:
        return None
    return None

@app.route("/")
def home():
    tickers = get_us_tickers()
    results = []
    for sym in tickers:
        res = analyze_ticker(sym)
        if res:
            results.append(res)
    if results:
        df = pd.DataFrame(results)
        table_html = df.to_html(index=False, justify="center", border=0)
        return render_template_string("""
        <html>
        <head>
        <title>Daily Stock Screener</title>
        <style>
            body { font-family: Arial; background: #111; color: #eee; text-align:center; }
            table { margin:auto; border-collapse: collapse; background:#222; }
            th, td { padding:8px 16px; border:1px solid #333; }
            th { background:#333; color:#0f0; }
            td { color:#ccc; }
        </style>
        </head>
        <body>
            <h2>📊 Stock Screener Result ({{date}})</h2>
            {{table|safe}}
        </body></html>
        """, table=table_html, date=TODAY)
    else:
        return f"<h3 style='color:white;'>No qualified stocks found for {TODAY}</h3>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
