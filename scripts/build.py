# scripts/build.py
# 功能：用 Finnhub 扫描全美股（排除OTC），按你的 TOS 条件 + 市值>10亿美元，生成 site/index.html 和 results.csv
import os, time, math, json, pathlib, datetime as dt
import requests
import pandas as pd
import numpy as np

API_KEY = "d3mmt09r01qmso34imfgd3mmt09r01qmso34img0"  # 你提供的 Finnhub Key
BASE = "https://finnhub.io/api/v1"
# 速率限制（免费 60/分钟），留点余量
RATE_LIMIT_PER_MIN = 55

# 选择主板交易所（排除OTC/pink），常见 MIC：
MAIN_EX_MICS = {"XNYS", "XNAS", "XASE", "ARCX", "BATS"}  # 纽交所、纳斯达克、美国证交所、Arca、BATS

def rate_limiter(counter, start_ts):
    if counter >= RATE_LIMIT_PER_MIN:
        elapsed = time.time() - start_ts
        if elapsed < 60:
            time.sleep(60 - elapsed + 0.5)
        return 0, time.time()
    return counter, start_ts

def get_symbols():
    """获取美股全列表，过滤非主板"""
    url = f"{BASE}/stock/symbol?exchange=US&token={API_KEY}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    syms = r.json()
    df = pd.DataFrame(syms)
    # 兼容字段：有的返回 mic，有的可能没有；尽量用 mic/type 过滤
    if "mic" in df.columns:
        df = df[df["mic"].isin(MAIN_EX_MICS)]
    if "type" in df.columns:
        df = df[df["type"].isin(["Common Stock", "ADR", "ETF", "EQUITY"])]
    # 去重、只要 symbol 和 description
    keep_cols = [c for c in ["symbol", "description", "mic"] if c in df.columns]
    df = df[keep_cols].drop_duplicates("symbol")
    return df

def get_profile(symbol):
    """取公司概况（含市值），用于市值过滤"""
    url = f"{BASE}/stock/profile2?symbol={symbol}&token={API_KEY}"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return {}
    return r.json() or {}

def get_daily_candles(symbol, days=260):
    """取日线K线（保证EMA/MA计算足够），返回 DataFrame(index by date)"""
    to_ts = int(time.time())
    frm_ts = to_ts - int(days * 86400 * 1.5)  # 给足余量
    url = f"{BASE}/stock/candle?symbol={symbol}&resolution=D&from={frm_ts}&to={to_ts}&token={API_KEY}"
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return pd.DataFrame()
    data = r.json()
    if not data or data.get("s") != "ok":
        return pd.DataFrame()
    df = pd.DataFrame({
        "t": data["t"],
        "o": data["o"],
        "h": data["h"],
        "l": data["l"],
        "c": data["c"],
        "v": data["v"],
    })
    df["date"] = pd.to_datetime(df["t"], unit="s", utc=True).dt.tz_convert("America/Edmonton").dt.date
    df = df.sort_values("date").drop_duplicates("date").set_index("date")
    return df[["o", "c", "h", "l", "v"]]

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def apply_tos_logic(df):
    """
    将你的 TOS 条件翻译为 pandas 版本，返回是否满足最终条件的布尔值（看最后一行）
    变量说明：使用日线的 open/close 及 EMA/MA 指标。
    """
    if df.shape[0] < 130:  # 需要足够K线
        return False

    close = df["c"]
    open_ = df["o"]

    # 均线
    MA20  = close.rolling(20).mean()
    EMA20 = ema(close, 20)
    MA60  = close.rolling(60).mean()
    EMA60 = ema(close, 60)
    MA120 = close.rolling(120).mean()
    EMA120 = ema(close, 120)

    # 条件组
    mid_today = (close + open_) / 2
    mid_ma20 = (EMA20 + MA20) / 2
    mid_ma60 = (EMA60 + MA60) / 2
    mid_ma120 = (EMA120 + MA120) / 2

    COND1 = ( (mid_today - mid_ma20).abs() <= close * 0.03 ) & ( (close + open_) < (EMA60 + MA60) ) & ( (close + open_) < (EMA120 + MA120) )
    COND2 = ( mid_today < mid_ma20 ) & ( (EMA20 + MA20) < (EMA60 + MA60) ) & ( (EMA20 + MA20) < (EMA120 + MA120) )

    CS = (close - EMA20) / EMA20 * 100
    SM = (EMA20 - EMA60) / EMA60 * 100
    ML = (EMA60 - EMA120) / EMA120 * 100

    COND3 = (SM < 0) & (CS > SM) & (CS > ML)
    COND4 = (CS < 0) & (SM < 0) & (CS > SM) & (ML > SM)

    DIF  = ema(close, 13) - ema(close, 26)
    DEA  = ema(DIF, 9)
    MACD = (DIF - DEA) * 2

    COND5 = (DIF > DEA) & (MACD > 0)
    COND6 = (DIF < 0) & (DEA < 0)

    YESTERDAY = COND2.shift(1) & COND4.shift(1) & COND6.shift(1)
    TODAY     = COND1 & COND3 & COND5
    FINAL     = YESTERDAY & TODAY & (EMA20 > EMA20.shift(1))

    # 只看最后一根K线是否满足
    return bool(FINAL.iloc[-1])

def build_html(df):
    now = dt.datetime.now(tz=dt.timezone(dt.timedelta(hours=-6))).strftime("%Y-%m-%d %H:%M (Calgary)")
    if df.empty:
        table_html = "<p><b>⚠️ 本次扫描未找到符合条件的股票，或请求受限。</b></p>"
    else:
        table_html = df.sort_values("Symbol").to_html(index=False, border=0)
    return f"""<!DOCTYPE html><html lang="zh-CN"><meta charset="utf-8">
<title>每日美股筛选结果</title>
<style>
body{{font-family:Segoe UI,Arial;margin:40px;background:#f7f9fc}}
h1{{color:#2c3e50}} table{{border-collapse:collapse;width:100%;background:#fff;margin-top:20px}}
th,td{{border:1px solid #ddd;padding:8px;text-align:center}} th{{background:#4CAF50;color:#fff}}
tr:nth-child(even){{background:#f2f2f2}} footer{{margin-top:20px;color:#888}}
</style>
<h1>🚀 每日美股筛选结果（Finnhub 版）</h1>
<p>更新时间：{now}｜条件：市值>10亿美元 + 你的TOS均线/MACD反转逻辑</p>
{table_html}
<footer>数据：Finnhub.io（日线）｜自动发布：GitHub Actions</footer>
</html>"""

def main():
    out_dir = pathlib.Path("site"); out_dir.mkdir(exist_ok=True)

    print("⏳ 获取主板股票列表 ...")
    symbols_df = get_symbols()
    print(f"✅ 候选股票数：{len(symbols_df)}")

    results = []
    req_counter, window_start = 0, time.time()

    for i, row in symbols_df.iterrows():
        sym = row["symbol"]

        # 市值过滤（先查 profile 再查K线，节省请求）
        req_counter += 1
        req_counter, window_start = rate_limiter(req_counter, window_start)
        prof = get_profile(sym)
        mktcap = prof.get("marketCapitalization") or 0
        if mktcap < 1_000:  # 单位：百万美元（Finnhub 返回单位一般是百万）
            continue

        # 取K线
        req_counter += 1
        req_counter, window_start = rate_limiter(req_counter, window_start)
        df = get_daily_candles(sym, days=260)
        if df.empty:
            continue

        try:
            if apply_tos_logic(df):
                last_close = float(df["c"].iloc[-1])
                results.append({"Symbol": sym, "LastClose": round(last_close, 2), "MktCap($M)": int(mktcap)})
        except Exception:
            # 单只失败跳过
            continue

    res_df = pd.DataFrame(results, columns=["Symbol", "LastClose", "MktCap($M)"])
    # 保存 CSV + HTML
    res_df.to_csv("site/results.csv", index=False)
    html = build_html(res_df)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"✅ 完成：匹配 {len(res_df)} 只；文件已写入 site/index.html & site/results.csv")

if __name__ == "__main__":
    main()
