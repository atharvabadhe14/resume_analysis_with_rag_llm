# HIRE - AI-Powered Talent Discovery Platform

---

## 📌 About

**HIRE** is a comprehensive AI-powered recruitment platform that automates the resume screening process using advanced semantic matching, RAG (Retrieval-Augmented Generation), and Large Language Models. It helps placement officers and HR professionals quickly discover the best candidates for job openings by analyzing resumes with unprecedented accuracy and speed.

### 🎯 Key Highlights
- **Multi-user Support**: Secure authentication system with personal databases
- **Bulk Processing**: Upload and process hundreds of resumes simultaneously
- **Semantic Search**: Goes beyond keyword matching to understand context and meaning
- **AI Analysis**: Powered by LLMs for detailed candidate evaluation
- **User-Friendly**: Modern web interface with drag-and-drop functionality
- **Scalable**: Vector database architecture for lightning-fast searches

---

## ❗ Problem Statement

College placement cells and HR departments face critical challenges:

- ⏱️ **Time-consuming**: Hours spent manually reviewing hundreds of resumes per job posting
- 🎭 **Inconsistent**: Different evaluators produce varying results for the same candidates
- 🔍 **Limited matching**: Traditional keyword searches miss qualified candidates with transferable skills
- 📈 **Scalability issues**: Manual processes fail as resume databases grow
- 🚫 **No transparency**: Candidates receive no feedback on why they weren't selected
- 🤝 **Poor candidate experience**: Long wait times and lack of communication

**HIRE** addresses all these pain points by providing:
- ⚡ **Fast processing**: Analyze 100+ resumes in minutes
- 📊 **Consistent evaluation**: AI-powered objective scoring
- 🧠 **Intelligent matching**: Semantic understanding of skills and experience
- 💡 **Detailed insights**: Match scores, strengths, and gaps for each candidate
- 📈 **Unlimited scale**: Handle thousands of resumes effortlessly

---

## ✨ Features

### Core Functionality
- 📄 **Bulk Resume Upload**: Process multiple PDF resumes simultaneously
- 👤 **Multi-user System**: Secure authentication with personal databases
- 🧠 **Semantic Search**: AI-powered matching beyond simple keywords
- 🎯 **Smart Ranking**: Candidates ranked by relevance with match scores
- 💪 **Strengths Analysis**: Identify key qualifications for each candidate
- 📉 **Gap Analysis**: Understand missing skills or experience
- 📝 **AI Summaries**: Comprehensive evaluation for each match
- 🔍 **Flexible Search**: Adjust result count and analysis depth

### Technical Features
- 🔄 **One-time Setup**: Process resumes once, search multiple times
- ⚡ **Fast Vector Search**: FAISS-powered similarity search
- 🗄️ **Efficient Storage**: SQLite for metadata, FAISS for embeddings
- 👤 **Auto Name Extraction**: Automatically identify candidate names
- 🌐 **Web Interface**: Modern, responsive design
- 🔒 **Secure**: Password hashing and session management

---

## 🛠️ Tech Stack

### AI & Machine Learning
| Technology | Purpose |
|------------|---------|
| **sentence-transformers** (all-mpnet-base-v2) | Generate semantic embeddings from text |
| **FAISS** | Fast similarity search in vector space |
| **Ollama + Gemma3:4b** | LLM for candidate analysis and insights |
| **transformers** | NLP model support |

### Document Processing
| Technology | Purpose |
|------------|---------|
| **PyMuPDF (fitz)** | Extract text from PDF documents |
| **Pytesseract** | OCR for scanned/image-based PDFs |
| **Pillow (PIL)** | Image processing for OCR |

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core programming language |
| **Flask** | Web framework |
| **SQLite** | Database for user data and resume metadata |
| **NumPy** | Numerical operations |

### Frontend
| Technology | Purpose |
|------------|---------|
| **HTML5/CSS3** | Modern web interface |
| **JavaScript** | Interactive features |
| **Responsive Design** | Mobile-friendly interface |

---

## 📦 Dataset

**Note:** This project uses AI-generated resumes for demonstration purposes.

### Dataset Structure:
```
resume/
├── resume1.pdf
├── resume2.pdf
├── resume3.pdf
└── ...
```

### Dataset Details:
- **Source**: AI-generated synthetic resumes
- **Format**: PDF files (text-based and scanned)
- **Content**: Varied candidate profiles with different skills, experience levels, and domains
- **Purpose**: Demonstration, testing, and development of the HIRE system
- **Privacy**: No real personal information included

---

## 🚀 Installation

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify: `python --version`

2. **Tesseract-OCR** (for scanned PDF support)
   - **Windows**: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - Verify: `tesseract --version`

3. **Ollama** (for AI analysis)
   - Download from [ollama.ai](https://ollama.ai/download)
   - Install and verify: `ollama --version`

### Step-by-Step Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/afrah1510/hire-ai-powered-talent-discovery.git
cd hire-ai-powered-talent-discovery
```

#### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### 3. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: First installation may take 5-10 minutes as it downloads AI models.

#### 4. Install and Configure Tesseract

**Windows Users:**
- After installation, add Tesseract to PATH or update the path in your code
- Default location: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**Linux/Mac Users:**
- Tesseract should be automatically available in PATH

#### 5. Install Ollama and Pull Model
```bash
# After installing Ollama from https://ollama.ai/download

# Pull the Gemma3:4b model
ollama pull gemma3:4b

# Verify model is installed
ollama list
```

#### 6. Prepare Resume Folder
```bash
# Create resume folder if it doesn't exist
mkdir -p resume

# Add your PDF resumes to the resume/ folder
# Or use the provided sample resumes
```

#### 7. Create Required Directories
```bash
mkdir -p databases
mkdir -p temp_uploads
```

---

## 💻 Usage

### Web Application

#### Start the Application

1. **Start Ollama Service** (in a separate terminal)
```bash
ollama serve
```

2. **Run the Flask Application**
```bash
python app.py
```

3. **Open Your Browser**
```
http://localhost:5000
```

#### Using the Web Interface

**Step 1: Create Account**
- Navigate to `http://localhost:5000`
- Click "Sign Up" tab
- Enter username, email, and password
- Click "Sign Up"

**Step 2: Upload Resumes**
- After login, click "📄 Upload Resumes"
- Enter a database name (e.g., "Software Engineers 2025")
- Drag and drop PDF files or click to browse
- Click "Process Resumes"
- Wait for processing to complete

**Step 3: Search for Candidates**
- From dashboard, click on a database
- Enter detailed job description
- Adjust settings:
  - **Top Results**: Number of candidates to retrieve (1-20)
  - **Use AI Analysis**: Enable for detailed LLM analysis
- Click "Search Candidates"
- View ranked results with match scores and analysis


---

## 📁 Project Structure

```
hire-ai-powered-talent-discovery/
│
├── resume/                      # Resume PDFs folder
│   ├── resume1.pdf
│   ├── resume2.pdf
│   └── ...
│
├── templates/                   # HTML templates
│   ├── login.html              # Login/signup page
│   ├── dashboard.html          # User dashboard
│   ├── upload.html             # Resume upload page
│   └── search.html             # Candidate search page
│
├── databases/                   # User databases (auto-generated)
│   ├── user1_db1.db
│   ├── user1_db1.index
│   └── ...
│
├── temp_uploads/                # Temporary upload storage
│
├── app.py                       # Flask web application
├── resume_embeddings.py         # Embedding generation script
├── requirements.txt             # Python dependencies
├── users.db                     # User authentication database
├── README.md                    # This file
└── .gitignore                   # Git ignore file
```

---

## 🔄 System Workflow

### Phase 1: Initial Setup (One-time per database)

```
Resume PDFs
    ↓
OCR Text Extraction (PyMuPDF + Tesseract)
    ↓
Candidate Name Extraction (NER/Pattern Matching)
    ↓
Text Embeddings Generation (sentence-transformers)
    ↓
FAISS Index Creation (768-dim vectors)
    ↓
SQLite Metadata Storage
```

**Output**: 
- `database_name.db` - Resume metadata (ID, name, text, path)
- `database_name.index` - FAISS vector index

### Phase 2: Job Matching (For each search)

```
Job Description Input
    ↓
Embedding Generation (sentence-transformers)
    ↓
Semantic Search (FAISS cosine similarity)
    ↓
Top-K Candidate Retrieval
    ↓
LLM Analysis (Ollama + Gemma3:4b) [Optional]
    ↓
Ranking & Results Display
```

**Output**:
- Ranked candidate list
- Match scores (0-100)
- Strengths and gaps
- Summary evaluation

---

## 🔮 Future Enhancements

### Planned Features
- [ ] **Advanced Filters**: Years of experience, location, GPA, certifications
- [ ] **Batch Processing**: Handle multiple job postings simultaneously
- [ ] **Export Features**: Generate Excel/PDF reports
- [ ] **Email Integration**: Automated notifications to shortlisted candidates
- [ ] **Multi-language Support**: Process resumes in multiple languages
- [ ] **Resume Quality Scoring**: Provide feedback to candidates
- [ ] **Video Interview Scheduling**: Integrated scheduling system

---


## 👥 Authors & Contributors

- **Afrah Mulla** - [GitHub](https://github.com/afrah1510)
- **Anjali Jujare** - [GitHub](https://github.com/anju2602)
- **Abhishek Thorat** - [GitHub](https://github.com/AbhishekThorat06)
- **Atharva Badhe** - [GitHub](https://github.com/atharvabadhe14)
- **Prasad Bhat** - [GitHub](https://github.com/Prasadbhat23)
- **Nilesh Nawale** - _[GitHub link to be added]_

---

## 🙏 Acknowledgments

Special thanks to the open-source community and these amazing projects:

- **[sentence-transformers](https://www.sbert.net/)** - Semantic embeddings made easy
- **[FAISS](https://github.com/facebookresearch/faiss)** - Facebook AI Research's similarity search library
- **[Ollama](https://ollama.ai/)** - Run large language models locally
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** - Fast PDF processing
- **[Tesseract OCR](https://github.com/tesseract-ocr/tesseract)** - Powerful OCR engine
- **[Flask](https://flask.palletsprojects.com/)** - Lightweight web framework
- **[Hugging Face](https://huggingface.co/)** - Transformers and model hub

---

<div align="center">
  <h3>Made with ❤️ for better campus placements and smarter hiring</h3>
  <p>Empowering recruiters with AI • Helping candidates find their perfect match</p>
  
  <br/>
  
  **[⬆ Back to Top](#hire---ai-powered-talent-discovery-platform)**
</div>