#!/bin/bash
#
# ParkPartner + localhost.run tunnel startup
#
# Usage:
#   ./start_parkpartner_with_tunnel.sh
#
# Stop:
#   Press Ctrl+C
#

set -e

echo "🚀 ParkPartner + Tunnel — starting..."

# Check if port 8000 is already in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "❌ Error: Port 8000 is already in use!"
    echo "   Stop existing process: pkill -f 'parkpartner:app'"
    exit 1
fi

# Start server
echo "📡 Starting server on port 8000..."
python -m uvicorn parkpartner:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for health check
echo "⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Server is ready"
        break
    fi
    sleep 1
done

# Verify server started
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "📍 Open in browser (local access):"
echo "   👉 http://localhost:8000"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping server..."
    kill $SERVER_PID 2>/dev/null || true
    echo "✅ Stopped"
    exit 0
}

# Trap Ctrl+C and exit
trap cleanup EXIT INT TERM

# Start tunnel
echo "🔗 Starting localhost.run tunnel..."
echo "⚠️  Note: Traffic routes through external server"
echo ""
ssh -R 80:localhost:8000 nokey@localhost.run
