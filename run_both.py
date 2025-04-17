#!/usr/bin/env python3
import subprocess
import threading
import sys
import os

def stream_output(process, prefix):
    """Stream output from a process with a prefix"""
    for line in iter(process.stdout.readline, b''):
        sys.stdout.write(f"{prefix} | {line.decode()}")
        sys.stdout.flush()

def run_flask():
    env = os.environ.copy()
    env["FLASK_APP"] = "slack_bot.py"
    process = subprocess.Popen(
        ["flask", "run", "--port=5005"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        text=False
    )
    stream_output(process, "FLASK")

def run_watcher():
    process = subprocess.Popen(
        ["python3", "watcher.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False
    )
    stream_output(process, "WATCH")

if __name__ == "__main__":
    print("Starting both processes...")
    
    # Start each process in its own thread
    flask_thread = threading.Thread(target=run_flask)
    watcher_thread = threading.Thread(target=run_watcher)
    
    flask_thread.daemon = True
    watcher_thread.daemon = True
    
    flask_thread.start()
    watcher_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            flask_thread.join(1)
            watcher_thread.join(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
