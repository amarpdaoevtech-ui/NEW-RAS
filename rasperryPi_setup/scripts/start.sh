#!/bin/bash
echo "Starting BMS Backend..."
sudo systemctl start bms-backend.service
echo "Starting Nginx..."
sudo systemctl start nginx
echo "✅ Services started"
