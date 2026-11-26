import os
import tempfile
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from docx import Document
import fitz # PyMuPDF

app = Flask(__name__)

# --- SECURITY PACK ---
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024 # 20MB limit
ALLOWED_EXTENSIONS = {'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_docx(path):
    doc = Document(path)
    text = "\n".join([p.text for p in doc.paragraphs])
    words = len(text.split())
    pages_est = max(1, words // 500)
    return {"type": "DOCX", "words": words, "pages_est": pages_est, "chars": len(text)}

def check_pdf(path):
    doc = fitz.open(path)
    pages = len(doc)
    text = ""
    for page in doc:
        text += page.get_text()
    words = len(text.split())
    return {"type": "PDF", "words": words, "pages": pages, "chars": len(text)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    if 'file' not in request.files:
        return jsonify({"error": "No file selected"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only .docx and .pdf allowed"}), 400

    filename = secure_filename(file.filename)
    # Use temp file, auto-delete after check
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        ext = filename.rsplit('.', 1)[1].lower()
        if ext == 'docx':
            result = check_docx(tmp_path)
        else:
            result = check_pdf(tmp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"File no fit open: {str(e)}"}), 400
    finally:
        # Always delete file after check
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too big! Max na 20MB"}), 413

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)