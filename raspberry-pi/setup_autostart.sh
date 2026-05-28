#!/bin/bash
# DustCheck - Setup auto-start on boot
# Run this script once on the Raspberry Pi: sudo bash setup_autostart.sh

echo "=== DustCheck Auto-Start Setup ==="

# Stop any existing monitor process
echo "[1/5] Stopping existing monitor processes..."
pkill -f "python3.*monitor.py" 2>/dev/null || true

# Copy service file
echo "[2/5] Installing systemd service..."
sudo cp /home/pi/dustcheck/dustcheck.service /etc/systemd/system/dustcheck.service

# Reload systemd
echo "[3/5] Reloading systemd..."
sudo systemctl daemon-reload

# Enable on boot
echo "[4/5] Enabling auto-start on boot..."
sudo systemctl enable dustcheck.service

# Start now
echo "[5/5] Starting DustCheck monitor..."
sudo systemctl start dustcheck.service

echo ""
echo "=== Setup Complete ==="
echo "Status:"
sudo systemctl status dustcheck.service --no-pager -l
echo ""
echo "Useful commands:"
echo "  sudo systemctl status dustcheck   # Check status"
echo "  sudo systemctl restart dustcheck  # Restart"
echo "  sudo systemctl stop dustcheck     # Stop"
echo "  tail -f /home/pi/dustcheck/monitor.log  # View logs"
