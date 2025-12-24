FROM python:3.11-slim

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml ./

# 依存関係のインストール（uvを使用）
RUN uv sync

# アプリケーションコードをコピー
COPY app/ ./app/

# 必要なディレクトリを作成
RUN mkdir -p /app/temp /app/data

EXPOSE 8000

# uvを使用してアプリケーションを起動
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
