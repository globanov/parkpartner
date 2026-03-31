"""Minimal tunnel management for ParkPartner."""

import logging
import re
import subprocess
import time

logger = logging.getLogger(__name__)
_tunnel_process: subprocess.Popen | None = None


def start_tunnel(port: int) -> str:
    """Start localhost.run tunnel, return URL."""
    global _tunnel_process
    logger.info(f"Starting tunnel on port {port}...")

    _tunnel_process = subprocess.Popen(
        ["ssh", "-R", f"80:localhost:{port}", "nokey@localhost.run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    while True:
        line = _tunnel_process.stdout.readline().strip()
        if line:
            print(line)
            if url := _extract_url(line):
                logger.info(f"Tunnel ready: {url}")
                return url


def stop_tunnel() -> None:
    """Stop tunnel process."""
    global _tunnel_process
    if _tunnel_process:
        logger.info("Stopping tunnel...")
        _tunnel_process.terminate()
        _tunnel_process.wait()
        _tunnel_process = None


def _extract_url(line: str) -> str | None:
    """Extract HTTPS URL from localhost.run output."""
    # Match tunnel URLs: https://*.localhost.run or https://*.lhr.life
    # Exclude admin URLs
    match = re.search(
        r"https://(?!admin)[a-zA-Z0-9.-]+\.(localhost\.run|lhr\.life)", line
    )
    return match.group(0) if match else None


class TunnelManager:
    """Context manager for localhost.run tunnel lifecycle."""

    def __init__(self, port: int = 8000, timeout: int = 30):
        self.port = port
        self.timeout = timeout
        self.process = None
        self.tunnel_url = None

    def __enter__(self) -> str:
        self.process = subprocess.Popen(
            ["ssh", "-R", f"80:localhost:{self.port}", "nokey@localhost.run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        start_time = time.time()
        while True:
            if self.process.poll() is not None:
                raise RuntimeError(f"Tunnel exited: {self.process.returncode}")
            line = self.process.stdout.readline().strip()
            if line:
                print(line)
                if url := _extract_url(line):
                    elapsed = time.time() - start_time
                    logger.info(f"Tunnel ready: {url} ({elapsed:.1f}s)")
                    self.tunnel_url = url
                    return url
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Tunnel timeout ({self.timeout}s)")
            time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.process:
            logger.info("Stopping tunnel...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
