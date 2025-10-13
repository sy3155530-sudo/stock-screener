from http.server import BaseHTTPRequestHandler
import pandas as pd
import requests
import io

CSV_URL = "https://raw.githubusercontent.com/sy3155530-sudo/stock-screener/main/results.csv"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>每日美股筛选结果</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 40px; background: #f7f9fc; }
    h1 { color: #2c3e50; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; background: white; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
    th { background: #4CAF50; color: white; }
    tr:nth-child(even) { background: #f2f2f2; }
    footer { margin-top: 30px; color: #888; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>🚀 每日美股筛选结果</h1>
  {table_html}
  <footer>数据来源：Yahoo Finance | 自动更新系统</footer>
</body>
</html>
"""

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 忽略浏览器自动请求的站点图标
            if self.path.endswith("favicon.ico") or self.path.endswith("favicon.png"):
                self.send_response(200); self.end_headers(); self.wfile.write(b""); return

            r = requests.get(CSV_URL, timeout=10)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.text))
                table_html = df.to_html(index=False, border=0)
            else:
                table_html = "<p><b>⚠️ 未找到 results.csv，请稍后再试。</b></p>"

            html = HTML_TEMPLATE.format(table_html=table_html)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"<h3>⚠️ 无法从GitHub获取数据: {e}</h3>".encode("utf-8"))
