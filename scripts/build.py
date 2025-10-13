import requests
import pandas as pd
import datetime as dt
import pathlib

# === 你的 Twelve Data API Key ===
API_KEY = "dffc5f3caf764b20af688cdd13bbaf98"

# === 你想追踪的股票 ===
TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "GOOGL", "NFLX", "AMD", "AVGO"]

def fetch_prices(tickers):
    """从 Twelve Data 获取股票价格"""
    rows = []
    for t in tickers:
        try:
            url = f"https://api.twelvedata.com/price?symbol={t}&apikey={API_KEY}"
            r = requests.get(url, timeout=5).json()
            if "price" in r:
                price = float(r["price"])
                rows.append({"Symbol": t, "Price": round(price, 2)})
            else:
                print(f"⚠️ 无法获取 {t} 的数据: {r}")
        except Exception as e:
            print(f"❌ {t} 错误: {e}")
    return pd.DataFrame(rows, columns=["Symbol", "Price"])

def build_html(df):
    """生成网页 HTML"""
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    if df.empty:
        table_html = "<p>⚠️ 暂无数据，请稍后再试。</p>"
    else:
        table_html = df.to_html(index=False, border=0, justify="center")

    html = f"""
    <html>
    <meta charset="utf-8">
    <title>每日美股筛选结果</title>
    <body style="font-family:Arial; background:#f7f9fc; margin:40px;">
        <h1>🚀 每日美股筛选结果</h1>
        <p>更新时间：{now}</p>
        {table_html}
        <footer style="margin-top:30px; color:gray;">
            数据源：Twelve Data ｜ 自动发布：GitHub Actions
        </footer>
    </body>
    </html>
    """
    return html

def main():
    print("⏳ 正在获取股票数据...")
    df = fetch_prices(TICKERS)
    html = build_html(df)
    pathlib.Path("site").mkdir(exist_ok=True)
    pathlib.Path("site/index.html").write_text(html, encoding="utf-8")
    print("✅ 已生成 site/index.html 文件")

if __name__ == "__main__":
    main()
