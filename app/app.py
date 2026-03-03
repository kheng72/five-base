import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configurations
UPLOAD_FOLDER = '/app/app/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS media (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            filetype TEXT NOT NULL,
            filesize BIGINT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@app.route('/index')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, filename, filetype, filesize, uploaded_at FROM media ORDER BY uploaded_at DESC')
    files = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Handle duplicates by adding timestamp
        base, extension = os.path.splitext(filename)
        filename = f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        file_size = os.path.getsize(file_path)
        file_type = filename.rsplit('.', 1)[1].lower()
        
        # Save metadata to DB
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO media (filename, filetype, filesize, uploaded_at) VALUES (%s, %s, %s, %s)',
            (filename, file_type, file_size, datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        
        flash('File successfully uploaded')
        return redirect(url_for('index'))
    else:
        flash('Allowed file types are jpg, png, mp4, mov')
        return redirect(request.url)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
else:
    # When running with Gunicorn
    init_db()
