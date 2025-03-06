from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from werkzeug.utils import secure_filename
import spacy

app = Flask(__name__)
CORS(app) 


nlp = spacy.load("en_core_web_lg")


COMMON_SKILLS = {
    'javascript', 'python', 'java', 'sql', 'html', 'css', 'react', 'node', 'typescript',
    'aws', 'docker', 'git', 'agile', 'scrum', 'management', 'leadership', 'communication',
    'experience', 'years', 'software', 'engineer', 'developer', 'data', 'analysis'
}

def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + " "
        return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def extract_key_skills(text):
    doc = nlp(text.lower())
    skills = set()
    for token in doc:
        if token.text in COMMON_SKILLS and not token.is_stop:
            skills.add(token.text)
    for ent in doc.ents:
        if ent.label_ in ["SKILL", "ORG", "DATE"] and ent.text.lower() in COMMON_SKILLS:
            skills.add(ent.text.lower())
    return list(skills)

def calculate_scores(job_desc, resume_text):
    job_doc = nlp(job_desc)
    resume_doc = nlp(resume_text)

  
    similarity_score = min(round(job_doc.similarity(resume_doc) * 100), 100)

    
    job_skills = set(extract_key_skills(job_desc))
    resume_skills = set(extract_key_skills(resume_text))
    matched_keywords = job_skills.intersection(resume_skills)

    ats_score = 0
    keyword_match_weight = 0.6
    experience_weight = 0.3
    extra_weight = 0.1

    keyword_match_score = (len(matched_keywords) / len(job_skills)) * 100 if job_skills else 0
    ats_score += keyword_match_score * keyword_match_weight

    experience_regex = r'(\d+)\s*(years|yrs|year)'
    job_experience = [int(m.group(1)) for m in re.finditer(experience_regex, job_desc, re.IGNORECASE)]
    resume_experience = [int(m.group(1)) for m in re.finditer(experience_regex, resume_text, re.IGNORECASE)]
    required_years = max(job_experience) if job_experience else 0
    candidate_years = max(resume_experience) if resume_experience else 0
    experience_score = (min((candidate_years / required_years) * 100, 100) if required_years > 0 else 50)
    ats_score += experience_score * experience_weight

    resume_length_score = min((len(resume_text.split()) / 200) * 100, 100)
    ats_score += resume_length_score * extra_weight

    return {
        "similarityScore": similarity_score,
        "atsScore": round(min(ats_score, 100)),
        "matchedKeywords": list(matched_keywords),
        "experienceYears": candidate_years
    }

def generate_feedback(job_desc, resume_text, scores):
    job_doc = nlp(job_desc.lower())
    resume_doc = nlp(resume_text.lower())
    job_skills = set(extract_key_skills(job_desc))
    resume_skills = set(extract_key_skills(resume_text))
    missing_keywords = list(job_skills - resume_skills)[:3]
    unique_resume_skills = list(resume_skills - job_skills)[:3]

    strengths, weaknesses, suggestions = [], [], []

    if scores["matchedKeywords"]:
        top_matches = " and ".join(scores["matchedKeywords"][:2])
        strengths.append(f"Your resume aligns well with the job through skills like {top_matches}.")
    if scores["experienceYears"] > 0:
        strengths.append(f"You showcase {scores['experienceYears']} years of experience, adding credibility.")
    if unique_resume_skills:
        strengths.append(f"Unique skill '{unique_resume_skills[0]}' sets your resume apart.")

    if missing_keywords:
        missing = " and ".join(missing_keywords[:2])
        weaknesses.append(f"Your resume misses key job skills like {missing}.")
    required_years = max([int(m.group(1)) for m in re.finditer(r'(\d+)\s*(years|yrs|year)', job_desc, re.IGNORECASE)], default=0)
    if required_years > 0 and scores["experienceYears"] < required_years:
        weaknesses.append(f"With {scores['experienceYears']} years, you’re {required_years - scores['experienceYears']} year(s) short.")
    elif scores["experienceYears"] == 0 and required_years > 0:
        weaknesses.append(f"No experience years listed; job expects {required_years} years.")
    if len(resume_text.split()) < 75:
        weaknesses.append(f"Your resume is brief ({len(resume_text.split())} words), possibly lacking detail.")

    if missing_keywords:
        suggestions.append(f"Add '{missing_keywords[0]}' to better match the job.")
    if scores["experienceYears"] > 0:
        suggestions.append(f"Highlight your {scores['experienceYears']}-year experience with examples.")
    elif scores["experienceYears"] == 0:
        suggestions.append("Quantify your experience with years or projects.")
    if unique_resume_skills:
        suggestions.append(f"Emphasize how '{unique_resume_skills[0]}' fits the role.")
    elif len(resume_text.split()) < 100:
        suggestions.append(f"Expand your resume (currently {len(resume_text.split())} words) with more details.")

    return {
        "strengths": strengths or ["Your resume has content but could highlight skills more clearly."],
        "weaknesses": weaknesses or [f"Minor gaps; consider adding skills like '{list(job_skills)[0] if job_skills else 'relevance'}'."],
        "suggestions": suggestions or ["Add more specific details to align with the job."]
    }

@app.route("/screen", methods=["POST"])
def screen_resumes():
    if "jobDescription" not in request.form:
        return jsonify({"error": "Job description is required"}), 400
    if "resumes" not in request.files:
        return jsonify({"error": "No resumes uploaded"}), 400

    job_desc = request.form["jobDescription"]
    files = request.files.getlist("resumes")
    candidates = []

    for file in files:
        filename = secure_filename(file.filename)
        if filename.endswith(".txt"):
            text = file.read().decode("utf-8")
        elif filename.endswith(".pdf"):
            text = extract_text_from_pdf(file)
        else:
            continue

        if text and text.strip():
            scores = calculate_scores(job_desc, text)
            feedback = generate_feedback(job_desc, text, scores)
            candidates.append({
                "name": filename,
                "similarityScore": scores["similarityScore"],
                "atsScore": scores["atsScore"],
                "matchedKeywords": scores["matchedKeywords"],
                "experienceYears": scores["experienceYears"],
                "feedback": feedback
            })

    if not candidates:
        return jsonify({"error": "No readable resumes found"}), 400

    candidates.sort(key=lambda x: (x["atsScore"], x["similarityScore"]), reverse=True)
    return jsonify({"candidates": candidates})

if __name__ == "__main__":
    app.run(debug=True, port=5000)