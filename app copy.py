from flask import Flask, request, render_template, send_file, session
from werkzeug.utils import secure_filename
from english_format_1 import do_english
from english_format_2 import do_english_format2
from marathi_1 import do_marathi #marathi_format1 import do_marathi
from marathi_2 import do_marathi_format2
import re, json, time
import os
import zipfile
import tempfile
import threading
from post import post_processing
from flask_socketio import SocketIO, emit
from flask_session import Session

async_mode = None
app = Flask(__name__, template_folder='templates')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
socketio = SocketIO(app, async_mode=async_mode)
app.config['UPLOAD_FOLDER'] = './PDF'
ALLOWED_EXTENSIONS = {'pdf','zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def delete_file(file_path, delay):
    # Function to delete the file after a specified delay
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)
@app.route('/set_sess', methods=['POST'])  # Specify the HTTP method as POST
def setSession():
    username = request.json.get('username')  # Access the username from the JSON request
    session['username'] = username  # Set the session variable
    return "okay"        
@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    file_path = os.path.join("PDF", filename)
    if not os.path.exists(file_path):
        return "Already downloaded or not existed"
    # Send the file as an attachment
    response = send_file(file_path, as_attachment=True)
    # Delete the file after sending
    # Delete the file after a delay of 5 seconds (adjust as needed)
    deletion_thread = threading.Thread(target=delete_file, args=(file_path, 5))
    deletion_thread.start()
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(filename , file_path, language, format):
    # Process the PDF file based on language and format
    if "MAR" in language:
        if "1" in format:
            Do_marathi = do_marathi(file_path)
            return Do_marathi.parse_doc(socketio, session.get('username'))
        if "2" in format:
            Do_marathi = do_marathi_format2(file_path)
            return Do_marathi.parse_doc(socketio, session.get('username'))
    else:
        if "1" in format:
            Do_english = do_english(file_path)
            return Do_english.parse_doc(socketio, session.get('username'))
        if "2" in format:
            Do_english = do_english_format2(file_path)
            return Do_english.parse_doc(socketio, session.get('username'))

@app.route('/upload', methods=['POST'])
def upload():
    
    if 'file' not in request.files:
        return 'No file uploaded'

    file = request.files['file']

    if file.filename == '':
        return 'Empty file name'

    if not allowed_file(file.filename):
        return 'Invalid file extension'
    try:
        filename = secure_filename(file.filename)
        filename = re.sub("PDF","pdf",filename)
        if filename.endswith('.zip'):
            file_path = os.path.join("upload", filename)
            file.save(file_path)
            os.system("rm -rf RESULT")
            os.mkdir("RESULT")
            # Extract the zip file to a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Process each PDF file in the temporary directory
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_path = os.path.join(root, file)
                            file_name = os.path.splitext(file)[0]

                            language = request.form.get('language')
                            format = request.form.get('format')
                            place = request.form.get('place')

                            # Process the PDF file
                            ALL_RESULTS = process_pdf(file_name, pdf_path, language, format)

                            json_file_path = os.path.join("RESULT", file_name + '.json')
                            with open(json_file_path, 'w') as json_file:
                                json.dump(ALL_RESULTS, json_file)

                # Create a zip file containing the JSON files
                zip_filename = "OUT_"+filename
                zip_file_path = os.path.join('TEMP', zip_filename)
                with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
                    for root, dirs, files in os.walk('RESULT'):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zip_file.write(file_path, os.path.basename(file_path))

                download_url = f"/download/TEMP/{zip_filename}"

        else:
            user_file = str(int(time.time()*100000))
            file_path = os.path.join("upload", '_'.join([user_file, filename]))
            file.save(file_path)
            # Process the single PDF file
            language = request.form.get('language')
            format = request.form.get('format')
            place = request.form.get('place')

            # Process the PDF file
            ALL_RESULTS = process_pdf(filename, file_path, language, format)

            json_filename = os.path.splitext(filename)[0] + '.json'
            json_file_path = os.path.join("PDF", json_filename)
            # with open(json_file_path, 'w', encoding='utf-8') as json_file:
            #     json.dump(ALL_RESULTS, json_file, indent='\t', ensure_ascii=False)
            xlsx_filename = os.path.splitext(filename)[0]+'.xlsx'
            xlsx_file_path = os.path.join("PDF", xlsx_filename)
            post_processing(ALL_RESULTS, xlsx_file_path)
            os.remove(file_path)

            download_url = f"/download/{xlsx_filename}"

        return render_template('success.html', download_url=download_url)
    except:
        socketio.emit('process', {'data': f"Error Encountered In Processing", 'username': session.get('username')})
        return render_template('upload.html')

@app.route('/')
@app.route('/home')
def index():
    return render_template('upload.html')

@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': "Connected !", 'count': session['receive_count']})
@socketio.event
def connect():
    emit('my_response', {'data': 'Connecting ...', 'count': 0})
@socketio.event
def disconnect():
    emit('my_response', {'data': 'Disconnected', 'count': 0})
if __name__ == '__main__':
    # from waitress import serve
    # serve(app, host="0.0.0.0", port=5000)
    app.run("0.0.0.0")