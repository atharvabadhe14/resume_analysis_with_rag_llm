import os
import pickle
import sqlite3
import re
from pathlib import Path
from datetime import datetime
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import io

Image.MAX_IMAGE_PIXELS = None
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ==============================
# NAME EXTRACTION FUNCTION
# ==============================
def extract_name_from_resume(resume_text):
    """Extract candidate name from resume - assumes name is on top"""
    lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
    
    for line in lines[:10]:  # Check first 10 lines
        # Skip common headers/labels
        skip_words = ['resume', 'cv', 'curriculum', 'contact', 'email', 'phone', 'address', 'linkedin', 'objective', 'summary']
        if any(word in line.lower() for word in skip_words) and len(line.split()) > 4:
            continue
        
        # All caps name (e.g., "DANA LOWELL")
        if re.match(r'^[A-Z\s]{4,30}$', line) and 2 <= len(line.split()) <= 4:
            return line.title()
        
        # Title case name (e.g., "Victoria Clark")
        if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line):
            words = line.split()
            if 2 <= len(words) <= 4 and all(len(w) > 1 for w in words[:2]):
                return ' '.join(words[:3])
        
        # "RESUME OF" pattern
        if 'resume of' in line.lower():
            name_part = re.sub(r'resume of\s*', '', line, flags=re.IGNORECASE).strip()
            if name_part:
                return name_part.title()
    
    # Fallback: first line with 2-4 words
    for line in lines[:5]:
        words = line.split()
        if 2 <= len(words) <= 4 and len(line) < 50:
            return line.title()
    
    return "Unknown"


class ResumeEmbedder:
    def __init__(self, base_path, db_path="resumes.db", index_path="resumes.index"):
        self.base_path = Path(base_path)
        self.db_path = db_path
        self.index_path = index_path
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.dimension = 768
        self.index = faiss.IndexFlatL2(self.dimension)
        self.current_id = 0
        self._init_db()
        print("✓ Model loaded and database initialized")
    
    def _init_db(self):
        """Initialize SQLite database WITH candidate_name column"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS resumes
                     (id INTEGER PRIMARY KEY,
                      file_path TEXT,
                      stream TEXT,
                      candidate_name TEXT,
                      extracted_text TEXT,
                      ocr_timestamp TEXT)''')
        conn.commit()
        conn.close()
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using OCR"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Try text extraction first (much faster)
                page_text = page.get_text()
                
                # If no text found, use OCR
                if len(page_text.strip()) < 50:
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img)
                
                text += page_text + "\n"
            
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
            return ""
    
    def process_batch(self, pdf_files, stream_name, batch_size=50):
        """Process a batch of PDFs"""
        total_files = len(pdf_files)
        print(f"\n🔹 Processing {total_files} resumes from '{stream_name}'...")
        
        for batch_start in range(0, total_files, batch_size):
            batch = pdf_files[batch_start:batch_start + batch_size]
            texts = []
            metadata = []
            
            print(f"  Batch {batch_start//batch_size + 1}: Processing {len(batch)} files...")
            
            for pdf_path in batch:
                text = self.extract_text_from_pdf(pdf_path)
                if text:
                    # Truncate to avoid token limits
                    text = text[:2000]
                    
                    # Extract candidate name
                    candidate_name = extract_name_from_resume(text)
                    
                    texts.append(text)
                    metadata.append({
                        'file_path': str(pdf_path),
                        'stream': stream_name,
                        'candidate_name': candidate_name,
                        'text': text,
                        'timestamp': datetime.now().isoformat()
                    })
            
            if not texts:
                print(f"  ⚠️ No valid text extracted from this batch")
                continue
            
            # Generate embeddings
            print(f"  Generating embeddings for {len(texts)} resumes...")
            embeddings = self.model.encode(texts, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Add to FAISS
            self.index.add(embeddings)
            
            # Store metadata in SQLite
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            for meta in metadata:
                c.execute('''INSERT INTO resumes (id, file_path, stream, candidate_name, extracted_text, ocr_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (self.current_id, meta['file_path'], meta['stream'], 
                          meta['candidate_name'], meta['text'], meta['timestamp']))
                self.current_id += 1
            conn.commit()
            conn.close()
            
            print(f"  ✓ Processed {len(texts)} resumes (Total so far: {self.current_id})")
    
    def search(self, query_text, k=5, stream_filter=None):
        """Search for similar resumes"""
        # Generate query embedding
        query_embedding = self.model.encode([query_text])
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Search in FAISS
        distances, indices = self.index.search(query_embedding, k * 2)
        
        # Retrieve metadata
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            c.execute('SELECT * FROM resumes WHERE id = ?', (int(idx),))
            row = c.fetchone()
            if row:
                if stream_filter and row[2] != stream_filter:
                    continue
                results.append({
                    'id': row[0],
                    'file_path': row[1],
                    'stream': row[2],
                    'candidate_name': row[3],
                    'text_preview': row[4][:200],
                    'distance': float(dist)
                })
                if len(results) >= k:
                    break
        
        conn.close()
        return results


# ==============================
# MAIN EXECUTION
# ==============================
if __name__ == "__main__":
    # Configuration
    RESUME_FOLDER = "resume/"  # Change this to your folder path
    STREAM_NAME = "AllResumes"  # Name for this batch
    
    print("="*60)
    print("RESUME EMBEDDING PIPELINE")
    print("="*60)
    
    # Check if folder exists
    if not os.path.exists(RESUME_FOLDER):
        print(f"❌ ERROR: Folder '{RESUME_FOLDER}' not found!")
        exit()
    
    # Find all PDFs
    pdf_files = list(Path(RESUME_FOLDER).glob("*.pdf"))
    print(f"\n📁 Found {len(pdf_files)} PDF files in '{RESUME_FOLDER}'")
    
    if len(pdf_files) == 0:
        print(f"❌ No PDF files found in '{RESUME_FOLDER}'!")
        exit()
    
    # Initialize embedder
    embedder = ResumeEmbedder(base_path=RESUME_FOLDER)
    
    # Process all PDFs
    embedder.process_batch(pdf_files, stream_name=STREAM_NAME, batch_size=50)
    
    # Save FAISS index
    faiss.write_index(embedder.index, embedder.index_path)
    print(f"\n💾 Index saved to '{embedder.index_path}'")
    
    # Show statistics
    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    
    conn = sqlite3.connect('resumes.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM resumes")
    count = c.fetchone()[0]
    print(f"📊 Total resumes in database: {count}")
    
    c.execute("SELECT id, candidate_name, stream FROM resumes LIMIT 5")
    print("\n📄 Sample resumes:")
    for row in c.fetchall():
        print(f"   ID: {row[0]:3d} | Name: {row[1]:30s} | Stream: {row[2]}")
    conn.close()
    
    if count == 0:
        print("\n❌ No resumes were successfully processed!")
        exit()
    
    # Test searches
    print("\n" + "="*60)
    print("TESTING SEARCH FUNCTIONALITY")
    print("="*60)
    
    print("\n🔍 Test Search 1: Python Developer")
    results = embedder.search("Python developer with machine learning experience", k=3)
    if results:
        for i, res in enumerate(results, 1):
            print(f"\n{i}. Candidate: {res['candidate_name']}")
            print(f"   Stream: {res['stream']}")
            print(f"   Distance: {res['distance']:.4f}")
            print(f"   Preview: {res['text_preview'][:100]}...")
    else:
        print("   No results found")
    
    print("\n🔍 Test Search 2: Java Backend Engineer")
    results = embedder.search("Java backend engineer with Spring Boot", k=3)
    if results:
        for i, res in enumerate(results, 1):
            print(f"\n{i}. Candidate: {res['candidate_name']}")
            print(f"   Stream: {res['stream']}")
            print(f"   Distance: {res['distance']:.4f}")
    else:
        print("   No results found")
    
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE!")
    print("="*60)