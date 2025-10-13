from flask import Flask, render_template_string
import pandas as pd
import requests

app = Flask(__name__)

# 你的GitHub Raw文件路径（请替换成自己的仓库地址）
CSV_URL = "https://raw.githubusercontent.com/sy3155530-sudo/stock-screener/main/results.csv"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
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
    {% if table_html %}
        {{ table_html | safe }}
    {% else %}
        <p><b>结果文件未找到，请先运行 GitHub Actions 生成 results.csv。</b></p>
    {% endif %}
    <footer>数据来源：Yahoo Finance | 自动更新系统</footer>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        response = requests.get(CSV_URL, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(pd.compat.StringIO(response.text))
            table_html = df.to_html(index=False)
            return render_template_string(HTML_TEMPLATE, table_html=table_html)
        else:
            return render_template_string(HTML_TEMPLATE, table_html=None)
    except Exception as e:
        return f"<h3>⚠️ 无法从GitHub获取数据: {e}</h3>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
