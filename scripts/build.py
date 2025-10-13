# scripts/build.py
import datetime as dt
import pathlib
import pandas as pd

try:
    import yfinance as yf
except Exception:
    yf = None

# === 你可以改这里的股票清单 ===
TICKERS = ["AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","AMD","NFLX","AVGO"]

def fetch_prices(tickers):
    """逐只获取最新收盘价；失败则跳过，保证至少返回空表而不是报错。"""
    rows = []
    if yf is None:
        return pd.DataFrame(rows, columns=["Symbol","Price"])
    for t in tickers:
        try:
            h = yf.Ticker(t).history(period="5d", interval="1d", auto_adjust=True)
            if not h.empty:
                price = float(h["Close"].tail(1).iloc[0])
                rows.append({"Symbol": t, "Price": round(price, 2)})
        except Exception:
            # 忽略单只失败，继续
            continue
    return pd.DataFrame(rows, columns=["Symbol","Price"])

def build_html(df: pd.DataFrame) -> str:
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    if df is None or df.empty:
        table_html = "<p><b>⚠️ 暂无数据（可能被数据源限流）。请稍后在 Actions 里手动重跑。</b></p>"
    else:
        # 统一列
        cols = list(df.columns)
        if cols == ["Symbol"] or len(cols) == 1:
            df["Price"] = ""
        elif len(cols) >= 2:
            df = df[["Symbol","Price"]]
        table_html = df.to_html(index=False, border=0)

    return f"""<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8">
<title>每日美股筛选结果</title>
<style>
body{{font-family:Segoe UI,Arial;margin:40px;background:#f7f9fc}}
h1{{color:#2c3e50}} table{{border-collapse:collapse;width:100%;background:#fff;margin-top:20px}}
th,td{{border:1px solid #ddd;padding:8px;text-align:center}} th{{background:#4CAF50;color:#fff}}
tr:nth-child(even){{background:#f2f2f2}} footer{{margin-top:20px;color:#888}}
</style>
<h1>🚀 每日美股筛选结果</h1>
<p>更新时间：{now}</p>
{table_html}
<footer>数据源：Yahoo Finance（yfinance）｜静态站点（GitHub Pages）</footer>
</html>"""

def main():
    df = fetch_prices(TICKERS)
    html = build_html(df)
    pathlib.Path("site").mkdir(exist_ok=True)
    pathlib.Path("site/index.html").write_text(html, encoding="utf-8")
    print(f"✅ Generated site/index.html with {0 if df is None else len(df)} rows")

if __name__ == "__main__":
    main()
