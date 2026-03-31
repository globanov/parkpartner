#!/usr/bin/env python3
"""
ParkPartner + localhost.run tunnel startup.

Usage:
    python start_parkpartner_with_tunnel.py

Stop:
    Press Ctrl+C
"""

import signal
import subprocess
import sys

from app.utils.server import is_port_in_use, start_server, wait_for_server
from app.utils.tunnel import TunnelManager

# Configuration
PORT = 8000

# Global reference for cleanup
server_process = None


def cleanup(signum=None, frame=None):
    """Clean up server process on exit."""
    print("\n🛑 Stopping server...")
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
    print("✅ Stopped")
    sys.exit(0)


def main():
    global server_process

    print("🚀 ParkPartner + Tunnel — starting...")

    # Check if port is already in use
    if is_port_in_use(PORT):
        print(f"❌ Error: Port {PORT} is already in use!")
        print("   Stop existing process: pkill -f 'parkpartner:app'")
        sys.exit(1)

    # Start server
    server_process = start_server(PORT)
    print(f"✅ Server started (PID: {server_process.pid})")

    # Wait for health check
    if not wait_for_server(PORT):
        print("❌ Server failed to start")
        server_process.kill()
        sys.exit(1)

    print()
    print("📍 Open in browser (local access):")
    print(f"   👉 http://localhost:{PORT}")
    print()

    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Start tunnel
    print("🔗 Starting localhost.run tunnel...")
    try:
        with TunnelManager(port=PORT) as tunnel_url:
            print(f"🔗 Tunnel URL: {tunnel_url}")
            print()
            print("Press Ctrl+C to stop")
            while True:
                import time

                time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
