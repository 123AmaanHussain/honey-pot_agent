"""
Email Monitor Manager
Controls the Node.js email monitor as a subprocess from Python.
Provides email credentials management and process management for the frontend.
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
email_config: Optional[Dict[str, str]] = None


def load_email_config_from_db():
    """Load email configuration from database on startup."""
    global email_config
    try:
        from app.db.repository import get_config
        
        imap_host = get_config('email_imap_host', decrypt=True)
        imap_port = get_config('email_imap_port')
        imap_user = get_config('email_imap_user', decrypt=True)
        imap_pass = get_config('email_imap_pass', decrypt=True)
        
        if imap_host and imap_user and imap_pass:
            email_config = {
                'imap_host': imap_host,
                'imap_port': imap_port or '993',
                'imap_user': imap_user,
                'imap_pass': imap_pass
            }
            print("✅ Email configuration loaded from database (decrypted)")
    except Exception as e:
        print(f"⚠️  Could not load email config from database: {e}")


# Load config on module import
load_email_config_from_db()


def set_email_config(host: str, port: str, user: str, password: str):
    """Set the email configuration for the monitor."""
    global email_config
    email_config = {
        'imap_host': host,
        'imap_port': port,
        'imap_user': user,
        'imap_pass': password
    }


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
    """Start the email monitor subprocess."""
    global monitor_process, monitor_thread, recent_output, email_config
    
    if monitor_process and monitor_process.poll() is None:
        return {"status": "already_running", "message": "Monitor is already running"}
    
    if not email_config:
        return {"status": "error", "message": "Email configuration not set. Please provide email credentials first."}
    
    try:
        local_agent_path = Path(__file__).parent / "local_agent"
        monitor_script = local_agent_path / "email_monitor.js"
        
        if not monitor_script.exists():
            return {"status": "error", "message": f"Monitor script not found: {monitor_script}"}
        
        # Clear previous output
        with output_lock:
            recent_output.clear()
        
        # Start the Node.js monitor with email config as arguments
        monitor_process = subprocess.Popen(
            ["node", str(monitor_script), 
             email_config['imap_host'],
             email_config['imap_port'],
             email_config['imap_user'],
             email_config['imap_pass']],
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
            "message": "Email monitor starting...",
            "pid": monitor_process.pid
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def stop_monitor() -> Dict[str, Any]:
    """Stop the email monitor subprocess."""
    global monitor_process
    
    if not monitor_process:
        return {"status": "not_running", "message": "Monitor is not running"}
    
    try:
        monitor_process.terminate()
        monitor_process.wait(timeout=5)
        monitor_process = None
        return {"status": "stopped", "message": "Email monitor stopped"}
    except subprocess.TimeoutExpired:
        monitor_process.kill()
        monitor_process = None
        return {"status": "killed", "message": "Email monitor forcefully stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_status() -> Dict[str, Any]:
    """Get current monitor status."""
    global monitor_process, recent_output, email_config
    
    if not monitor_process:
        return {
            "status": "not_running",
            "running": False,
            "message": "Monitor is not running",
            "config_set": bool(email_config)
        }
    
    if monitor_process.poll() is None:
        # Check recent output for connection status
        with output_lock:
            output_copy = recent_output.copy()
        
        connected = any("connected" in line.lower() or "listening" in line.lower() or "ready" in line.lower() for line in output_copy)
        error = any("error" in line.lower() or "failed" in line.lower() or "authentication" in line.lower() for line in output_copy)
        
        return {
            "status": "running",
            "running": True,
            "pid": monitor_process.pid,
            "connected": connected,
            "error": error,
            "config_set": bool(email_config),
            "recent_output": output_copy[-5:] if output_copy else []
        }
    else:
        monitor_process = None
        return {
            "status": "stopped",
            "running": False,
            "message": "Monitor process has exited",
            "config_set": bool(email_config)
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
    print("Testing Email Manager...")
    result = start_monitor()
    print(f"Start result: {result}")
    
    time.sleep(5)
    status = get_status()
    print(f"Status: {status}")
    
    time.sleep(5)
    output = get_recent_output()
    print(f"Recent output: {output}")
