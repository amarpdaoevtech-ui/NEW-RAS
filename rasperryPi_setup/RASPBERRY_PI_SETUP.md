# 🚀 E-Bike Dashboard - Raspberry Pi 4 Setup Guide
## Complete Step-by-Step Implementation for 7-inch Display (1024x600)

---

## 📋 **PREREQUISITES**

### Hardware Required:
- ✅ Raspberry Pi 4 (2GB+ RAM recommended)
- ✅ 7-inch HDMI LCD Display (1024x600)
- ✅ RS-485 HAT/Module for Raspberry Pi
- ✅ MicroSD Card (16GB+ recommended)
- ✅ Power Supply (5V 3A for Pi + Display)
- ✅ DAO BMS connected via RS-485

### Software Required:
- Raspberry Pi OS (Bullseye or newer)
- Internet connection for initial setup

---

## 🔧 **PART 1: RASPBERRY PI INITIAL SETUP**

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - From: https://www.raspberrypi.com/software/
   
2. **Flash OS to SD Card**
   ```
   - Choose OS: Raspberry Pi OS (64-bit) Lite or Desktop
   - Choose Storage: Your SD Card
   - Click Settings (gear icon):
     ✓ Enable SSH
     ✓ Set username/password
     ✓ Configure WiFi (if needed)
   - Click WRITE
   ```

3. **Boot Raspberry Pi**
   - Insert SD card
   - Connect 7-inch display via HDMI
   - Power on

### Step 2: Configure Display Resolution

1. **Edit boot config**
   ```bash
   sudo nano /boot/firmware/config.txt
   ```
   
2. **Add these lines at the end:**
   ```
   # 7-inch Display Configuration (1024x600)
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=1024 600 60 3 0 0 0
   hdmi_drive=2
   
   # UART Configuration for RS-485
   enable_uart=1
   dtoverlay=disable-bt
   ```

3. **Save and reboot**
   ```bash
   sudo reboot
   ```

---

## 🔌 **PART 2: RS-485 HARDWARE SETUP**

### Step 3: Connect RS-485 HAT

1. **Physical Connections**
   ```
   Raspberry Pi GPIO → RS-485 Module
   - GPIO 14 (TXD)  → TX
   - GPIO 15 (RXD)  → RX
   - 5V             → VCC
   - GND            → GND
   ```

2. **RS-485 to BMS Wiring**
   ```
   RS-485 Module → DAO BMS
   - A+ → BMS A+
   - B- → BMS B-
   - GND → Common Ground
   ```

### Step 4: Test Serial Port

```bash
# Check available serial ports
ls -l /dev/ttyAMA* /dev/serial*

# You should see:
# /dev/ttyAMA0 (Hardware UART - this is what we want)
# /dev/serial0 (symlink to ttyAMA0)

# Set permissions
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Logout and login again for permissions to take effect
```

---

## 📦 **PART 3: INSTALL DEPENDENCIES**

### Step 5: Update System

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3-pip nodejs npm git
```

### Step 6: Install Node.js (Latest LTS)

```bash
# Remove old Node.js if exists
sudo apt remove -y nodejs npm

# Install Node.js 18.x (LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version  # Should show v18.x.x
npm --version   # Should show 9.x.x or higher
```

---

## 📂 **PART 4: DEPLOY APPLICATION**

### Step 7: Transfer Project Files

**Option A: Using Git (Recommended)**
```bash
# Create project directory
mkdir -p ~/ebike-dashboard
cd ~/ebike-dashboard

# If you have a Git repository:
git clone <your-repo-url> .

# Or copy files from your development machine
```

**Option B: Using SCP from your Windows PC**
```powershell
# From your Windows PC (PowerShell):
scp -r "c:\Users\kirija R\Documents\DAO EV TECH\UI1" pi@<raspberry-pi-ip>:~/ebike-dashboard
```

**Option C: Using USB Drive**
```bash
# Insert USB drive, then:
sudo mount /dev/sda1 /mnt
cp -r /mnt/UI1/* ~/ebike-dashboard/
sudo umount /mnt
```

### Step 8: Install Python Dependencies

```bash
cd ~/ebike-dashboard/backend

# Install Python packages
pip3 install -r requirements.txt

# Verify installation
pip3 list | grep -E "Flask|pyserial|socketio"
```

### Step 9: Install Frontend Dependencies

```bash
cd ~/ebike-dashboard

# Install npm packages
npm install

# This will install:
# - React, Vite
# - socket.io-client
# - All other dependencies
```

---

## 🧪 **PART 5: TEST BACKEND**

### Step 10: Test BMS Connection

```bash
cd ~/ebike-dashboard/backend

# Run the BMS server
python3 bms_server.py

# You should see:
# ✅ Successfully opened /dev/ttyAMA0
# 📊 Listening on /dev/ttyAMA0 at 9600 baud...
# 🌐 Starting Web Server...
```

**If you see errors:**
- Check RS-485 wiring
- Verify UART is enabled: `ls -l /dev/ttyAMA0`
- Check permissions: `groups` (should include dialout)
- Verify BMS is powered and transmitting

**Test API manually:**
```bash
# Open new terminal
curl http://localhost:5000/api/health
curl http://localhost:5000/api/bms
```

---

## 🎨 **PART 6: BUILD & RUN FRONTEND**

### Step 11: Build Production Frontend

```bash
cd ~/ebike-dashboard

# Build optimized production bundle
npm run build

# This creates a 'dist' folder with optimized files
```

### Step 12: Install Web Server (Nginx)

```bash
# Install Nginx
sudo apt install -y nginx

# Copy built files to web root
sudo rm -rf /var/www/html/*
sudo cp -r dist/* /var/www/html/

# Set permissions
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html
```

### Step 13: Configure Nginx

```bash
# Edit Nginx config
sudo nano /etc/nginx/sites-available/default
```

**Replace content with:**
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html;
    
    server_name _;
    
    # Serve frontend
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

**Save and restart Nginx:**
```bash
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
sudo systemctl enable nginx  # Start on boot
```

---

## 🚀 **PART 7: AUTO-START ON BOOT**

### Step 14: Create Systemd Service for Backend

```bash
# Create service file
sudo nano /etc/systemd/system/bms-backend.service
```

**Add this content:**
```ini
[Unit]
Description=E-Bike BMS Backend Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ebike-dashboard/backend
ExecStart=/usr/bin/python3 /home/pi/ebike-dashboard/backend/bms_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bms-backend.service
sudo systemctl start bms-backend.service

# Check status
sudo systemctl status bms-backend.service
```

### Step 15: Configure Auto-Login and Kiosk Mode

```bash
# Enable auto-login
sudo raspi-config
# Navigate to: System Options → Boot / Auto Login → Desktop Autologin
```

**Create kiosk startup script:**
```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/dashboard.desktop
```

**Add this content:**
```ini
[Desktop Entry]
Type=Application
Name=E-Bike Dashboard
Exec=/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state --disable-features=TranslateUI --window-size=1024,600 --window-position=0,0 http://localhost
```

**Or for Lite version (no desktop), use framebuffer browser:**
```bash
sudo apt install -y chromium-browser xserver-xorg xinit openbox

# Create startup script
nano ~/start-dashboard.sh
```

**Add:**
```bash
#!/bin/bash
export DISPLAY=:0
xset s off
xset -dpms
xset s noblank
openbox &
chromium-browser --kiosk --noerrdialogs --disable-infobars --window-size=1024,600 http://localhost
```

```bash
chmod +x ~/start-dashboard.sh

# Add to .bashrc for auto-start
echo "~/start-dashboard.sh" >> ~/.bashrc
```

---

## ✅ **PART 8: VERIFICATION & TESTING**

### Step 16: Complete System Test

1. **Reboot Raspberry Pi**
   ```bash
   sudo reboot
   ```

2. **After boot, verify:**
   - ✅ Display shows dashboard at 1024x600
   - ✅ Backend is running: `sudo systemctl status bms-backend`
   - ✅ Nginx is running: `sudo systemctl status nginx`
   - ✅ BMS data is updating in real-time

3. **Check logs if issues:**
   ```bash
   # Backend logs
   sudo journalctl -u bms-backend.service -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

---

## 🔧 **TROUBLESHOOTING**

### Issue: No BMS Data

```bash
# Check serial port
ls -l /dev/ttyAMA0

# Test manually
sudo cat /dev/ttyAMA0  # Should show raw data

# Check backend logs
sudo journalctl -u bms-backend.service -n 50
```

### Issue: Display Resolution Wrong

```bash
# Check current resolution
tvservice -s

# Force resolution
sudo nano /boot/firmware/config.txt
# Ensure hdmi_cvt=1024 600 60 3 0 0 0 is present
```

### Issue: Frontend Not Loading

```bash
# Check Nginx
sudo systemctl status nginx
curl http://localhost

# Rebuild frontend
cd ~/ebike-dashboard
npm run build
sudo cp -r dist/* /var/www/html/
```

### Issue: WebSocket Not Connecting

```bash
# Check backend is running
curl http://localhost:5000/api/health

# Check Nginx proxy
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 **MONITORING & MAINTENANCE**

### View Real-time Logs
```bash
# Backend logs
sudo journalctl -u bms-backend.service -f

# System logs
dmesg | tail -50
```

### Update Application
```bash
cd ~/ebike-dashboard
git pull  # If using Git
npm run build
sudo cp -r dist/* /var/www/html/
sudo systemctl restart bms-backend
```

### Performance Optimization
```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Reduce GPU memory (if not using desktop)
sudo nano /boot/firmware/config.txt
# Add: gpu_mem=16
```

---

## 🎯 **FINAL CHECKLIST**

- [ ] Raspberry Pi OS installed and updated
- [ ] Display configured for 1024x600
- [ ] UART enabled and Bluetooth disabled
- [ ] RS-485 HAT connected and tested
- [ ] Python dependencies installed
- [ ] Node.js and npm installed
- [ ] Backend service running and auto-starting
- [ ] Frontend built and deployed to Nginx
- [ ] Nginx configured with API proxy
- [ ] Kiosk mode enabled for auto-start
- [ ] BMS data displaying in real-time
- [ ] System tested after reboot

---

## 📝 **QUICK REFERENCE COMMANDS**

```bash
# Restart backend
sudo systemctl restart bms-backend

# View backend logs
sudo journalctl -u bms-backend.service -f

# Restart Nginx
sudo systemctl restart nginx

# Rebuild frontend
cd ~/ebike-dashboard && npm run build && sudo cp -r dist/* /var/www/html/

# Check BMS connection
sudo cat /dev/ttyAMA0

# Reboot system
sudo reboot
```

---

## 🆘 **SUPPORT**

If you encounter issues:
1. Check logs: `sudo journalctl -u bms-backend.service -n 100`
2. Verify connections: RS-485 wiring, power supply
3. Test components individually: backend → frontend → display

**System is working when:**
- Dashboard loads automatically on boot
- Real-time BMS data updates every few seconds
- Temperature shows average of 5 sensors
- Voltage, current, power, SoC, SoH all display correctly

---

**🎉 Setup Complete! Your E-Bike Dashboard is now running on Raspberry Pi 4!**
