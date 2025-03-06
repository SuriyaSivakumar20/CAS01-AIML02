from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import PyPDF2
import docx
import re
from collections import Counter

app = Flask(__name__)
CORS(app)  

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

stop_words = set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'
])

common_skills = [
    'javascript', 'python', 'java', 'sql', 'html', 'css', 'react', 'node', 'typescript',
    'aws', 'docker', 'git', 'agile', 'scrum', 'management', 'leadership', 'communication',
    'experience', 'years', 'software', 'engineer', 'developer', 'data', 'analysis'
]

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_text(text):
    """Preprocess text: lowercase, remove punctuation, and stopwords"""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  
    words = text.split()
    return " ".join([word for word in words if word not in stop_words])

def extract_text_from_file(file_path):
    """Extract text from PDF, TXT, or DOCX"""
    text = ""
    extension = file_path.rsplit(".", 1)[1].lower()

    if extension == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    
    elif extension == "pdf":
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + " "

    elif extension == "docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + " "

    return clean_text(text)

def calculate_similarity(job_desc, resume_text):
    """Compute similarity score between job description and resume"""
    job_words = job_desc.split()
    resume_words = resume_text.split()

    job_word_count = Counter(job_words)
    resume_word_count = Counter(resume_words)

    common_words = set(job_words) & set(resume_words)

    if not common_words:
        return 0  # No similarity

    match_score = sum(min(job_word_count[word], resume_word_count[word]) for word in common_words)
    similarity = round((match_score / max(len(job_words), 1)) * 100, 2)  
    
    return similarity

def extract_experience(text):
    """Extract years of experience from text"""
    experience_regex = re.findall(r"(\d+)\s*(years|yrs|year)", text)
    years = [int(match[0]) for match in experience_regex if match[0].isdigit()]
    return max(years) if years else 0 

@app.route("/screen", methods=["POST"])
def screen_resumes():
    if "jobDescription" not in request.form or "resumes" not in request.files:
        return jsonify({"error": "Missing job description or resumes"}), 400

    job_desc = clean_text(request.form["jobDescription"])
    files = request.files.getlist("resumes")

    if not job_desc:
        return jsonify({"error": "Job description is empty"}), 400

    candidates = []
    
    for file in files:
        if file and allowed_file(file.filename):
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)
            
            resume_text = extract_text_from_file(file_path)
            if not resume_text:
                continue

            similarity_score = calculate_similarity(job_desc, resume_text)
            experience_years = extract_experience(resume_text)
            
            matched_keywords = [word for word in common_skills if word in resume_text]

            ats_score = round(similarity_score * 0.6 + experience_years * 0.3 + len(matched_keywords) * 0.1, 2)

            candidates.append({
                "name": file.filename,
                "similarityScore": similarity_score,
                "atsScore": ats_score,
                "experienceYears": experience_years,
                "matchedKeywords": matched_keywords
            })

    if not candidates:
        return jsonify({"message": "No suitable candidates found."}), 200

    candidates.sort(key=lambda x: (-x["atsScore"], -x["similarityScore"]))
    
    return jsonify({"candidates": candidates})

if __name__ == "__main__":
    app.run(debug=True)
