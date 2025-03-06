from flask import Flask, request, jsonify
import os
import spacy
import fitz  
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load AI Model
nlp = spacy.load("en_core_web_sm")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text("text") + " "
    return text.strip()

def calculate_similarity(job_desc, resume_text):
    job_embedding = embed_model.encode(job_desc, convert_to_tensor=True)
    resume_embedding = embed_model.encode(resume_text, convert_to_tensor=True)
    score = util.pytorch_cos_sim(job_embedding, resume_embedding).item() * 100
    return round(score, 2)

@app.route("/screen_resumes", methods=["POST"])
def screen_resumes():
    job_desc = request.form.get("job_description")
    if not job_desc:
        return jsonify({"error": "Job description is required"}), 400

    uploaded_files = request.files.getlist("resumes")
    if not uploaded_files:
        return jsonify({"error": "No resumes uploaded"}), 400

    candidates = []
    for file in uploaded_files:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        if file.filename.endswith(".pdf"):
            resume_text = extract_text_from_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                resume_text = f.read()

        score = calculate_similarity(job_desc, resume_text)
        candidates.append({"name": file.filename, "score": score})

    candidates.sort(key=lambda x: x["score"], reverse=True)  

    return jsonify({"candidates": candidates})

if __name__ == "__main__":
    app.run(debug=True)
