from flask.ext.socketio import SocketIO
from flask.ext.login import current_user
from flask.ext.socketio import join_room, leave_room, emit
from woe import socketio

@socketio.on('join', namespace='/topic')
def handle_join_topic(data):
    join_room("topic"+str(data["topic"]))
    emit('new post', "test", broadcast=True)
    print str(data)

@socketio.on('message', namespace='/test')
def handle_message(message):
    print('received message: ' + str(message))

@socketio.on('connect', namespace='/test')
def handle_connect():
    print "ok"