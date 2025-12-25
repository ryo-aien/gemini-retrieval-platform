# ===============================
# Stage 1: Frontend Build
# ===============================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 依存関係をインストール
COPY frontend/package*.json ./
RUN npm ci

# フロントエンドコードをコピー
COPY frontend/ ./

# ビルド時の環境変数を設定（Cloud Run上では/apiにプロキシされる）
ENV VITE_API_URL=""

# 本番ビルドを実行
RUN npm run build

# ===============================
# Stage 2: Backend Setup
# ===============================
FROM python:3.11-slim AS backend-builder

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app/backend

# 依存関係ファイルをコピー
COPY backend/pyproject.toml ./

# 依存関係のインストール
RUN uv sync

# ===============================
# Stage 3: Final Production Image
# ===============================
FROM python:3.11-slim

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y nginx curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# uvをコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Backendの依存関係をコピー
COPY --from=backend-builder /app/backend/.venv /app/backend/.venv
COPY backend/pyproject.toml /app/backend/

# Backendのアプリケーションコードをコピー
COPY backend/app /app/backend/app

# Frontendのビルド成果物をコピー
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 必要なディレクトリを作成
RUN mkdir -p /app/backend/temp /app/backend/data

# nginx設定ファイルをコピー
COPY nginx-unified.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# 起動スクリプトをコピー
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Cloud RunのPORT環境変数に対応
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE $PORT

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# 起動スクリプトを実行
CMD ["/app/start.sh"]
