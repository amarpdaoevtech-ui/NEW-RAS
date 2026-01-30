# ⚡ QUICK START CHECKLIST

Use this checklist to deploy your BMS dashboard to Raspberry Pi 4.

---

## 📦 Pre-Deployment (On Your Windows Computer)

### ☐ 1. Verify Files
```powershell
cd "C:\Users\kirija R\Documents\DAO EV TECH\rasperryPi_setup"
dir
```

**Should see:**
- ✅ `backend/` folder
- ✅ `config/` folder
- ✅ `scripts/` folder
- ✅ `src/` folder
- ✅ `.env` file
- ✅ `package.json`
- ✅ `PRODUCTION_DEPLOYMENT.md`

### ☐ 2. Check Configuration
```powershell
type .env
```

**Should show:**
```
BIKE_MODEL=703-O
DB_PATH=data/bms_data.db
...
```

### ☐ 3. Prepare Raspberry Pi SD Card

**Option A: Fresh Install**
1. Download Raspberry Pi Imager
2. Flash "Raspberry Pi OS (64-bit)" with desktop
3. Configure:
   - Hostname: `bms-dashboard`
   - Username: `pi`
   - Password: (your choice)
   - Enable SSH
   - Configure WiFi (if needed)

**Option B: Existing Raspberry Pi**
- Just make sure it's updated and accessible

---

## 🔌 Hardware Setup

### ☐ 4. Connect Hardware

**Connections:**
- [ ] Raspberry Pi 4 powered off
- [ ] RS-485 HAT installed on GPIO pins
- [ ] 7-inch display connected via HDMI
- [ ] RS-485 wiring:
  - [ ] A+ → BMS A+
  - [ ] B- → BMS B-
  - [ ] GND → GND
- [ ] Keyboard and mouse connected (for initial setup)
- [ ] Power supply ready (don't power on yet)

---

## 📤 Transfer Files to Raspberry Pi

### ☐ 5. Power On Raspberry Pi

- [ ] Insert SD card
- [ ] Power on
- [ ] Wait for boot (first boot takes ~2 minutes)
- [ ] Note the IP address (shown on screen or check router)

### ☐ 6. Transfer Project Files

**Option A: Using SCP (Recommended)**
```powershell
# From Windows PowerShell
scp -r "C:\Users\kirija R\Documents\DAO EV TECH\rasperryPi_setup" pi@bms-dashboard.local:~/
```

**Option B: Using USB Drive**
1. Copy `rasperryPi_setup` folder to USB drive
2. Insert USB into Raspberry Pi
3. Copy from USB to home directory

**Option C: Using Git**
```bash
# On Raspberry Pi
git clone <your-repo-url> ~/rasperryPi_setup
```

### ☐ 7. Verify Transfer

```bash
# SSH into Raspberry Pi
ssh pi@bms-dashboard.local

# Check files
ls -la ~/rasperryPi_setup
```

**Should see all project files**

---

## 🚀 Installation

### ☐ 8. Run Setup Script

```bash
cd ~/rasperryPi_setup
chmod +x scripts/setup_raspberry_pi.sh
./scripts/setup_raspberry_pi.sh
```

**This will take 15-20 minutes**

**Watch for:**
- ✅ "Updating system packages..."
- ✅ "Installing dependencies..."
- ✅ "Configuring UART..."
- ✅ "Configuring display..."
- ✅ "Building frontend..."
- ✅ "Configuring Nginx..."
- ✅ "Creating systemd service..."
- ✅ "Configuring kiosk mode..."
- ✅ "Setup Complete!"

### ☐ 9. Verify Configuration

```bash
# Check .env file
cat ~/rasperryPi_setup/.env

# Should show your bike model
# BIKE_MODEL=703-O
```

### ☐ 10. Reboot

```bash
sudo reboot
```

**IMPORTANT:** Reboot is required for UART and display settings!

---

## ✅ Post-Installation Verification

### ☐ 11. Check Auto-Start

After reboot (wait ~30 seconds):

- [ ] Dashboard appears in full-screen (kiosk mode)
- [ ] Display resolution is correct (1024x600)
- [ ] No browser toolbars visible

### ☐ 12. Check BMS Connection

**On the dashboard, verify:**
- [ ] Temperature shows real values (not 0)
- [ ] Voltage shows real values
- [ ] Current shows real values
- [ ] SoC (State of Charge) shows percentage
- [ ] Status shows "Normal discharge" or similar
- [ ] "Last Update" timestamp is recent

**If showing zeros:**
- Check RS-485 wiring
- Check serial port (see troubleshooting)

### ☐ 13. Test Services

**SSH into Raspberry Pi again:**
```bash
ssh pi@bms-dashboard.local
```

**Check backend service:**
```bash
sudo systemctl status bms-backend.service
```
- [ ] Shows "active (running)" in green

**Check Nginx:**
```bash
sudo systemctl status nginx
```
- [ ] Shows "active (running)" in green

### ☐ 14. Test API

```bash
# Test health endpoint
curl http://localhost/api/health

# Should return:
# {"status":"ok","connected":true,...}

# Test BMS data
curl http://localhost/api/bms

# Should return current BMS data

# Test configuration
curl http://localhost/api/config

# Should show bike model: 703-O
```

### ☐ 15. Check Database

```bash
# Check database file exists
ls -lh ~/rasperryPi_setup/data/bms_data.db

# Should show file size growing over time

# Query database
sqlite3 ~/rasperryPi_setup/data/bms_data.db "SELECT COUNT(*) FROM bms_logs;"

# Should show number of logged records
```

### ☐ 16. Check Logs

```bash
# View backend logs
~/rasperryPi_setup/scripts/logs.sh

# Press Ctrl+C to exit

# Should show:
# - BMS UPDATE messages
# - No error messages
```

---

## 🎮 Test Management Scripts

### ☐ 17. Test Stop/Start

```bash
# Stop services
~/rasperryPi_setup/scripts/stop.sh

# Dashboard should disappear from display

# Start services
~/rasperryPi_setup/scripts/start.sh

# Dashboard should reappear
```

### ☐ 18. Test Status

```bash
~/rasperryPi_setup/scripts/status.sh

# Should show both services running
```

---

## 🔧 Optional Configuration

### ☐ 19. Adjust Settings (if needed)

**Edit .env file:**
```bash
nano ~/rasperryPi_setup/.env
```

**Common adjustments:**
- `DB_LOG_INTERVAL=5` → Change logging frequency
- `DATA_RETENTION_DAYS=30` → Change how long to keep data
- `LOG_LEVEL=INFO` → Change to DEBUG for more logs

**After changes:**
```bash
sudo systemctl restart bms-backend.service
```

### ☐ 20. Test from Another Device (Optional)

**On your phone/computer on same network:**
```
http://bms-dashboard.local
# Or use IP address
http://192.168.1.XXX
```

- [ ] Dashboard loads
- [ ] Data updates in real-time

---

## 🎯 Final Verification

### ☐ 21. Complete System Test

**Power cycle test:**
1. Unplug Raspberry Pi
2. Wait 10 seconds
3. Plug back in
4. Wait ~30 seconds
5. Dashboard should auto-start in kiosk mode

**Data logging test:**
1. Let system run for 5 minutes
2. Check database:
   ```bash
   sqlite3 ~/rasperryPi_setup/data/bms_data.db \
     "SELECT COUNT(*) FROM bms_logs;"
   ```
3. Should have ~60 records (5 min × 12 logs/min)

**API test:**
```bash
# Get historical data
curl "http://localhost/api/history?hours=1"

# Should return logged data
```

---

## ✅ Production Checklist

Mark when complete:

- [ ] Hardware connected correctly
- [ ] Raspberry Pi OS installed
- [ ] Project files transferred
- [ ] Setup script completed successfully
- [ ] System rebooted
- [ ] Dashboard auto-starts in kiosk mode
- [ ] Display resolution correct (1024x600)
- [ ] BMS data showing real values
- [ ] Backend service running
- [ ] Nginx running
- [ ] Database logging working
- [ ] API endpoints responding
- [ ] Management scripts working
- [ ] System survives reboot
- [ ] No error messages in logs

---

## 🐛 Troubleshooting Quick Reference

### Issue: No BMS Data (All Zeros)

```bash
# Check serial port exists
ls -l /dev/ttyAMA0

# Check user in dialout group
groups | grep dialout

# If not in group:
sudo usermod -a -G dialout pi
# Then log out and back in

# Test serial port
sudo cat /dev/ttyAMA0
# Should show data if BMS is connected

# Check wiring:
# A+ to A+, B- to B-, GND to GND
```

### Issue: Dashboard Not Loading

```bash
# Check Nginx
sudo systemctl status nginx

# If not running:
sudo systemctl start nginx

# Check frontend build
ls -la ~/rasperryPi_setup/dist/

# If empty:
cd ~/rasperryPi_setup
npm install
npm run build
sudo systemctl restart nginx
```

### Issue: Wrong Display Size

```bash
# Edit config
sudo nano /boot/firmware/config.txt

# Add/verify these lines:
# hdmi_group=2
# hdmi_mode=87
# hdmi_cvt=1024 600 60 3 0 0 0
# hdmi_drive=2

# Save and reboot
sudo reboot
```

### Issue: Service Won't Start

```bash
# Check logs
sudo journalctl -u bms-backend.service -n 50

# Common fixes:
# 1. Fix permissions
sudo chown -R pi:pi ~/rasperryPi_setup

# 2. Reinstall dependencies
cd ~/rasperryPi_setup/backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

# 3. Restart service
sudo systemctl restart bms-backend.service
```

---

## 📚 Next Steps After Setup

### Learn More
- [ ] Read `SWITCHING_MODELS.md` to learn how to add new bikes
- [ ] Read `PRODUCTION_DEPLOYMENT.md` for detailed info
- [ ] Explore API endpoints
- [ ] Query database for analytics

### Customize
- [ ] Add your other bike models to `config/bike_models.json`
- [ ] Adjust logging intervals in `.env`
- [ ] Customize frontend UI if needed

### Monitor
- [ ] Check logs daily: `~/rasperryPi_setup/scripts/logs.sh`
- [ ] Monitor database size: `ls -lh ~/rasperryPi_setup/data/`
- [ ] Backup database periodically

---

## 🎉 Success!

If all checkboxes are marked, you have:

✅ **Production-ready BMS dashboard**  
✅ **Auto-starting kiosk mode**  
✅ **Real-time data monitoring**  
✅ **Database logging**  
✅ **Easy bike model switching**  
✅ **Professional deployment**

**Your dashboard is ready for your scooty! 🚴‍♂️⚡**

---

## 📞 Support

**If you encounter issues:**

1. Check logs: `~/rasperryPi_setup/scripts/logs.sh`
2. Check status: `~/rasperryPi_setup/scripts/status.sh`
3. Read troubleshooting section above
4. Consult `PRODUCTION_DEPLOYMENT.md`

**For configuration questions:**
- See `SWITCHING_MODELS.md`
- See `SETUP_SUMMARY.md`

---

**Estimated Total Time:** 30-45 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** Basic Linux command line knowledge

**Happy riding! 🚴‍♂️⚡**
