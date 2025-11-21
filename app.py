from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import json
import subprocess
import platform
import psutil
import requests
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

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

def get_server_status():
    """Get real server status using system commands"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_info = {
            'total': round(memory.total / (1024**3), 2),
            'used': round(memory.used / (1024**3), 2),
            'percent': memory.percent
        }
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_info = {
            'total': round(disk.total / (1024**3), 2),
            'used': round(disk.used / (1024**3), 2),
            'percent': disk.percent
        }
        
        # Uptime
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds / 3600
        
        # Running processes count
        processes = len(psutil.pids())
        
        return {
            'cpu_percent': cpu_percent,
            'memory': memory_info,
            'disk': disk_info,
            'uptime_hours': round(uptime_hours, 2),
            'processes': processes,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to get server status: {str(e)}'}

def get_top_processes(limit=5):
    """Get top processes by CPU usage"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by CPU usage and get top processes
        top_cpu = sorted(processes, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:limit]
        return top_cpu
    except Exception as e:
        return [{'error': f'Failed to get top processes: {str(e)}'}]

def get_network_info():
    """Get network interface information"""
    try:
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    except Exception as e:
        return {'error': f'Failed to get network info: {str(e)}'}

# Main route to serve HTML
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket connection handling
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    # Send welcome message
    emit('welcome', {
        'message': 'Welcome to Real WebSocket Server!',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('command')
def handle_command(data):
    print(f'Command received from {request.sid}: {data}')
    
    # Process different commands
    if data == 'server-status':
        status = get_server_status()
        emit('server-status', status)
    
    elif data == 'time':
        emit('response', {
            'command': 'time',
            'result': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'ping':
        ping_result = ping_host()
        emit('response', {
            'command': 'ping',
            'result': ping_result,
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'top-processes':
        top_procs = get_top_processes()
        emit('response', {
            'command': 'top-processes',
            'result': top_procs,
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'network-info':
        net_info = get_network_info()
        emit('response', {
            'command': 'network-info',
            'result': net_info,
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'disk-usage':
        disk_info = get_server_status().get('disk', {})
        emit('response', {
            'command': 'disk-usage',
            'result': disk_info,
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'memory-usage':
        memory_info = get_server_status().get('memory', {})
        emit('response', {
            'command': 'memory-usage',
            'result': memory_info,
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'help':
        help_text = """
Available Commands:
- server-status: Get detailed server status
- ping: Ping Google DNS (8.8.8.8)
- time: Get server time
- top-processes: Get top 5 processes by CPU usage
- network-info: Get network statistics
- disk-usage: Get disk usage information
- memory-usage: Get memory usage information
"""
        emit('response', {
            'command': 'help',
            'result': help_text,
            'timestamp': datetime.now().isoformat()
        })
    
    else:
        emit('response', {
            'command': data,
            'result': f'Unknown command: {data}. Type "help" for available commands.',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('message')
def handle_message(data):
    print(f'Message from {request.sid}: {data}')
    
    # Send response to the same client
    emit('response', {
        'type': 'message-response',
        'original': data,
        'response': 'Your message was received',
        'timestamp': datetime.now().isoformat()
    })
    
    # Broadcast to all clients
    emit('broadcast', {
        'from': request.sid,
        'message': data,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)