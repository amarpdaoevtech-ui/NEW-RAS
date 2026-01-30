# 🔄 Quick Guide: Switching Bike Models

This guide shows you how to quickly switch between different bike models **without changing any code**.

---

## 📋 Current Setup

Your system is configured for **Model 703-O** by default.

To use the same backend with different bikes, you only need to:
1. Edit the `.env` file
2. Restart the backend service

**That's it! No code changes needed.**

---

## 🚀 How to Switch Models

### Step 1: Check Available Models

```bash
cd ~/rasperryPi_setup
cat config/bike_models.json | grep '"name"'
```

You'll see available models:
- `703-O` - Scooty Model 703-O (your current model)
- `GENERIC-EV` - Generic EV Bike (example)

### Step 2: Edit .env File

```bash
nano .env
```

Change the `BIKE_MODEL` line:
```bash
# For Model 703-O (default)
BIKE_MODEL=703-O

# For Generic EV
BIKE_MODEL=GENERIC-EV

# For your custom model
BIKE_MODEL=YOUR-MODEL-NAME
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Restart Backend

```bash
sudo systemctl restart bms-backend.service
```

### Step 4: Verify

```bash
# Check logs
sudo journalctl -u bms-backend.service -n 20

# Should show:
# ✅ Loaded configuration for: [Your Model Name]

# Check API
curl http://localhost/api/config
```

---

## ➕ Adding a New Bike Model

### Step 1: Edit Configuration File

```bash
nano config/bike_models.json
```

### Step 2: Add Your Model

Add a new entry in the `"models"` section:

```json
{
  "models": {
    "703-O": { ... existing ... },
    
    "MY-NEW-BIKE": {
      "name": "My New Bike Model",
      "protocol": "RS485",
      "baud_rate": 9600,
      "serial_ports": [
        "/dev/ttyAMA0",
        "/dev/serial0"
      ],
      "parameters": {
        "max_voltage": 48.0,
        "max_current": 30.0,
        "max_power": 1500.0,
        "max_speed": 45,
        "max_temperature": 70,
        "battery_capacity": 20,
        "num_temp_sensors": 3
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

### Step 3: Update .env

```bash
nano .env
```

Change to your new model:
```bash
BIKE_MODEL=MY-NEW-BIKE
```

### Step 4: Restart

```bash
sudo systemctl restart bms-backend.service
```

---

## 🔧 Configuration Parameters Explained

### `parameters` Section

| Parameter | Description | Example |
|-----------|-------------|---------|
| `max_voltage` | Maximum battery voltage (V) | 60.0 |
| `max_current` | Maximum current (A) | 50.0 |
| `max_power` | Maximum power (W) | 3000.0 |
| `max_speed` | Maximum speed (km/h) | 60 |
| `max_temperature` | Maximum safe temperature (°C) | 80 |
| `battery_capacity` | Battery capacity (Ah) | 30 |
| `num_temp_sensors` | Number of temperature sensors | 5 |

### `bms_config` Section

| Parameter | Description | Example |
|-----------|-------------|---------|
| `frame_start` | BMS frame start byte | "0x5B" |
| `command_response` | BMS command response code | "0x82" |
| `data_length` | Expected data length | 24 |
| `crc_type` | CRC algorithm | "modbus" |
| `voltage_multiplier` | Voltage conversion factor | 0.1 |
| `current_multiplier` | Current conversion factor | 0.1 |
| `temp_offset` | Temperature offset | -40 |

### `display` Section

| Parameter | Description | Values |
|-----------|-------------|--------|
| `show_temperature` | Show temperature gauge | true/false |
| `show_voltage` | Show voltage display | true/false |
| `show_current` | Show current display | true/false |
| `show_power` | Show power display | true/false |
| `show_soc` | Show State of Charge | true/false |
| `show_soh` | Show State of Health | true/false |
| `show_speed` | Show speedometer | true/false |
| `theme` | UI theme | "dark"/"light" |

---

## 📝 Example: Different Protocols

### If Your New Bike Uses Different Baud Rate

```json
"MY-FAST-BIKE": {
  "name": "High-Speed Model",
  "protocol": "RS485",
  "baud_rate": 19200,  // ← Changed from 9600
  ...
}
```

### If Your New Bike Has Different Temperature Sensors

```json
"MY-SIMPLE-BIKE": {
  "name": "Simple Model",
  "parameters": {
    "num_temp_sensors": 3,  // ← Changed from 5
    ...
  },
  ...
}
```

### If Your New Bike Has Different Voltage Range

```json
"MY-48V-BIKE": {
  "name": "48V Model",
  "parameters": {
    "max_voltage": 54.6,  // ← 48V nominal, 54.6V max
    "max_current": 30.0,
    "max_power": 1500.0,
    ...
  },
  ...
}
```

---

## 🎯 Quick Commands

### Switch to Model 703-O
```bash
sed -i 's/BIKE_MODEL=.*/BIKE_MODEL=703-O/' .env
sudo systemctl restart bms-backend.service
```

### Switch to Generic EV
```bash
sed -i 's/BIKE_MODEL=.*/BIKE_MODEL=GENERIC-EV/' .env
sudo systemctl restart bms-backend.service
```

### View Current Model
```bash
grep BIKE_MODEL .env
curl http://localhost/api/config | grep "model"
```

---

## ✅ Verification Checklist

After switching models:

1. **Check logs for successful load:**
   ```bash
   sudo journalctl -u bms-backend.service -n 5
   ```
   Should show: `✅ Loaded configuration for: [Model Name]`

2. **Verify API returns correct config:**
   ```bash
   curl http://localhost/api/config
   ```

3. **Check dashboard displays correctly:**
   - Open http://localhost
   - Verify all gauges show appropriate ranges

4. **Verify BMS data is being received:**
   ```bash
   curl http://localhost/api/bms
   ```

---

## 🐛 Troubleshooting

### Model Not Found Error

**Error:** `Bike model 'XXX' not found in configuration`

**Solution:**
1. Check spelling in `.env` file
2. Verify model exists in `config/bike_models.json`
3. Model names are case-sensitive!

### Backend Won't Start

**Check logs:**
```bash
sudo journalctl -u bms-backend.service -n 50
```

**Common issues:**
- JSON syntax error in config file
- Missing comma in JSON
- Invalid parameter values

**Validate JSON:**
```bash
python3 -m json.tool config/bike_models.json
```

### Data Not Updating

**Possible causes:**
1. Wrong baud rate for new bike
2. Different BMS protocol
3. Serial port not configured

**Check:**
```bash
# View current config
curl http://localhost/api/config

# Check serial port
ls -l /dev/ttyAMA0

# Test serial data
sudo cat /dev/ttyAMA0
```

---

## 💡 Pro Tips

### Tip 1: Keep a Backup
```bash
cp config/bike_models.json config/bike_models.json.backup
```

### Tip 2: Test New Models in Development First
```bash
# Stop production service
sudo systemctl stop bms-backend.service

# Run manually to test
cd backend
source venv/bin/activate
python bms_server_enhanced.py

# Watch for errors, then Ctrl+C to stop
deactivate

# Restart production service
sudo systemctl start bms-backend.service
```

### Tip 3: Use Environment Variables for Quick Testing
```bash
# Override model temporarily (doesn't change .env)
BIKE_MODEL=GENERIC-EV python backend/bms_server_enhanced.py
```

### Tip 4: Create Model-Specific .env Files
```bash
# Save different configurations
cp .env .env.703-O
cp .env .env.generic

# Switch quickly
cp .env.703-O .env
sudo systemctl restart bms-backend.service
```

---

## 📚 Summary

**To switch bike models:**
1. Edit `.env` → Change `BIKE_MODEL=YOUR-MODEL`
2. Restart → `sudo systemctl restart bms-backend.service`
3. Verify → `curl http://localhost/api/config`

**No code changes needed!** 🎉

All bike-specific settings are in:
- `config/bike_models.json` (bike definitions)
- `.env` (active model selection)

This makes it easy to:
- ✅ Support multiple bikes
- ✅ Switch between bikes quickly
- ✅ Add new bikes without coding
- ✅ Keep configurations organized
- ✅ Deploy same code to different bikes

---

**Questions? Check the logs:**
```bash
~/rasperryPi_setup/scripts/logs.sh
```
