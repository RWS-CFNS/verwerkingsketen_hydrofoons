from flask import Flask, request
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.normpath(os.path.join(SCRIPT_DIR, "../../recordings"))

print(f"Saving to folder: {FOLDER}")

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(os.path.join(FOLDER, file.filename))
    return 'OK'

app.run(host='0.0.0.0')
