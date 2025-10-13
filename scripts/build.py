# scripts/build.py
import yfinance as yf, pandas as pd, datetime as dt, pathlib
# ========== 你可以随时修改这里的股票列表 ==========
TICKERS = ["AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","AMD","NFLX","AVGO"]

# 最近价格（示例：取最近1天收盘；你也可以换成你的筛选结果DataFrame）
df = yf.download(" ".join(TICKERS), period="6mo", interval="1d", auto_adjust=True)["Close"].tail(1).T
df.reset_index(inplace=True); df.columns=["Symbol","Price"]; df["Price"]=df["Price"].round(2)

now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
html = f"""<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8">
<title>每日美股筛选结果</title>
<style>
body{{font-family:Segoe UI,Arial;margin:40px;background:#f7f9fc}}
h1{{color:#2c3e50}} table{{border-collapse:collapse;width:100%;background:#fff;margin-top:20px}}
th,td{{border:1px solid #ddd;padding:8px;text-align:center}} th{{background:#4CAF50;color:#fff}}
tr:nth-child(even){{background:#f2f2f2}} footer{{margin-top:20px;color:#888}}
</style>
<h1>🚀 每日美股筛选结果</h1>
<p>更新时间：{now}</p>
{df.to_html(index=False, border=0)}
<footer>数据源：Yahoo Finance（yfinance）｜全部静态，无后端</footer></html>"""

pathlib.Path("site").mkdir(exist_ok=True)
open("site/index.html","w",encoding="utf-8").write(html)
print("✅ Generated site/index.html")
