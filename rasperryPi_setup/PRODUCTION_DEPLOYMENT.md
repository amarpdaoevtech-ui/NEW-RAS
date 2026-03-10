# 🚀 Complete Production Deployment Guide
## DAO EV Tech - Raspberry Pi Kiosk Mode Setup

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Pre-Installation Steps](#pre-installation-steps)
4. [Installation Process](#installation-process)
5. [Configuration](#configuration)
6. [Running the System](#running-the-system)
7. [Management & Maintenance](#management--maintenance)
8. [Troubleshooting](#troubleshooting)
9. [Adding New Bike Models](#adding-new-bike-models)

---

## 🎯 Overview

This guide will help you set up a **production-ready, auto-starting kiosk mode dashboard** on Raspberry Pi 4 for real-time BMS data monitoring on your e-bike.

### What You'll Get:
- ✅ **Auto-start on boot** - Dashboard starts automatically when powered on
- ✅ **Kiosk mode** - Full-screen display, no distractions
- ✅ **Database logging** - All data saved to SQLite database
- ✅ **Configuration-based** - Switch bike models by editing .env file
- ✅ **Production-ready** - Systemd services, Nginx reverse proxy
- ✅ **Easy management** - Simple scripts for start/stop/logs

---

## 🔧 Hardware Requirements

### Required:
- **Raspberry Pi 4** (2GB RAM minimum, 4GB recommended)
- **MicroSD Card** (16GB minimum, 32GB recommended, Class 10)
- **7-inch HDMI Display** (1024x600 resolution)
- **RS-485 HAT/Module** for Raspberry Pi
- **Power Supply** (5V 3A official Raspberry Pi adapter)
- **DAO BMS** with RS-485 output
- **RS-485 Cable** (A+, B-, GND)

### Optional:
- **Case** for Raspberry Pi with display
- **Cooling fan** (recommended for continuous operation)
- **UPS/Battery backup** for clean shutdowns

---

## 📥 Pre-Installation Steps

### 1. Flash Raspberry Pi OS

1. **Download Raspberry Pi Imager:**
   - Windows/Mac/Linux: https://www.raspberrypi.com/software/

2. **Flash the OS:**
   - Insert microSD card into your computer
   - Open Raspberry Pi Imager
   - Choose OS: **Raspberry Pi OS (64-bit)** with desktop
   - Choose Storage: Your microSD card
   - Click **Settings** (gear icon):
     - Set hostname: `bms-dashboard`
     - Enable SSH
     - Set username: `pi` (or your choice)
     - Set password
     - Configure WiFi (if needed)
   - Click **Write**

3. **First Boot:**
   - Insert microSD into Raspberry Pi
   - Connect display, keyboard, mouse
   - Power on
   - Complete initial setup wizard

### 2. Connect to Raspberry Pi

**Option A: Direct (with keyboard/mouse/display)**
- Already connected!

**Option B: SSH (headless)**
```bash
# From your computer
ssh pi@bms-dashboard.local
# Or use IP address
ssh pi@192.168.1.XXX
```

### 3. Transfer Project Files

**Option A: Using Git (recommended)**
```bash
cd ~
git clone <your-repository-url> rasperryPi_setup
cd rasperryPi_setup
```

**Option B: Using SCP (from your computer)**
```bash
# From your Windows computer (PowerShell)
scp -r "C:\Users\kirija R\Documents\DAO EV TECH\rasperryPi_setup" pi@bms-dashboard.local:~/
```

**Option C: Using USB Drive**
1. Copy project folder to USB drive
2. Insert USB into Raspberry Pi
3. Copy to home directory:
```bash
cp -r /media/pi/USB_DRIVE/rasperryPi_setup ~/
```

---

## 🚀 Installation Process

### Automated Installation (Recommended)

```bash
cd ~/rasperryPi_setup
chmod +x scripts/setup_raspberry_pi.sh
./scripts/setup_raspberry_pi.sh
```

**This script will:**
1. ✅ Update system packages
2. ✅ Install Node.js, Python, Nginx, Chromium
3. ✅ Configure UART for RS-485
4. ✅ Configure 7-inch display (1024x600)
5. ✅ Build frontend and backend
6. ✅ Setup Nginx reverse proxy
7. ✅ Create systemd services
8. ✅ Configure kiosk mode auto-start
9. ✅ Create management scripts

**Installation time:** ~15-20 minutes (depending on internet speed)

---

## ⚙️ Configuration

### 1. Configure Your Bike Model

Edit the `.env` file:
```bash
cd ~/rasperryPi_setup
nano .env
```

**For your Scooty Model 703-O (default):**
```bash
BIKE_MODEL=703-O
DB_PATH=data/bms_data.db
DB_LOG_INTERVAL=5
BACKEND_HOST=0.0.0.0
BACKEND_PORT=5000
DEBUG_MODE=False
DATA_RETENTION_DAYS=30
LOG_LEVEL=INFO
LOG_FILE=logs/bms_server.log
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### 2. Verify Configuration

Check that your bike model exists:
```bash
cat config/bike_models.json | grep "703-O"
```

### 3. Test Backend

```bash
cd ~/rasperryPi_setup/backend
source venv/bin/activate
python main.py
```

You should see:
```
====================================
🚀 DAO BMS DATA SERVER - ENHANCED VERSION
====================================
📋 Bike Model: Scooty Model 703-O
🔧 Protocol: RS485
💾 Database: /home/pi/rasperryPi_setup/data/bms_data.db
====================================
```

Press `Ctrl+C` to stop, then:
```bash
deactivate
```

### 4. Reboot

**IMPORTANT:** Reboot is required for UART and display settings!
```bash
sudo reboot
```

---

## 🎮 Running the System

### After Reboot

The system will **automatically start** in kiosk mode showing your dashboard!

### Manual Control

If you need to manually control services:

**Start Services:**
```bash
~/rasperryPi_setup/scripts/start.sh
```

**Stop Services:**
```bash
~/rasperryPi_setup/scripts/stop.sh
```

**Check Status:**
```bash
~/rasperryPi_setup/scripts/status.sh
```

**View Logs:**
```bash
~/rasperryPi_setup/scripts/logs.sh
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost | Main UI |
| **API - Current Data** | http://localhost/api/bms | Real-time BMS data |
| **API - Configuration** | http://localhost/api/config | Bike configuration |
| **API - History** | http://localhost/api/history?hours=24 | Historical data |
| **API - Health** | http://localhost/api/health | System health |

### Testing from Another Device

If your Raspberry Pi is on the network:
```
http://bms-dashboard.local
# Or use IP address
http://192.168.1.XXX
```

---

## 🔧 Management & Maintenance

### View Live Logs
```bash
# Backend logs
sudo journalctl -u bms-backend.service -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart backend
sudo systemctl restart bms-backend.service

# Restart Nginx
sudo systemctl restart nginx

# Restart both
~/rasperryPi_setup/scripts/stop.sh
~/rasperryPi_setup/scripts/start.sh
```

### Database Management

**View database location:**
```bash
ls -lh ~/rasperryPi_setup/data/bms_data.db
```

**Query database:**
```bash
sqlite3 ~/rasperryPi_setup/data/bms_data.db

# Inside sqlite3:
.tables
SELECT * FROM bms_logs ORDER BY timestamp DESC LIMIT 10;
.exit
```

**Backup database:**
```bash
cp ~/rasperryPi_setup/data/bms_data.db ~/bms_backup_$(date +%Y%m%d).db
```

### Update Application

```bash
cd ~/rasperryPi_setup
git pull  # If using git
~/rasperryPi_setup/scripts/update.sh
```

### Exit Kiosk Mode

**Temporarily:**
- Press `F11` to exit fullscreen
- Press `Alt+F4` to close Chromium

**Permanently disable auto-start:**
```bash
nano ~/.config/lxsession/LXDE-pi/autostart
# Comment out the Chromium line by adding # at the start
```

---

## 🐛 Troubleshooting

### Issue: No BMS Data

**Check serial connection:**
```bash
ls -l /dev/ttyAMA0
# Should show: crw-rw---- 1 root dialout

# Check if user is in dialout group
groups
# Should include: dialout
```

**If not in dialout group:**
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

**Test serial port:**
```bash
sudo cat /dev/ttyAMA0
# Should show data if BMS is connected
```

**Check wiring:**
- RS-485 A+ → BMS A+
- RS-485 B- → BMS B-
- GND → GND

### Issue: Display Wrong Size

**Check HDMI settings:**
```bash
sudo nano /boot/firmware/config.txt
```

Ensure these lines exist:
```
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 3 0 0 0
hdmi_drive=2
```

**Reboot after changes:**
```bash
sudo reboot
```

### Issue: Dashboard Not Loading

**Check Nginx:**
```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

**Check backend:**
```bash
sudo systemctl status bms-backend.service
curl http://localhost:5000/api/health
```

**Check frontend build:**
```bash
ls -la ~/rasperryPi_setup/dist/
# Should contain index.html and assets/
```

### Issue: WebSocket Not Connecting

**Check firewall:**
```bash
sudo ufw status
# If active, allow port 80
sudo ufw allow 80
```

**Check Nginx WebSocket proxy:**
```bash
sudo nano /etc/nginx/sites-available/bms-dashboard
# Verify socket.io location block exists
```

### Issue: Service Won't Start

**Check logs:**
```bash
sudo journalctl -u bms-backend.service -n 50
```

**Common fixes:**
```bash
# Fix permissions
sudo chown -R $USER:$USER ~/rasperryPi_setup

# Reinstall dependencies
cd ~/rasperryPi_setup/backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Restart service
sudo systemctl restart bms-backend.service
```

### Issue: Kiosk Mode Not Starting

**Check autostart file:**
```bash
cat ~/.config/lxsession/LXDE-pi/autostart
```

**Test Chromium manually:**
```bash
chromium-browser --kiosk http://localhost
```

---

## 🔄 Adding New Bike Models

### 1. Edit Configuration File

```bash
nano ~/rasperryPi_setup/config/bike_models.json
```

### 2. Add Your Model

```json
{
  "models": {
    "703-O": { ... },
    "YOUR-MODEL-NAME": {
      "name": "Your Bike Model Display Name",
      "protocol": "RS485",
      "baud_rate": 9600,
      "serial_ports": [
        "/dev/ttyAMA0",
        "/dev/serial0"
      ],
      "parameters": {
        "max_voltage": 60.0,
        "max_current": 50.0,
        "max_power": 3000.0,
        "max_speed": 60,
        "max_temperature": 80,
        "battery_capacity": 30,
        "num_temp_sensors": 5
      },
      "bms_config": {
        "frame_start": "0x5B",
        "command_response": "0x82",
        "data_length": 24,
        "crc_type": "modbus",
        "voltage_multiplier": 0.1,
        "current_multiplier": 0.1,
        "temp_offset": -40
      },
      "display": {
        "show_temperature": true,
        "show_voltage": true,
        "show_current": true,
        "show_power": true,
        "show_soc": true,
        "show_soh": true,
        "show_speed": false,
        "theme": "dark"
      }
    }
  },
  "active_model": "703-O"
}
```

### 3. Update .env File

```bash
nano ~/rasperryPi_setup/.env
```

Change:
```bash
BIKE_MODEL=YOUR-MODEL-NAME
```

### 4. Restart Backend

```bash
sudo systemctl restart bms-backend.service
```

### 5. Verify

```bash
curl http://localhost/api/config
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4                        │
│                                                          │
│  ┌────────────┐    ┌──────────────┐   ┌──────────────┐ │
│  │   BMS      │───▶│  RS-485 HAT  │──▶│ /dev/ttyAMA0 │ │
│  │  (RS-485)  │    │              │   │   (UART)     │ │
│  └────────────┘    └──────────────┘   └──────┬───────┘ │
│                                               │         │
│                                               ▼         │
│                                    ┌──────────────────┐ │
│                                    │  Python Backend  │ │
│                                    │  (bms_server)    │ │
│                                    │  Port: 5000      │ │
│                                    └────────┬─────────┘ │
│                                             │           │
│                                             ▼           │
│                                    ┌──────────────────┐ │
│                                    │   SQLite DB      │ │
│                                    │   (data logs)    │ │
│                                    └──────────────────┘ │
│                                             │           │
│                                             ▼           │
│  ┌─────────────┐                  ┌──────────────────┐ │
│  │  Chromium   │◀─────────────────│     Nginx        │ │
│  │  (Kiosk)    │                  │  (Reverse Proxy) │ │
│  │             │                  │   Port: 80       │ │
│  └──────┬──────┘                  └──────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────┐                                      │
│  │  7" Display  │                                      │
│  │  1024x600    │                                      │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Production Checklist

After setup, verify:

- [ ] Backend service is running: `sudo systemctl status bms-backend`
- [ ] Nginx is running: `sudo systemctl status nginx`
- [ ] API returns data: `curl http://localhost/api/bms`
- [ ] Dashboard loads: Open browser to `http://localhost`
- [ ] BMS data is updating (check voltage, current, etc.)
- [ ] Database is logging: `ls -lh ~/rasperryPi_setup/data/bms_data.db`
- [ ] Display resolution is correct (1024x600)
- [ ] Kiosk mode starts on boot
- [ ] Serial port is accessible: `ls -l /dev/ttyAMA0`
- [ ] User is in dialout group: `groups | grep dialout`

---

## 📚 Additional Resources

### Configuration Files
- **Bike Models:** `~/rasperryPi_setup/config/bike_models.json`
- **Environment:** `~/rasperryPi_setup/.env`
- **Nginx:** `/etc/nginx/sites-available/bms-dashboard`
- **Systemd Service:** `/etc/systemd/system/bms-backend.service`
- **Autostart:** `~/.config/lxsession/LXDE-pi/autostart`

### Log Files
- **Backend:** `~/rasperryPi_setup/logs/bms_server.log`
- **Systemd:** `sudo journalctl -u bms-backend.service`
- **Nginx Access:** `/var/log/nginx/access.log`
- **Nginx Error:** `/var/log/nginx/error.log`

### Data Files
- **Database:** `~/rasperryPi_setup/data/bms_data.db`
- **Frontend Build:** `~/rasperryPi_setup/dist/`

---

## 🎉 Success!

Your production-ready BMS dashboard is now running!

**What happens now:**
1. Dashboard auto-starts on boot in kiosk mode
2. BMS data is read via RS-485 and displayed in real-time
3. All data is logged to SQLite database
4. You can switch bike models by editing `.env` file
5. System is production-ready and stable

**For support or questions, check the logs and troubleshooting section above.**

**Happy riding! 🚴‍♂️⚡**
