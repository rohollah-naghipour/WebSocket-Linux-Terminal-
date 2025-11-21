from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import subprocess
import platform
import psutil
import os
import shlex

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# 🚨 COMPLETE SHELL ACCESS - DANGEROUS!
def execute_shell_command(command):
    """🚨 Execute any shell command - COMPLETE SHELL ACCESS"""
    try:
        # Get current working directory
        current_dir = os.getcwd()
        
        # Execute the command with proper shell
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir
        )
        
        stdout, stderr = process.communicate(timeout=30)
        
        return {
            'success': True,
            'command': command,
            'output': stdout,
            'error': stderr,
            'returncode': process.returncode,
            'current_dir': current_dir,
            'user': os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USER', 'unknown'),
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'command': command,
            'error': 'Command timed out after 30 seconds',
            'current_dir': os.getcwd(),
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'command': command,
            'error': str(e),
            'current_dir': os.getcwd(),
            'returncode': -1
        }

def change_directory(path):
    """Change current working directory"""
    try:
        if path == "~":
            path = os.path.expanduser("~")
        elif path.startswith("~/"):
            path = os.path.expanduser(path)
        
        os.chdir(path)
        return {
            'success': True,
            'new_dir': os.getcwd(),
            'message': f'Changed to {os.getcwd()}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'cd failed: {str(e)}'
        }

# Main route to serve HTML
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket connection handling
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    # Send welcome message with current shell info
    emit('welcome', {
        'message': 'Welcome to Linux Shell WebSocket!',
        'current_dir': os.getcwd(),
        'user': os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USER', 'unknown'),
        'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('shell')
def handle_shell_command(data):
    """🚨 MAIN SHELL COMMAND HANDLER - EXECUTES ANYTHING"""
    print(f'Shell command from {request.sid}: {data}')
    
    # Handle cd command separately
    if data.strip().startswith('cd '):
        path = data.strip()[3:].strip()
        result = change_directory(path)
        emit('shell-response', {
            'type': 'cd',
            'command': data,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    else:
        # Execute any other command
        result = execute_shell_command(data)
        emit('shell-response', {
            'type': 'command',
            'command': data,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('command')
def handle_command(data):
    """Legacy command handler for compatibility"""
    if data == 'server-status':
        status = get_server_status()
        emit('server-status', status)
    elif data == 'help':
        emit('response', {
            'command': 'help',
            'result': 'Use "shell" event for Linux commands',
            'timestamp': datetime.now().isoformat()
        })
    else:
        emit('response', {
            'command': data,
            'result': f'Use shell event for Linux commands',
            'timestamp': datetime.now().isoformat()
        })

def get_server_status():
    """Get server status"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    print("🚨 LINUX SHELL WebSocket Server Started")
    print("⚠️  WARNING: Complete shell access enabled!")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)