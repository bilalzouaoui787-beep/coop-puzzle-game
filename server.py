import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!_coop_game_2026'
socketio = SocketIO(app, cors_allowed_origins="*")

# تخزين حالات الغرف والألغاز
rooms_state = {}

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('create_room')
def handle_create_room(data):
    room_code = generate_room_code()
    while room_code in rooms_state:
        room_code = generate_room_code()
    
    join_room(room_code)
    
    rooms_state[room_code] = {
        'players': [data.get('username', 'Player 1')],
        'stage': 1,
        'grid_p1': [0, 1, 0, 1, 1, 0, 1, 0, 0],
        'grid_p2': [1, 0, 1, 0, 0, 1, 0, 1, 1],
        'solved': False
    }
    
    emit('room_created', {'room': room_code, 'player_id': 1})

@socketio.on('join_room')
def handle_join_room(data):
    room_code = data.get('room').upper()
    if room_code in rooms_state:
        if len(rooms_state[room_code]['players']) < 2:
            join_room(room_code)
            rooms_state[room_code]['players'].append(data.get('username', 'Player 2'))
            emit('room_joined', {'room': room_code, 'player_id': 2}, room=room_code)
            socketio.emit('update_game_state', rooms_state[room_code], room=room_code)
        else:
            emit('error_message', {'message': 'الغرفة ممتلئة بالفعل!'})
    else:
        emit('error_message', {'message': 'رمز الغرفة غير موجود!'})

@socketio.on('player_action')
def handle_player_action(data):
    room_code = data.get('room')
    if room_code in rooms_state:
        action_type = data.get('type')
        if action_type == 'toggle_grid':
            index = data.get('index')
            player_id = data.get('player_id')
            grid_key = f'grid_p{player_id}'
            
            if 0 <= index < len(rooms_state[room_code][grid_key]):
                rooms_state[room_code][grid_key][index] = 1 - rooms_state[room_code][grid_key][index]
            
            p1 = rooms_state[room_code]['grid_p1']
            p2 = rooms_state[room_code]['grid_p2']
            if sum(p1) == 5 and sum(p2) == 4:
                rooms_state[room_code]['solved'] = True
                
            socketio.emit('update_game_state', rooms_state[room_code], room=room_code)

@socketio.on('send_chat')
def handle_chat(data):
    room_code = data.get('room')
    message = data.get('message')
    username = data.get('username')
    emit('receive_chat', {'username': username, 'message': message}, room=room_code)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
