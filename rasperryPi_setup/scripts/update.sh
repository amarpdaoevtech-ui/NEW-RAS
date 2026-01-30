#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Stopping services..."
sudo systemctl stop bms-backend.service

echo "Updating frontend..."
npm install
npm run build

echo "Updating backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

echo "Restarting services..."
sudo systemctl restart bms-backend.service
sudo systemctl restart nginx

echo "✅ Update complete"
