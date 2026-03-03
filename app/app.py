import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import functools

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'mov'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'media_db'),
        user=os.environ.get('DB_USER', 'media_user'),
        password=os.environ.get('DB_PASSWORD', 'strongpassword')
    )
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required.')
            return render_template('register.html')
            
        password_hash = generate_password_hash(password)
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                       (username, password_hash))
            conn.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username already exists.')
        finally:
            cur.close()
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password.')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE user_id = %s ORDER BY uploaded_at DESC',
               (session['user_id'],))
    files = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['POST'])
@login_required
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
        # Append timestamp to filename to avoid collisions
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        filesize = os.path.getsize(file_path)
        filetype = filename.rsplit('.', 1)[1].lower()
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO files (user_id, filename, filetype, filesize) VALUES (%s, %s, %s, %s)',
            (session['user_id'], unique_filename, filetype, filesize)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        flash('File uploaded successfully!')
        return redirect(url_for('dashboard'))
    
    flash('File type not allowed.')
    return redirect(url_for('dashboard'))

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
    file_record = cur.fetchone()
    cur.close()
    conn.close()
    
    if not file_record:
        abort(404)
    
    if file_record['user_id'] != session['user_id']:
        abort(403)
        
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_record['filename'])

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
    file_record = cur.fetchone()
    
    if not file_record:
        cur.close()
        conn.close()
        abort(404)
    
    if file_record['user_id'] != session['user_id']:
        cur.close()
        conn.close()
        abort(403)
        
    # Delete from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_record['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Delete from database
    cur.execute('DELETE FROM files WHERE id = %s', (file_id,))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('File deleted successfully.')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
