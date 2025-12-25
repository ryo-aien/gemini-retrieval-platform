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

# Cloud RunはPORT環境変数を使用するため、デフォルト値を設定
ENV PORT=8000
EXPOSE $PORT

# 本番環境用の起動コマンド（--reloadを削除し、PORTを環境変数から取得）
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
