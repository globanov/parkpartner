#!/usr/bin/env python3
"""
ParkPartner E2E Test Runner

Starts the application, runs E2E tests, and ensures clean shutdown.

Usage:
    python run_e2e_tests.py

Options:
    --verbose, -v      Show detailed output
    --headed           Run browser tests with visible window
    --test PATTERN     Run specific test (e.g., --test test_complete)
    --help, -h         Show this help message

Requirements:
    - Ollama service running (ollama serve)
    - Model pulled (ollama pull qwen2.5:3b)
    - Playwright installed (pip install playwright && playwright install chromium)
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Configuration
SERVER_HOST = "localhost"
SERVER_PORT = "8000"
HEALTH_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/health"
PROJECT_ROOT = Path(__file__).parent.absolute()
LOGS_DIR = PROJECT_ROOT / "logs"
E2E_TEST_FILE = "tests/system/test_e2e_001_browser.py"


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def log(message, level="INFO", color=None):
    """Print colored log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"[{timestamp}] {level}:"

    if color:
        print(f"{color}{prefix} {message}{Colors.ENDC}")
    else:
        print(f"{prefix} {message}")


def log_info(message):
    log(message, "INFO", Colors.OKCYAN)


def log_success(message):
    log(message, "✓", Colors.OKGREEN)


def log_error(message):
    log(message, "✗", Colors.FAIL)


def log_warning(message):
    log(message, "⚠", Colors.WARNING)


def check_prerequisites():
    """Check if all required services and dependencies are available"""
    log_info("Checking prerequisites...")

    all_ok = True

    # Check Ollama
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and "qwen2.5" in result.stdout.decode():
            log_success("Ollama service is running with qwen2.5 model")
        else:
            log_warning("Ollama service may not have qwen2.5 model pulled")
            log_info("Run: ollama pull qwen2.5:3b")
    except Exception:
        log_warning("Ollama service not detected")
        log_info("Start with: ollama serve")

    # Check Playwright
    try:
        __import__("playwright")
        log_success("Playwright is installed")
    except ImportError:
        log_error("Playwright not installed")
        log_info("Run: pip install playwright && playwright install chromium")
        all_ok = False

    # Check if port is available
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex((SERVER_HOST, int(SERVER_PORT)))
        if result == 0:
            log_warning(f"Port {SERVER_PORT} is already in use")
            log_info("An existing server may be running")
        else:
            log_success(f"Port {SERVER_PORT} is available")
    finally:
        sock.close()

    return all_ok


def start_server():
    """Start ParkPartner server"""
    log_info("Starting ParkPartner server...")

    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)

    # Start server process
    log_file = LOGS_DIR / f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "parkpartner:app",
            "--host",
            "0.0.0.0",
            "--port",
            SERVER_PORT,
            "--log-level",
            "warning",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(PROJECT_ROOT),
    )

    log_info(f"Server PID: {process.pid}")
    log_info(f"Log file: {log_file}")

    # Wait for server to be ready
    log_info("Waiting for server to be ready...")

    import requests

    max_attempts = 30
    for attempt in range(max_attempts):
        time.sleep(1)
        try:
            response = requests.get(HEALTH_URL, timeout=2)
            if response.status_code == 200:
                log_success(f"Server is ready (attempt {attempt + 1}/{max_attempts})")
                return process
        except Exception:
            if attempt % 5 == 0:
                log_info(f"  Still waiting... ({attempt + 1}/{max_attempts})")

    log_error("Server failed to start within timeout")
    process.terminate()
    return None


def run_e2e_tests(server_process, args):
    """Run E2E tests"""
    log_info("Running E2E tests...")

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", E2E_TEST_FILE, "-v", "--tb=short"]

    if args.verbose:
        cmd.append("-s")  # Show print statements

    if args.headed:
        cmd.append("--headed")  # Show browser window

    if args.test:
        cmd.append(f"-k {args.test}")

    log_info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            log_success("All E2E tests passed!")
            return True
        log_error(f"E2E tests failed with code {result.returncode}")
        return False

    except subprocess.TimeoutExpired:
        log_error("E2E tests timed out (5 minutes)")
        return False
    except Exception as e:
        log_error(f"E2E tests error: {e}")
        return False


def stop_server(process):
    """Stop server process and ensure cleanup"""
    if process is None:
        return

    log_info("Stopping server...")

    try:
        # Try graceful shutdown first
        process.terminate()

        # Wait for process to exit
        try:
            process.wait(timeout=10)
            log_success("Server stopped gracefully")
        except subprocess.TimeoutExpired:
            log_warning("Server didn't stop gracefully, forcing...")
            process.kill()
            process.wait()
            log_success("Server force-killed")

    except Exception as e:
        log_error(f"Error stopping server: {e}")


def cleanup_all_processes():
    """Ensure all related processes are stopped"""
    log_info("Cleaning up any remaining processes...")

    # Kill any process on our port
    try:
        if sys.platform == "win32":
            # Windows
            subprocess.run(
                f"netstat -ano | findstr :{SERVER_PORT}",
                shell=True,
                capture_output=True,
            )
            # Extract PID and kill
        else:
            # Unix-like
            result = subprocess.run(
                f"lsof -ti:{SERVER_PORT}", shell=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        log_info(f"Killed process {pid}")
                    except Exception:
                        pass
    except Exception:
        pass

    # Kill any orphaned uvicorn processes from this run
    try:
        if sys.platform == "win32":
            subprocess.run(
                "taskkill /F /IM python.exe /FI 'WINDOWTITLE eq *uvicorn*'", shell=True
            )
        else:
            subprocess.run("pkill -f 'uvicorn.*parkpartner'", shell=True)
    except Exception:
        pass

    log_success("Cleanup complete")


def print_summary(tests_passed, duration):
    """Print test run summary"""
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}E2E Test Run Summary{Colors.ENDC}")
    print("=" * 60)

    if tests_passed:
        print(f"{Colors.OKGREEN}✓ Tests: PASSED{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}✗ Tests: FAILED{Colors.ENDC}")

    print(f"Duration: {duration:.1f} seconds")
    print("Server: Stopped")
    print(f"Logs: {LOGS_DIR}/")
    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run ParkPartner E2E tests with automatic server management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output including print statements",
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser tests with visible window (for debugging)",
    )

    parser.add_argument(
        "-t", "--test", type=str, help="Run specific test (pytest -k pattern)"
    )

    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip prerequisite checks"
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}🚀 ParkPartner E2E Test Runner{Colors.ENDC}")
    print("=" * 60 + "\n")

    start_time = time.time()
    server_process = None
    tests_passed = False

    try:
        # Check prerequisites
        if not args.skip_checks and not check_prerequisites():
            log_error("Prerequisites check failed")
            sys.exit(1)

        # Start server
        server_process = start_server()
        if not server_process:
            log_error("Failed to start server")
            sys.exit(1)

        # Run tests
        tests_passed = run_e2e_tests(server_process, args)

    except KeyboardInterrupt:
        log_warning("Interrupted by user")
        tests_passed = False

    except Exception as e:
        log_error(f"Unexpected error: {e}")
        tests_passed = False

    finally:
        # Always cleanup
        stop_server(server_process)
        cleanup_all_processes()

        # Print summary
        duration = time.time() - start_time
        print_summary(tests_passed, duration)

        # Exit with appropriate code
        sys.exit(0 if tests_passed else 1)


if __name__ == "__main__":
    main()
