# 🚀 QUICK START GUIDE - Raspberry Pi 4 E-Bike Dashboard

## 📦 **ONE-TIME SETUP** (Do this once)

### 1. Prepare SD Card
```bash
# Flash Raspberry Pi OS using Raspberry Pi Imager
# Enable SSH, set username/password, configure WiFi
```

### 2. Configure Boot Settings
```bash
sudo nano /boot/firmware/config.txt
```
Add:
```
hdmi_cvt=1024 600 60 3 0 0 0
hdmi_group=2
hdmi_mode=87
enable_uart=1
dtoverlay=disable-bt
```

### 3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs python3-pip nginx git

# Set permissions
sudo usermod -a -G dialout,tty $USER
```

### 4. Deploy Application
```bash
# Transfer files to ~/ebike-dashboard
# Then:
cd ~/ebike-dashboard

# Install Python deps
cd backend && pip3 install -r requirements.txt

# Install Node deps and build
cd ~/ebike-dashboard
npm install
npm run build

# Deploy to Nginx
sudo cp -r dist/* /var/www/html/
```

### 5. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/default
```
Copy config from RASPBERRY_PI_SETUP.md (Part 6, Step 13)

### 6. Auto-Start Backend
```bash
sudo nano /etc/systemd/system/bms-backend.service
```
Copy service file from RASPBERRY_PI_SETUP.md (Part 7, Step 14)

```bash
sudo systemctl enable bms-backend
sudo systemctl start bms-backend
```

### 7. Enable Kiosk Mode
```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/dashboard.desktop
```
Copy desktop file from RASPBERRY_PI_SETUP.md (Part 7, Step 15)

---

## ⚡ **DAILY USE COMMANDS**

### Check System Status
```bash
# Backend status
sudo systemctl status bms-backend

# View live logs
sudo journalctl -u bms-backend.service -f

# Check if BMS is sending data
sudo cat /dev/ttyAMA0
```

### Restart Services
```bash
# Restart backend
sudo systemctl restart bms-backend

# Restart web server
sudo systemctl restart nginx

# Reboot everything
sudo reboot
```

### Update Dashboard
```bash
cd ~/ebike-dashboard
git pull  # or copy new files
npm run build
sudo cp -r dist/* /var/www/html/
sudo systemctl restart bms-backend
```

---

## 🔍 **TROUBLESHOOTING**

| Problem | Solution |
|---------|----------|
| No BMS data | Check RS-485 wiring, run `ls -l /dev/ttyAMA0` |
| Display wrong size | Verify `/boot/firmware/config.txt` has correct hdmi_cvt |
| Frontend not loading | Run `sudo systemctl restart nginx` |
| WebSocket error | Check backend: `curl http://localhost:5000/api/health` |
| Permission denied | Run `sudo usermod -a -G dialout $USER` and logout/login |

---

## 📊 **DATA MAPPING**

| Frontend Component | Backend Data | Source |
|-------------------|--------------|--------|
| Temperature Gauge | `bmsData.temperature` | Average of 5 sensors |
| Voltage Display | `bmsData.voltage` | Pack voltage (V) |
| Current Display | `bmsData.current` | Discharge current (A) |
| Power Bar | `bmsData.power` | Calculated: V × I (W) |
| SoC Gauge | `bmsData.soc` | State of Charge (%) |
| SoH Gauge | `bmsData.soh` | State of Health (%) |

---

## 🎯 **SYSTEM ARCHITECTURE**

```
BMS (RS-485) 
    ↓
Raspberry Pi UART (/dev/ttyAMA0)
    ↓
Python Backend (bms_server.py) - Port 5000
    ↓ WebSocket + REST API
Nginx (Port 80)
    ↓
React Frontend (Browser Kiosk Mode)
    ↓
7-inch Display (1024x600)
```

---

## ✅ **VERIFICATION CHECKLIST**

After setup, verify:
- [ ] `sudo systemctl status bms-backend` shows "active (running)"
- [ ] `curl http://localhost:5000/api/bms` returns JSON data
- [ ] Dashboard loads at `http://localhost` in browser
- [ ] Temperature, voltage, current update in real-time
- [ ] Display resolution is exactly 1024x600
- [ ] System auto-starts after reboot

---

## 📱 **ACCESSING DASHBOARD**

- **On Raspberry Pi:** Opens automatically in kiosk mode
- **From other device:** `http://<raspberry-pi-ip>`
- **API endpoint:** `http://<raspberry-pi-ip>/api/bms`

---

**For complete setup instructions, see: RASPBERRY_PI_SETUP.md**
