from flask import Flask, render_template_string
import pandas as pd
import os

app = Flask(__name__)

@app.route('/')
def home():
    # 检查结果文件是否存在
    file_path = "output/results.csv"
    if not os.path.exists(file_path):
        return "<h2>🚀 结果文件未找到，请先运行 GitHub Actions 获取筛选结果。</h2>"

    # 读取结果
    df = pd.read_csv(file_path)
    if df.empty:
        return "<h2>😅 没有符合条件的股票。</h2>"

    # 转成HTML表格
    table_html = df.to_html(classes='table table-striped', index=False)

    # 网页模板
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>每日美股筛选结果</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-dark text-light">
        <div class="container mt-4">
            <h1 class="text-center text-warning">📈 每日美股筛选结果</h1>
            <p class="text-center text-secondary">自动更新（来自 GitHub Actions）</p>
            <div class="table-responsive bg-light text-dark p-3 rounded">
                {table_html}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
