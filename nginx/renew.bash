#!/bin/bash

# 현재 경로에 있는 .env 파일 로드
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
else
  echo "❌ .env file not found in current directory."
  exit 1
fi

# DOMAIN 값 확인
if [ -z "$DOMAIN" ]; then
  echo "❌ DOMAIN variable not set in .env file."
  exit 1
fi

# certbot 설치 여부 확인
if ! command -v certbot &> /dev/null; then
  echo "⚙️ certbot not found. Installing..."
  sudo apt update
  sudo apt install -y certbot python3-certbot-nginx

  if [ $? -ne 0 ]; then
    echo "❌ Failed to install certbot. Exiting."
    exit 1
  fi
fi

# 인증서 갱신 시도
echo "▶️ Starting certbot renewal for domain: $DOMAIN"
sudo certbot renew --quiet --cert-name "$DOMAIN"

# 갱신 성공 여부 확인
if [ $? -eq 0 ]; then
  mkdir -p "./certbot/conf/$DOMAIN"
  mkdir -p "./certbot/renewal"
  cp -L "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "./certbot/conf/$DOMAIN/fullchain.pem"
  cp -L "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "./certbot/conf/$DOMAIN/privkey.pem"
  cp "/etc/letsencrypt/renewal/$DOMAIN.conf" "./certbot/renewal/$DOMAIN.conf"

  echo "✅ Cert for $DOMAIN renewed."
else
  echo "⚠️ Certbot renewal failed for $DOMAIN."
fi

