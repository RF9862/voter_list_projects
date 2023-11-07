from flask import Flask, request, render_template, send_file, session
from werkzeug.utils import secure_filename
import re, json, time
from flask_socketio import SocketIO, emit
from flask_session import Session


async_mode = None
app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app, async_mode=async_mode)
# app.secret_key = 'Jrgkhc!123456'
# app.config['SECRET_KEY'] = 'Jrgkhc!123456'  # Set a secret key for session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
 

Session(app)  # Initialize Flask-Session
@app.route('/')
def index():
    return render_template('upload.html')
@app.route('/home')
def increase():
    username = session.get('username')
    for i in range(100):
        print(username,  i)
        time.sleep(1.5)
@app.route('/set_sess', methods=['POST'])  # Specify the HTTP method as POST
def setSession():
    username = request.json.get('username')  # Access the username from the JSON request
    session['username'] = username  # Set the session variable
    return "okay"
@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    # session['username'] = message['data']
    session['username'] = 'xxxx'
    # global username
    # username = message['data']
    emit('my_response',
         {'data': "I am Connected", 'count': session['receive_count']})
@socketio.event
def connect():
    emit('my_response', {'data': 'Connected', 'count': 0})
if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=5000)
    app.run("0.0.0.0")
