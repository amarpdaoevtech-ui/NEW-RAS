#!/bin/bash
# DAO EV Tech - Raspberry Pi Production Setup Script
# This script sets up the complete kiosk mode dashboard on Raspberry Pi 4

# Note: We don't use 'set -e' to allow the script to continue even if some
# non-critical commands fail (like disabling services that don't exist)

echo "======================================"
echo "🚀 DAO EV Tech - Raspberry Pi Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}📁 Project root: $PROJECT_ROOT${NC}"

# ================= STEP 1: System Update =================
echo -e "\n${YELLOW}📦 Step 1: Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# ================= STEP 2: Install Dependencies =================
echo -e "\n${YELLOW}🔧 Step 2: Installing dependencies...${NC}"

# Install Node.js (v18.x LTS)
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    echo "Node.js already installed: $(node --version)"
fi

# Install Python dependencies
echo "Installing Python packages..."
sudo apt-get install -y python3-pip python3-venv python3-dev

# Install system dependencies
echo "Installing system packages..."
sudo apt-get install -y \
    nginx \
    chromium \
    unclutter \
    xdotool \
    x11-xserver-utils \
    git \
    sqlite3

# ================= STEP 3: Configure UART =================
echo -e "\n${YELLOW}⚙️  Step 3: Configuring UART for RS-485...${NC}"

# Backup config.txt
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup

# Enable UART
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
fi

# Disable Bluetooth to free up hardware UART
if ! grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt; then
    echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt
fi

# Disable console on serial port (check if service exists first)
if systemctl list-unit-files | grep -q hciuart; then
    sudo systemctl disable hciuart 2>/dev/null || true
    echo "Disabled hciuart service"
else
    echo "hciuart service not found (this is normal on newer Raspberry Pi OS)"
fi

# Try to disable serial console if it exists
if systemctl list-unit-files | grep -q serial-getty@ttyAMA0; then
    sudo systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true
    echo "Disabled serial console on ttyAMA0"
fi

# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER

echo -e "${GREEN}✅ UART configured${NC}"

# ================= STEP 4: Configure Display =================
echo -e "\n${YELLOW}🖥️  Step 4: Configuring 7-inch display (1024x600)...${NC}"

# Set custom HDMI mode for 1024x600
if ! grep -q "hdmi_group=2" /boot/firmware/config.txt; then
    cat << EOF | sudo tee -a /boot/firmware/config.txt

# 7-inch display configuration (1024x600)
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 3 0 0 0
hdmi_drive=2
EOF
fi

echo -e "${GREEN}✅ Display configured${NC}"

# ================= STEP 5: Setup Project Environment =================
echo -e "\n${YELLOW}🏗️  Step 5: Setting up project environment...${NC}"

cd "$PROJECT_ROOT"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file to set your bike model${NC}"
fi

# Create necessary directories
mkdir -p data logs

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Install Node.js dependencies and build frontend
echo "Building frontend..."
cd "$PROJECT_ROOT"
npm install
npm run build

echo -e "${GREEN}✅ Project environment ready${NC}"

# ================= STEP 6: Configure Nginx =================
echo -e "\n${YELLOW}🌐 Step 6: Configuring Nginx...${NC}"

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/bms-dashboard << EOF
server {
    listen 80;
    server_name localhost;
    
    # Frontend
    root "$PROJECT_ROOT/dist";
    index index.html;
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # WebSocket proxy
    location /socket.io/ {
        proxy_pass http://localhost:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/bms-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo -e "${GREEN}✅ Nginx configured${NC}"

# ================= STEP 7: Create Systemd Service =================
echo -e "\n${YELLOW}⚙️  Step 7: Creating systemd service for backend...${NC}"

sudo tee /etc/systemd/system/bms-backend.service << EOF
[Unit]
Description=DAO BMS Backend Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_ROOT/backend
Environment="PATH=$PROJECT_ROOT/backend/venv/bin"
ExecStart=$PROJECT_ROOT/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable bms-backend.service
sudo systemctl start bms-backend.service

echo -e "${GREEN}✅ Backend service created and started${NC}"

# ================= STEP 8: Configure Kiosk Mode =================
echo -e "\n${YELLOW}🖼️  Step 8: Configuring kiosk mode...${NC}"

# Determine correct browser command
if command -v chromium &> /dev/null; then
    BROWSER_CMD="chromium"
else
    BROWSER_CMD="chromium-browser"
fi

KIOSK_ARGS="--noerrdialogs --disable-infobars --kiosk --incognito --disable-session-crashed-bubble --disable-restore-session-state --password-store=basic http://localhost"

# 1. Setup for Labwc (New Raspberry Pi OS / Wayland)
echo "Configuring for Labwc..."
mkdir -p /home/$USER/.config/labwc

tee /home/$USER/.config/labwc/autostart << EOF
#!/bin/bash
# Disable screen blanking
xset s off &
xset -dpms &
xset s noblank &

# Hide mouse cursor
unclutter -idle 0.5 -root &

# Wait for services to start
sleep 10

# Start Chromium in kiosk mode
$BROWSER_CMD $KIOSK_ARGS &
EOF
chmod +x /home/$USER/.config/labwc/autostart

# 2. Setup for LXDE-pi (Older Raspberry Pi OS / X11)
echo "Configuring for LXDE-pi..."
mkdir -p /home/$USER/.config/lxsession/LXDE-pi

tee /home/$USER/.config/lxsession/LXDE-pi/autostart << EOF
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
@xscreensaver -no-splash

# Disable screen blanking
@xset s off
@xset -dpms
@xset s noblank

# Hide mouse cursor
@unclutter -idle 0.5 -root

# Wait for services to start
@sleep 10

# Start Chromium in kiosk mode
@$BROWSER_CMD $KIOSK_ARGS
EOF

echo -e "${GREEN}✅ Kiosk mode configured for Labwc and LXDE${NC}"

echo -e "${GREEN}✅ Kiosk mode configured${NC}"

# ================= STEP 9: Create Management Scripts =================
echo -e "\n${YELLOW}📝 Step 9: Creating management scripts...${NC}"

# Create start script
tee "$PROJECT_ROOT/scripts/start.sh" << 'EOF'
#!/bin/bash
echo "Starting BMS Backend..."
sudo systemctl start bms-backend.service
echo "Starting Nginx..."
sudo systemctl start nginx
echo "✅ Services started"
EOF

# Create stop script
tee "$PROJECT_ROOT/scripts/stop.sh" << 'EOF'
#!/bin/bash
echo "Stopping BMS Backend..."
sudo systemctl stop bms-backend.service
echo "Stopping Nginx..."
sudo systemctl stop nginx
echo "✅ Services stopped"
EOF

# Create status script
tee "$PROJECT_ROOT/scripts/status.sh" << 'EOF'
#!/bin/bash
echo "=== BMS Backend Status ==="
sudo systemctl status bms-backend.service --no-pager
echo ""
echo "=== Nginx Status ==="
sudo systemctl status nginx --no-pager
echo ""
echo "=== Recent Logs ==="
sudo journalctl -u bms-backend.service -n 20 --no-pager
EOF

# Create logs script
tee "$PROJECT_ROOT/scripts/logs.sh" << 'EOF'
#!/bin/bash
echo "Following BMS Backend logs (Ctrl+C to exit)..."
sudo journalctl -u bms-backend.service -f
EOF

# Create update script
tee "$PROJECT_ROOT/scripts/update.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Stopping services..."
sudo systemctl stop bms-backend.service

echo "Updating frontend..."
npm install
npm run build

echo "Updating backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate

echo "Restarting services..."
sudo systemctl restart bms-backend.service
sudo systemctl restart nginx

echo "✅ Update complete"
EOF

# Make scripts executable
chmod +x "$PROJECT_ROOT/scripts/"*.sh

echo -e "${GREEN}✅ Management scripts created${NC}"

# ================= STEP 10: Final Steps =================
echo -e "\n${YELLOW}🎯 Step 10: Final configuration...${NC}"

# Create desktop shortcut
tee /home/$USER/Desktop/BMS-Dashboard.desktop << EOF
[Desktop Entry]
Type=Application
Name=BMS Dashboard
Comment=Open BMS Dashboard
Exec=chromium-browser --kiosk http://localhost
Icon=chromium-browser
Terminal=false
Categories=Application;
EOF

chmod +x /home/$USER/Desktop/BMS-Dashboard.desktop

echo -e "\n${GREEN}======================================"
echo "✅ Setup Complete!"
echo "======================================${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Edit .env file to set your bike model:"
echo "   nano $PROJECT_ROOT/.env"
echo ""
echo "2. Reboot the Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "3. After reboot, the dashboard will start automatically in kiosk mode"
echo ""
echo "📚 Management Commands:"
echo "   Start:  $PROJECT_ROOT/scripts/start.sh"
echo "   Stop:   $PROJECT_ROOT/scripts/stop.sh"
echo "   Status: $PROJECT_ROOT/scripts/status.sh"
echo "   Logs:   $PROJECT_ROOT/scripts/logs.sh"
echo "   Update: $PROJECT_ROOT/scripts/update.sh"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard: http://localhost"
echo "   API:       http://localhost/api/bms"
echo "   Config:    http://localhost/api/config"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Reboot required for UART and display settings!${NC}"
