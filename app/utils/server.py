"""Server management utilities for ParkPartner."""

import logging
import socket
import subprocess
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def is_port_in_use(port: int) -> bool:
    """Check if port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for server health endpoint to respond."""
    logger.info(f"Waiting for server on port {port}...")
    start_time = time.time()
    health_url = f"http://localhost:{port}/health"

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(health_url, timeout=2) as response:  # noqa: S310
                if response.status == 200:
                    logger.info("Server is ready")
                    return True
        except (urllib.error.URLError, ConnectionRefusedError):
            pass
        time.sleep(1)

    logger.error(f"Server did not start within {timeout} seconds")
    return False


def start_server(port: int = 8000) -> subprocess.Popen:
    """Start ParkPartner server as subprocess."""
    if is_port_in_use(port):
        raise RuntimeError(f"Port {port} is already in use")

    logger.info(f"Starting server on port {port}...")
    import sys

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "parkpartner:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
