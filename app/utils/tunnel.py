"""Minimal tunnel management for ParkPartner.

Single entry point: use `TunnelManager` as a context manager.
"""

import logging
import re
import subprocess
import time

from app.config import get_log_filepath

logger = logging.getLogger(__name__)


def _extract_url(line: str) -> str | None:
    """Extract tunnel URL from a pre-cleaned localhost.run output line.

    Only matches lines containing the signal phrase:
    "tunneled with tls termination".
    """
    if "tunneled with tls termination" not in line:
        return None
    match = re.search(r"https://[a-zA-Z0-9.-]+\.(lhr\.life|localhost\.run)", line)
    return match.group(0).rstrip("],;)'\" ") if match else None


class TunnelManager:
    """Context manager for localhost.run tunnel lifecycle."""

    def __init__(self, port: int = 8000, timeout: int = 30):
        self.port = port
        self.timeout = timeout
        self.process = None
        self.tunnel_url = None
        self._error_banner = ""
        self._raw_output = ""

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
            raw_line = self.process.stdout.readline().strip()
            if raw_line:
                # Save raw line before stripping (for logging)
                self._raw_output += raw_line + "\n"

                # Strip ANSI escape codes and non-printable characters
                line = re.sub(r"[\x1b\x00-\x1F\x7F-\x9F]+", "", raw_line)
                line = line.replace("\r", "")
                self._error_banner += line + "\n"

                if url := _extract_url(line):
                    elapsed = time.time() - start_time
                    logger.info(f"Tunnel ready: {url} ({elapsed:.1f}s)")
                    self.tunnel_url = url
                    return url
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Tunnel timeout ({self.timeout}s)")
            time.sleep(0.1)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Log full session output before cleanup
        if self._raw_output:
            log_path = get_log_filepath("tunnel", "tunnel")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(self._raw_output)

        if self.process:
            logger.info("Stopping tunnel...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
