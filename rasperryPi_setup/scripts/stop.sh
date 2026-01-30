#!/bin/bash
echo "Stopping BMS Backend..."
sudo systemctl stop bms-backend.service
echo "Stopping Nginx..."
sudo systemctl stop nginx
echo "✅ Services stopped"
