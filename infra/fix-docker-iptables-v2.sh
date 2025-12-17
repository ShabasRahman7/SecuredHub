#!/bin/bash
# Comprehensive fix for Docker iptables issue with nftables
# Run with: sudo bash fix-docker-iptables-v2.sh

set -e

echo "=== Fixing Docker iptables/nftables issue ==="

# Step 1: Switch to iptables-legacy
echo "Step 1: Switching to iptables-legacy..."
update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || {
    echo "Warning: Could not set iptables to legacy mode (may already be set)"
}
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || {
    echo "Warning: Could not set ip6tables to legacy mode (may already be set)"
}

# Step 2: Configure Docker to use iptables-legacy
echo "Step 2: Configuring Docker daemon..."
DOCKER_DAEMON_JSON="/etc/docker/daemon.json"
DOCKER_DAEMON_DIR="/etc/docker"

# Create docker directory if it doesn't exist
mkdir -p "$DOCKER_DAEMON_DIR"

# Backup existing daemon.json if it exists
if [ -f "$DOCKER_DAEMON_JSON" ]; then
    cp "$DOCKER_DAEMON_JSON" "${DOCKER_DAEMON_JSON}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backed up existing daemon.json"
fi

# Create or update daemon.json
cat > "$DOCKER_DAEMON_JSON" << 'EOF'
{
  "iptables": true,
  "ip-forward": true
}
EOF

echo "Created/updated Docker daemon.json"

# Step 3: Stop Docker
echo "Step 3: Stopping Docker..."
systemctl stop docker

# Step 4: Flush and recreate iptables chains
echo "Step 4: Flushing iptables rules..."
iptables-legacy -t filter -F DOCKER-ISOLATION-STAGE-1 2>/dev/null || true
iptables-legacy -t filter -F DOCKER-ISOLATION-STAGE-2 2>/dev/null || true
iptables-legacy -t filter -X DOCKER-ISOLATION-STAGE-1 2>/dev/null || true
iptables-legacy -t filter -X DOCKER-ISOLATION-STAGE-2 2>/dev/null || true

# Create the chains
echo "Step 5: Creating iptables chains..."
iptables-legacy -t filter -N DOCKER-ISOLATION-STAGE-1 || true
iptables-legacy -t filter -N DOCKER-ISOLATION-STAGE-2 || true

# Add basic rules
iptables-legacy -t filter -A DOCKER-ISOLATION-STAGE-1 -j DOCKER-ISOLATION-STAGE-2 || true
iptables-legacy -t filter -A DOCKER-ISOLATION-STAGE-2 -j RETURN || true

# Step 6: Start Docker
echo "Step 6: Starting Docker..."
systemctl start docker

# Wait for Docker to be ready
echo "Waiting for Docker to be ready..."
sleep 5

# Step 7: Verify
echo "Step 7: Verifying Docker..."
if docker info > /dev/null 2>&1; then
    echo "✓ Docker is running"
else
    echo "✗ Docker is not running properly"
    exit 1
fi

# Check iptables chains
if iptables-legacy -t filter -L DOCKER-ISOLATION-STAGE-2 > /dev/null 2>&1; then
    echo "✓ iptables chains exist"
else
    echo "⚠ Warning: iptables chains may not exist (Docker will create them)"
fi

echo ""
echo "=== Fix complete! ==="
echo "You can now run: docker compose up -d"
echo ""
echo "If you still have issues, try:"
echo "  1. Reboot the system"
echo "  2. Check Docker logs: journalctl -u docker -n 50"


