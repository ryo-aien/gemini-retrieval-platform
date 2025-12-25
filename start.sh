#!/bin/bash
set -e

# Cloud RunのPORT環境変数をnginx設定に適用（デフォルト8080）
PORT=${PORT:-8080}
echo "Starting services on port $PORT..."

# nginx設定ファイルのポートを置換
sed -i "s/listen 8080;/listen $PORT;/g" /etc/nginx/sites-available/default

# nginx設定のテスト
nginx -t

# Backendを起動（バックグラウンドで8000番ポートで起動）
echo "Starting backend (uvicorn) on port 8000..."
cd /app/backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Backendの起動を待つ
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -f http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Nginxを起動（フォアグラウンド）
echo "Starting nginx on port $PORT..."
nginx -g "daemon off;"
