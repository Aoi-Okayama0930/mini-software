# ベースイメージを指定
FROM python:3.11-slim

# 作業ディレクトリを作成，設定
WORKDIR /myapp

# 必要なファイルをコンテナ内にコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

## アプリケーションのコードをコピー（マウントするからいい）
#COPY . .

# アプリケーションのエントリーポイントを指定
# 開発中のみ--reloadオプションをつける
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "3000"]

