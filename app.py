from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to a random secret key
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload

# Global model cache
embed_model = None

# ==============================
# USER AUTHENTICATION DATABASE
# ==============================
def init_user_db():
    """Initialize user authentication database"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  email TEXT,
                  created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_databases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  db_name TEXT,
                  db_path TEXT,
                  index_path TEXT,
                  created_at TEXT,
                  resume_count INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, email):
    """Create a new user"""
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        password_hash = hash_password(password)
        c.execute('''INSERT INTO users (username, password_hash, email, created_at)
                    VALUES (?, ?, ?, ?)''',
                 (username, password_hash, email, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(username, password):
    """Verify user credentials"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    password_hash = hash_password(password)
    c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?',
             (username, password_hash))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def get_user_databases(user_id):
    """Get all databases for a user"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT id, db_name, db_path, index_path, created_at, resume_count
                FROM user_databases WHERE user_id = ?
                ORDER BY created_at DESC''', (user_id,))
    databases = c.fetchall()
    conn.close()
    return databases

def save_user_database(user_id, db_name, db_path, index_path, resume_count):
    """Save database info for user"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO user_databases 
                (user_id, db_name, db_path, index_path, created_at, resume_count)
                VALUES (?, ?, ?, ?, ?, ?)''',
             (user_id, db_name, db_path, index_path, 
              datetime.now().isoformat(), resume_count))
    conn.commit()
    conn.close()

# ==============================
# RESUME PROCESSING FUNCTIONS
# ==============================
def process_resumes_from_folder(folder_path, db_name):
    """Process resumes from uploaded folder"""
    from resume_embeddings import ResumeEmbedder
    
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    if len(pdf_files) == 0:
        return None, None, 0
    
    # Create unique paths for this database
    db_path = f"databases/{db_name}.db"
    index_path = f"databases/{db_name}.index"
    
    os.makedirs("databases", exist_ok=True)
    
    # Initialize embedder
    embedder = ResumeEmbedder(base_path=folder_path, db_path=db_path, index_path=index_path)
    
    # Process in batches
    batch_size = 50
    for i in range(0, len(pdf_files), batch_size):
        batch = pdf_files[i:i + batch_size]
        embedder.process_batch(batch, stream_name="AllResumes", batch_size=batch_size)
    
    # Save index
    faiss.write_index(embedder.index, embedder.index_path)
    
    return db_path, index_path, embedder.current_id

# ==============================
# RAG SEARCH FUNCTIONS
# ==============================
def load_database(db_path, index_path):
    """Load FAISS index and resume database"""
    try:
        index = faiss.read_index(index_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, file_path, candidate_name, extracted_text FROM resumes")
        rows = cursor.fetchall()
        conn.close()
        
        resume_dict = {}
        for r in rows:
            resume_dict[r[0]] = {
                "id": r[0],
                "file_path": r[1],
                "candidate_name": r[2],
                "resume_text": r[3] or ""
            }
        
        return index, resume_dict
    except Exception as e:
        print(f"Error loading database: {e}")
        return None, None

def search_candidates(job_description, index, resume_dict, model, top_k=5):
    """Search for matching candidates"""
    job_embedding = model.encode([job_description])
    distances, indices = index.search(job_embedding, top_k)
    
    retrieved = []
    for idx in indices[0]:
        if idx in resume_dict:
            candidate = resume_dict[idx].copy()
            retrieved.append(candidate)
    
    return retrieved

def analyze_with_llm(job_description, candidate, ollama_url="http://localhost:11434/api/generate", model_name="gemma3:4b"):
    """Analyze candidate using LLM"""
    prompt = f"""
You are an AI recruitment assistant.

Job Description:
{job_description}

Candidate Name: {candidate['candidate_name']}

Candidate Resume:
{candidate['resume_text']}

Analyze the resume and respond ONLY in valid JSON:

{{
  "resume_id": {candidate['id']},
  "candidate_name": "{candidate['candidate_name']}",
  "match_score": 0,
  "strengths": [],
  "gaps": [],
  "summary": ""
}}
"""
    
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload, timeout=600)
        response.raise_for_status()
        
        output = response.json()["response"]
        start = output.find("{")
        end = output.rfind("}") + 1
        
        return json.loads(output[start:end])
    except Exception as e:
        return {
            "resume_id": candidate['id'],
            "candidate_name": candidate['candidate_name'],
            "match_score": 0,
            "strengths": [],
            "gaps": [],
            "summary": f"Error analyzing: {str(e)}"
        }

# ==============================
# FLASK ROUTES
# ==============================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user_id = verify_user(username, password)
    if user_id:
        session['user_id'] = user_id
        session['username'] = username
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('index'))

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    
    if password != password2:
        flash('Passwords do not match!', 'error')
        return redirect(url_for('index'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters!', 'error')
        return redirect(url_for('index'))
    
    success, message = create_user(username, password, email)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_dbs = get_user_databases(session['user_id'])
    return render_template('dashboard.html', databases=user_dbs, username=session['username'])

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        db_name = request.form.get('db_name', '').strip()
        
        if not db_name:
            flash('Please provide a database name!', 'error')
            return redirect(url_for('upload'))
        
        # Sanitize database name
        db_name = secure_filename(db_name)
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            flash('No files selected!', 'error')
            return redirect(url_for('upload'))
        
        # Create temp folder
        temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], 
                                   f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(temp_folder, exist_ok=True)
        
        # Save uploaded files
        pdf_count = 0
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                file.save(os.path.join(temp_folder, filename))
                pdf_count += 1
        
        if pdf_count == 0:
            flash('No valid PDF files found!', 'error')
            shutil.rmtree(temp_folder)
            return redirect(url_for('upload'))
        
        # Process resumes
        try:
            db_path, index_path, resume_count = process_resumes_from_folder(temp_folder, db_name)
            
            if db_path and index_path:
                save_user_database(session['user_id'], db_name, db_path, index_path, resume_count)
                flash(f'Successfully processed {resume_count} resumes!', 'success')
                shutil.rmtree(temp_folder)
                return redirect(url_for('dashboard'))
            else:
                flash('Error processing resumes', 'error')
                shutil.rmtree(temp_folder)
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
        
        return redirect(url_for('upload'))
    
    return render_template('upload.html', username=session['username'])

@app.route('/search/<int:db_id>')
def search_page(db_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get database info
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT db_name, db_path, index_path, resume_count 
                FROM user_databases 
                WHERE id = ? AND user_id = ?''', (db_id, session['user_id']))
    db_info = c.fetchone()
    conn.close()
    
    if not db_info:
        flash('Database not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('search.html', 
                         db_id=db_id,
                         db_name=db_info[0],
                         resume_count=db_info[3],
                         username=session['username'])

@app.route('/api/search', methods=['POST'])
def api_search():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    global embed_model
    
    data = request.json
    db_id = data.get('db_id')
    job_description = data.get('job_description', '').strip()
    top_k = int(data.get('top_k', 5))
    use_llm = data.get('use_llm', False)
    
    if not job_description:
        return jsonify({'error': 'Job description required'}), 400
    
    # Get database paths
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT db_path, index_path 
                FROM user_databases 
                WHERE id = ? AND user_id = ?''', (db_id, session['user_id']))
    db_info = c.fetchone()
    conn.close()
    
    if not db_info:
        return jsonify({'error': 'Database not found'}), 404
    
    db_path, index_path = db_info
    
    # Load model if needed
    if embed_model is None:
        embed_model = SentenceTransformer('all-mpnet-base-v2')
    
    # Load database
    index, resume_dict = load_database(db_path, index_path)
    
    if index is None or resume_dict is None:
        return jsonify({'error': 'Failed to load database'}), 500
    
    # Search
    candidates = search_candidates(job_description, index, resume_dict, embed_model, top_k)
    
    if not candidates:
        return jsonify({'candidates': []})
    
    # Analyze with LLM if requested
    if use_llm:
        results = []
        for candidate in candidates:
            result = analyze_with_llm(job_description, candidate)
            results.append(result)
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        return jsonify({'candidates': results, 'analyzed': True})
    else:
        # Return basic candidate info
        simple_results = [
            {
                'candidate_name': c['candidate_name'],
                'file_path': c['file_path'],
                'resume_preview': c['resume_text'][:300] + '...'
            }
            for c in candidates
        ]
        return jsonify({'candidates': simple_results, 'analyzed': False})

if __name__ == '__main__':
    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('databases', exist_ok=True)
    init_user_db()
    app.run(debug=True, host='0.0.0.0', port=5000)