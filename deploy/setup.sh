#!/bin/bash
# Первичная настройка / обновление на Ubuntu 22.04
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/steam-auth/app}"

echo "==> SABR RUST deploy in $APP_DIR"

cd "$APP_DIR"

if ! command -v python3 >/dev/null; then
  sudo apt update
  sudo apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx ufw
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

sudo cp deploy/nginx.sabrrust.online.conf /etc/nginx/sites-available/sabrrust.online
sudo ln -sf /etc/nginx/sites-available/sabrrust.online /etc/nginx/sites-enabled/sabrrust.online
sudo rm -f /etc/nginx/sites-enabled/default

sudo cp deploy/sabrrust-web.service /etc/systemd/system/sabrrust-web.service
sudo systemctl daemon-reload
sudo systemctl enable sabrrust-web
sudo systemctl restart sabrrust-web

sudo nginx -t
sudo systemctl reload nginx

echo "Done. Check: systemctl status sabrrust-web"
