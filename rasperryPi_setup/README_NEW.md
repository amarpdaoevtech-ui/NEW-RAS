# 🚴 DAO EV Tech - Production BMS Dashboard System

**Real-time Battery Management System monitoring for E-Bikes**  
**Production-ready • Kiosk Mode • Multi-bike Support • Database Logging**

---

## 🎯 What Is This?

A **complete, production-ready system** for displaying real-time BMS data on a 7-inch display in your e-bike. The system:

- ✅ **Auto-starts on boot** in kiosk mode (full-screen, no distractions)
- ✅ **Logs all data** to SQLite database for analysis
- ✅ **Supports multiple bike models** - switch by editing one file
- ✅ **Production-ready** with systemd services and Nginx
- ✅ **Real-time updates** via WebSocket (\<30ms latency)
- ✅ **Easy to deploy** - one script does everything

---

## 📸 What You'll Get

```
┌─────────────────────────────────────────────┐
│  🔋 BMS Dashboard - Model 703-O             │
├─────────────────────────────────────────────┤
│                                             │
│   Temperature: 35.2°C  ●●●●○○○○○○  [80°C]  │
│                                             │
│   Voltage:     54.3V   ████████░░  [60V]   │
│   Current:     12.5A   █████░░░░░  [50A]   │
│                                             │
│   Power:       678.75W ███████░░░  [3000W] │
│                                             │
│   SoC:         78%     ●●●●●●●●○○           │
│   SoH:         95%     ●●●●●●●●●○           │
│                                             │
│   Status: Normal discharge                  │
│   Last Update: 2026-01-11 13:22:54          │
└─────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### For Raspberry Pi (Production)

1. **Transfer files to Raspberry Pi**
2. **Run setup script:**
   ```bash
   cd ~/rasperryPi_setup
   chmod +x scripts/setup_raspberry_pi.sh
   ./scripts/setup_raspberry_pi.sh
   ```
3. **Reboot:**
   ```bash
   sudo reboot
   ```
4. **Done!** Dashboard auto-starts in kiosk mode

**📖 Full guide:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)

### For Development (Windows/Mac/Linux)

```bash
# 1. Install dependencies
npm install
cd backend && pip install -r requirements.txt

# 2. Create .env file (already exists)
# Edit if needed: nano .env

# 3. Run backend
cd backend
python main.py

# 4. Run frontend (new terminal)
npm run dev

# 5. Open browser
http://localhost:5173
```

---

## 📁 Project Structure

```
rasperryPi_setup/
├── backend/
│   ├── main.py                    # Modular orchestrator (USE THIS)
│   ├── api/                       # API routes and sockets
│   ├── hardware/                  # Hardware drivers
│   ├── logic/                     # DTE and Odometer logic
│   └── requirements.txt           # Python dependencies
│
├── config/
│   └── bike_models.json           # Bike model configurations
│
├── scripts/
│   ├── setup_raspberry_pi.sh      # Complete setup script
│   ├── start.sh                   # Start services
│   ├── stop.sh                    # Stop services
│   ├── status.sh                  # Check status
│   ├── logs.sh                    # View logs
│   └── update.sh                  # Update application
│
├── src/
│   ├── components/                # React components
│   └── hooks/                     # Custom hooks
│
├── data/                          # SQLite database (created on first run)
├── logs/                          # Log files (created on first run)
│
├── .env                           # Environment configuration
├── .env.example                   # Environment template
│
├── PRODUCTION_DEPLOYMENT.md       # 📘 Complete deployment guide
├── SWITCHING_MODELS.md            # 🔄 How to switch bike models
├── RASPBERRY_PI_SETUP.md          # 📋 Original setup guide
├── INTEGRATION_EXPLAINED.md       # 📚 Technical details
└── README.md                      # This file
```

---

## 🔧 Configuration System

### Switch Bike Models Without Code Changes!

**Your current model:** `703-O` (Scooty Model 703-O)

**To switch to a different bike:**

1. Edit `.env` file:
   ```bash
   nano .env
   ```

2. Change `BIKE_MODEL`:
   ```bash
   BIKE_MODEL=YOUR-MODEL-NAME
   ```

3. Restart backend:
   ```bash
   sudo systemctl restart bms-backend.service
   ```

**That's it!** No code changes needed.

**📖 Full guide:** [SWITCHING_MODELS.md](./SWITCHING_MODELS.md)

---

## 📊 Features

### 🔥 Core Features

| Feature | Description |
|---------|-------------|
| **Real-time Monitoring** | WebSocket updates \<30ms latency |
| **Database Logging** | SQLite database with configurable retention |
| **Multi-bike Support** | Switch models via .env file |
| **Kiosk Mode** | Auto-start full-screen on boot |
| **Production Ready** | Systemd services, Nginx reverse proxy |
| **Easy Management** | Simple scripts for all operations |

### 📈 Data Displayed

- **Temperature** - Average of 5 sensors (configurable)
- **Voltage** - Real-time battery voltage
- **Current** - Discharge current
- **Power** - Calculated (V × I)
- **SoC** - State of Charge (%)
- **SoH** - State of Health (%)
- **Status** - BMS status flags
- **Historical Data** - Query via API

### 🎨 Display Features

- **Optimized for 7-inch 1024x600 display**
- **Responsive gauges and charts**
- **Real-time animations**
- **Dark theme (configurable)**
- **No scrolling or overflow**

---

## 🛠️ Technology Stack

### Backend
- **Python 3** - Core language
- **Flask** - Web framework
- **Flask-SocketIO** - WebSocket support
- **pySerial** - RS-485 communication
- **SQLite** - Database
- **python-dotenv** - Configuration management

### Frontend
- **React 19** - UI framework
- **Vite** - Build tool
- **Socket.IO Client** - WebSocket
- **TailwindCSS** - Styling
- **Lucide React** - Icons

### Infrastructure
- **Nginx** - Web server & reverse proxy
- **Systemd** - Service management
- **Chromium** - Kiosk mode browser

---

## 📚 Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **[PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)** | Complete Raspberry Pi setup | First-time setup |
| **[SWITCHING_MODELS.md](./SWITCHING_MODELS.md)** | How to switch bike models | When adding new bikes |
| **[RASPBERRY_PI_SETUP.md](./RASPBERRY_PI_SETUP.md)** | Original setup guide | Reference |
| **[INTEGRATION_EXPLAINED.md](./INTEGRATION_EXPLAINED.md)** | Technical details | Understanding the system |
| **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** | Quick commands | Daily operations |

---

## 🎮 Management Commands

All scripts are in `scripts/` directory:

```bash
# Start services
~/rasperryPi_setup/scripts/start.sh

# Stop services
~/rasperryPi_setup/scripts/stop.sh

# Check status
~/rasperryPi_setup/scripts/status.sh

# View logs
~/rasperryPi_setup/scripts/logs.sh

# Update application
~/rasperryPi_setup/scripts/update.sh
```

---

## 🌐 API Endpoints

| Endpoint | Description | Example |
|----------|-------------|---------|
| `/api/bms` | Current BMS data | `curl http://localhost/api/bms` |
| `/api/config` | Bike configuration | `curl http://localhost/api/config` |
| `/api/history` | Historical data | `curl http://localhost/api/history?hours=24` |
| `/api/health` | System health | `curl http://localhost/api/health` |

---

## 💾 Database

### Location
```bash
~/rasperryPi_setup/data/bms_data.db
```

### Schema
```sql
CREATE TABLE bms_logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    bike_model TEXT,
    temperature REAL,
    voltage REAL,
    current REAL,
    power REAL,
    soc INTEGER,
    soh INTEGER,
    battery_capacity INTEGER,
    charge_cycles INTEGER,
    -- ... more fields
);
```

### Query Examples
```bash
# Open database
sqlite3 ~/rasperryPi_setup/data/bms_data.db

# View recent logs
SELECT timestamp, voltage, current, soc 
FROM bms_logs 
ORDER BY timestamp DESC 
LIMIT 10;

# Average voltage over last hour
SELECT AVG(voltage) 
FROM bms_logs 
WHERE timestamp > datetime('now', '-1 hour');
```

---

## 🔄 Workflow

### Development Workflow

1. **Make changes** to code
2. **Test locally:**
   ```bash
   npm run dev  # Frontend
   python backend/bms_server_enhanced.py  # Backend
   ```
3. **Build for production:**
   ```bash
   npm run build
   ```
4. **Deploy to Raspberry Pi:**
   ```bash
   scp -r dist/ pi@bms-dashboard.local:~/rasperryPi_setup/
   ```
5. **Restart services:**
   ```bash
   ssh pi@bms-dashboard.local
   ~/rasperryPi_setup/scripts/update.sh
   ```

### Adding New Bike Model

1. **Edit config:**
   ```bash
   nano config/bike_models.json
   ```
2. **Add model definition** (see [SWITCHING_MODELS.md](./SWITCHING_MODELS.md))
3. **Update .env:**
   ```bash
   BIKE_MODEL=NEW-MODEL
   ```
4. **Restart:**
   ```bash
   sudo systemctl restart bms-backend.service
   ```

---

## 🐛 Troubleshooting

### Quick Diagnostics

```bash
# Check all services
~/rasperryPi_setup/scripts/status.sh

# View logs
~/rasperryPi_setup/scripts/logs.sh

# Test API
curl http://localhost/api/health

# Check serial port
ls -l /dev/ttyAMA0
```

### Common Issues

| Issue | Solution |
|-------|----------|
| No BMS data | Check RS-485 wiring, verify serial port |
| Dashboard not loading | Check Nginx: `sudo systemctl status nginx` |
| Wrong display size | Edit `/boot/firmware/config.txt` |
| Service won't start | Check logs: `sudo journalctl -u bms-backend.service` |

**📖 Full troubleshooting:** [PRODUCTION_DEPLOYMENT.md#troubleshooting](./PRODUCTION_DEPLOYMENT.md#troubleshooting)

---

## 🎯 Production Checklist

Before deployment:

- [ ] Hardware connected (Raspberry Pi, display, RS-485, BMS)
- [ ] Raspberry Pi OS installed and updated
- [ ] Project files transferred to Raspberry Pi
- [ ] Setup script executed successfully
- [ ] `.env` file configured for your bike model
- [ ] Backend service running
- [ ] Nginx running
- [ ] Dashboard accessible at http://localhost
- [ ] BMS data updating in real-time
- [ ] Database logging working
- [ ] Display resolution correct (1024x600)
- [ ] Kiosk mode auto-starts on boot
- [ ] System tested with reboot

---

## 📦 What's Included

### ✅ Enhanced Backend
- Configuration-based bike model support
- SQLite database logging
- Environment variable configuration
- Improved error handling and logging
- REST API + WebSocket support

### ✅ Production Scripts
- Complete Raspberry Pi setup script
- Service management scripts (start/stop/status/logs)
- Update script for easy deployments
- Kiosk mode configuration

### ✅ Configuration System
- JSON-based bike model definitions
- Environment variable overrides
- Easy switching between models
- No code changes needed

### ✅ Documentation
- Complete deployment guide
- Model switching guide
- Troubleshooting guide
- API reference

---

## 🚀 Deployment Summary

### One-Command Setup
```bash
./scripts/setup_raspberry_pi.sh
```

**This script:**
1. ✅ Updates system
2. ✅ Installs all dependencies
3. ✅ Configures UART for RS-485
4. ✅ Configures 7-inch display
5. ✅ Builds frontend and backend
6. ✅ Sets up Nginx
7. ✅ Creates systemd services
8. ✅ Configures kiosk mode
9. ✅ Creates management scripts

**Total time:** ~15-20 minutes

---

## 📈 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4                        │
│                                                          │
│  BMS (RS-485) → RS-485 HAT → /dev/ttyAMA0               │
│                                    ↓                     │
│                          Python Backend (Port 5000)      │
│                                    ↓                     │
│                          SQLite Database                 │
│                                    ↓                     │
│                          Nginx (Port 80)                 │
│                                    ↓                     │
│                          Chromium (Kiosk)                │
│                                    ↓                     │
│                          7" Display (1024x600)           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 Success Criteria

After setup, you should have:

1. ✅ **Auto-starting dashboard** - Powers on with Raspberry Pi
2. ✅ **Real-time data** - Updates \<30ms from BMS
3. ✅ **Database logging** - All data saved for analysis
4. ✅ **Easy bike switching** - Change models via .env
5. ✅ **Production stability** - Systemd services, auto-restart
6. ✅ **Easy management** - Simple scripts for all operations

---

## 📞 Support

### Documentation
- **Setup:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- **Switching Models:** [SWITCHING_MODELS.md](./SWITCHING_MODELS.md)
- **Troubleshooting:** See deployment guide

### Logs
```bash
# Backend logs
~/rasperryPi_setup/scripts/logs.sh

# System logs
sudo journalctl -u bms-backend.service -f
```

### Health Check
```bash
curl http://localhost/api/health
```

---

## 🔐 Security Notes

- Backend runs on localhost only (not exposed externally)
- Nginx proxies all requests
- WebSocket connections are local
- For remote access, configure firewall and use HTTPS

---

## 📄 License

This project is for educational and personal use. Modify as needed for your e-bike project.

---

## 🎯 Next Steps

1. **Read:** [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
2. **Setup:** Run `scripts/setup_raspberry_pi.sh`
3. **Configure:** Edit `.env` for your bike model
4. **Deploy:** Reboot and enjoy!

---

## 🏆 Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Real-time BMS monitoring | ✅ | \<30ms latency |
| Database logging | ✅ | SQLite with retention policy |
| Multi-bike support | ✅ | Config-based, no code changes |
| Kiosk mode | ✅ | Auto-start on boot |
| Production ready | ✅ | Systemd + Nginx |
| Easy deployment | ✅ | One-script setup |
| Management scripts | ✅ | Start/stop/status/logs |
| API endpoints | ✅ | REST + WebSocket |
| Documentation | ✅ | Complete guides |

---

**Happy riding! 🚴‍♂️⚡**

**Your production-ready BMS dashboard is ready to deploy!**
