# ビルドステージ
FROM node:20-alpine AS builder

WORKDIR /app

# 依存関係をインストール
COPY package*.json ./
RUN npm ci

# アプリケーションコードをコピー
COPY . .

# ビルド時の環境変数を設定
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# 本番ビルドを実行
RUN npm run build

# 本番ステージ
FROM nginx:alpine

# ビルド成果物をnginxの公開ディレクトリにコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx設定をコピー
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud RunはPORT環境変数を使用するため、envsubstで置換するスクリプトを作成
RUN apk add --no-cache bash && \
    echo '#!/bin/bash' > /docker-entrypoint.sh && \
    echo 'PORT=${PORT:-8080}' >> /docker-entrypoint.sh && \
    echo 'envsubst '"'"'$PORT'"'"' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf' >> /docker-entrypoint.sh && \
    echo 'nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# テンプレートとして保存
RUN mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.template

ENV PORT=8080
EXPOSE $PORT

CMD ["/docker-entrypoint.sh"]
