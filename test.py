from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import subprocess
import platform
import psutil
import requests
import time


def ping_host(host="8.8.8.8"):
    """Real ping command to Google DNS"""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "4", host]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return "Ping timeout"
    except Exception as e:
        return f"Ping error: {str(e)}"
    


print(ping_host())
