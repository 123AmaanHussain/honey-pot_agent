"""
Telegram Monitor Manager
Controls the Node.js Telegram monitor as a subprocess from Python.
Provides bot token capture and process management for the frontend.
"""
import subprocess
import threading
import os
import json
import time
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global storage for recent output (thread-safe via list append)
recent_output = []
max_output_lines = 100
monitor_process: Optional[subprocess.Popen] = None
monitor_thread: Optional[threading.Thread] = None
output_lock = threading.Lock()
bot_token: Optional[str] = None


def load_token_from_db():
    """Load Telegram bot token from database on startup."""
    global bot_token
    try:
        from app.db.repository import get_config
        token = get_config('telegram_bot_token', decrypt=True)
        if token:
            bot_token = token
            print("✅ Telegram bot token loaded from database (decrypted)")
    except Exception as e:
        print(f"⚠️  Could not load token from database: {e}")


# Load token on module import
load_token_from_db()


def set_bot_token(token: str):
    """Set the Telegram bot token for the monitor."""
    global bot_token
    bot_token = token


def add_output_line(line: str):
    """Thread-safe output line storage."""
    global recent_output
    with output_lock:
        recent_output.append(line)
        if len(recent_output) > max_output_lines:
            recent_output.pop(0)


def read_output(process: subprocess.Popen):
    """Read subprocess output line by line and store globally."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                stripped = line.strip()
                add_output_line(stripped)
    except Exception as e:
        add_output_line(f"ERROR: {str(e)}")


def start_monitor() -> Dict[str, Any]:
    """Start the Telegram monitor subprocess."""
    global monitor_process, monitor_thread, recent_output, bot_token
    
    if monitor_process and monitor_process.poll() is None:
        return {"status": "already_running", "message": "Monitor is already running"}
    
    if not bot_token:
        return {"status": "error", "message": "Bot token not set. Please provide a bot token first."}
    
    try:
        local_agent_path = Path(__file__).parent / "local_agent"
        monitor_script = local_agent_path / "telegram_monitor.js"
        
        if not monitor_script.exists():
            return {"status": "error", "message": f"Monitor script not found: {monitor_script}"}
        
        # Clear previous output
        with output_lock:
            recent_output.clear()
        
        # Start the Node.js monitor with bot token as argument
        monitor_process = subprocess.Popen(
            ["node", str(monitor_script), bot_token],
            cwd=str(local_agent_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True
        )
        
        # Start thread to read output
        monitor_thread = threading.Thread(
            target=read_output,
            args=(monitor_process,),
            daemon=True
        )
        monitor_thread.start()
        
        return {
            "status": "starting",
            "message": "Telegram monitor starting...",
            "pid": monitor_process.pid
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def stop_monitor() -> Dict[str, Any]:
    """Stop the Telegram monitor subprocess."""
    global monitor_process
    
    if not monitor_process:
        return {"status": "not_running", "message": "Monitor is not running"}
    
    try:
        monitor_process.terminate()
        monitor_process.wait(timeout=5)
        monitor_process = None
        return {"status": "stopped", "message": "Telegram monitor stopped"}
    except subprocess.TimeoutExpired:
        monitor_process.kill()
        monitor_process = None
        return {"status": "killed", "message": "Telegram monitor forcefully stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_status() -> Dict[str, Any]:
    """Get current monitor status."""
    global monitor_process, recent_output
    
    if not monitor_process:
        return {
            "status": "not_running",
            "running": False,
            "message": "Monitor is not running"
        }
    
    if monitor_process.poll() is None:
        # Check recent output for bot token and connection status
        with output_lock:
            output_copy = recent_output.copy()
        
        token_required = any("token" in line.lower() or "bot_token" in line.lower() for line in output_copy)
        connected = any("connected" in line.lower() or "ready" in line.lower() or "listening" in line.lower() for line in output_copy)
        error = any("error" in line.lower() or "failed" in line.lower() for line in output_copy)
        
        return {
            "status": "running",
            "running": True,
            "pid": monitor_process.pid,
            "token_required": token_required,
            "connected": connected,
            "error": error,
            "recent_output": output_copy[-5:] if output_copy else []
        }
    else:
        monitor_process = None
        return {
            "status": "stopped",
            "running": False,
            "message": "Monitor process has exited"
        }


def get_recent_output(lines: int = 20) -> Dict[str, Any]:
    """Get recent output from the monitor."""
    global recent_output
    with output_lock:
        output_copy = recent_output.copy()
    
    return {
        "status": "success",
        "output": output_copy[-lines:] if output_copy else []
    }


if __name__ == "__main__":
    # Test the manager
    print("Testing Telegram Manager...")
    result = start_monitor()
    print(f"Start result: {result}")
    
    time.sleep(5)
    status = get_status()
    print(f"Status: {status}")
    
    time.sleep(5)
    output = get_recent_output()
    print(f"Recent output: {output}")
