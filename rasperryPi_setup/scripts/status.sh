#!/bin/bash
echo "=== BMS Backend Status ==="
sudo systemctl status bms-backend.service --no-pager
echo ""
echo "=== Nginx Status ==="
sudo systemctl status nginx --no-pager
echo ""
echo "=== Recent Logs ==="
sudo journalctl -u bms-backend.service -n 20 --no-pager
