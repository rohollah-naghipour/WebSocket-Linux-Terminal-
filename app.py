from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

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
        'message': 'Welcome to WebSocket Server!',
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
        emit('server-status', {
            'msg': 'Flask server is running',
            'status': 'online',
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'time':
        emit('response', {
            'command': 'time',
            'result': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': datetime.now().isoformat()
        })
    
    elif data == 'ping':
        emit('response', {
            'command': 'ping',
            'result': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    else:
        emit('response', {
            'command': data,
            'result': f'Command "{data}" executed',
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