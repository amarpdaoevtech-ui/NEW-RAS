#!/bin/bash
echo "Following BMS Backend logs (Ctrl+C to exit)..."
sudo journalctl -u bms-backend.service -f
