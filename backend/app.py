from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)  


STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
    'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'
}

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    return [stem_word(word) for word in words if word not in STOP_WORDS]

def stem_word(word):
    if word.endswith('ing'):
        return word[:-3]
    if word.endswith('ed'):
        return word[:-2]
    if word.endswith('s') and not word.endswith('ss'):
        return word[:-1]
    return word

def extract_key_skills(text):
    common_skills = [
        'javascript', 'python', 'java', 'sql', 'html', 'css', 'react', 'node', 'typescript',
        'aws', 'docker', 'git', 'agile', 'scrum', 'management', 'leadership', 'communication',
        'experience', 'years', 'software', 'engineer', 'developer', 'data', 'analysis'
    ]
    words = clean_text(text)
    return list(set(word for word in words if word in common_skills))

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

def calculate_scores(job_desc, resume_text):
    job_words = set(clean_text(job_desc))
    resume_words = clean_text(resume_text)
    word_freq = {}
    matched_keywords = []

    for word in resume_words:
        word_freq[word] = word_freq.get(word, 0) + 1

    similarity_score = 0
    for word in job_words:
        if word in word_freq:
            similarity_score += word_freq[word]
            matched_keywords.append(word)
    
    max_similarity_score = len(job_words) * 5
    similarity_score = min((similarity_score / max_similarity_score) * 100, 100)

    ats_score = 0
    keyword_match_weight = 0.6
    experience_weight = 0.3
    extra_weight = 0.1

    keyword_match_score = (len(matched_keywords) / len(job_words)) * 100
    ats_score += keyword_match_score * keyword_match_weight

    experience_regex = r'(\d+)\s*(years|yrs|year)'
    job_experience = [int(m.group(1)) for m in re.finditer(experience_regex, job_desc, re.IGNORECASE)]
    resume_experience = [int(m.group(1)) for m in re.finditer(experience_regex, resume_text, re.IGNORECASE)]
    required_years = max(job_experience) if job_experience else 0
    candidate_years = max(resume_experience) if resume_experience else 0
    experience_score = (min((candidate_years / required_years) * 100, 100) if required_years > 0 else 50)
    ats_score += experience_score * experience_weight

    resume_length_score = min((len(resume_words) / 200) * 100, 100)
    ats_score += resume_length_score * extra_weight

    return {
        "similarityScore": round(similarity_score),
        "atsScore": round(min(ats_score, 100)),
        "matchedKeywords": matched_keywords,
        "experienceYears": candidate_years
    }

def generate_feedback(job_desc, resume_text, scores):
    job_words = set(clean_text(job_desc))
    resume_words = clean_text(resume_text)
    missing_keywords = [word for word in job_words if word not in resume_words][:3]
    unique_resume_words = [word for word in resume_words if word not in job_words][:3]

    strengths, weaknesses, suggestions = [], [], []

    if scores["matchedKeywords"]:
        top_matches = " and ".join(scores["matchedKeywords"][:2])
        strengths.append(f"Your resume aligns well with the job through keywords like {top_matches}.")
    if scores["experienceYears"] > 0:
        strengths.append(f"You highlight {scores['experienceYears']} years of experience, adding credibility.")
    if unique_resume_words:
        strengths.append(f"The inclusion of '{unique_resume_words[0]}' sets your resume apart.")

    if missing_keywords:
        missing = " and ".join(missing_keywords[:2])
        weaknesses.append(f"Your resume misses critical job terms such as {missing}.")
    required_years = max([int(m.group(1)) for m in re.finditer(r'(\d+)\s*(years|yrs|year)', job_desc, re.IGNORECASE)], default=0)
    if required_years > 0 and scores["experienceYears"] < required_years:
        weaknesses.append(f"With {scores['experienceYears']} years, you fall {required_years - scores['experienceYears']} year(s) short.")
    elif scores["experienceYears"] == 0 and required_years > 0:
        weaknesses.append(f"No experience years specified, while the job expects {required_years} years.")
    if len(resume_words) < 75:
        weaknesses.append(f"The resume is brief ({len(resume_words)} words), potentially lacking detail.")

    if missing_keywords:
        suggestions.append(f"Add '{missing_keywords[0]}' to your resume to better match the job.")
    if scores["experienceYears"] > 0:
        suggestions.append(f"Elaborate on your {scores['experienceYears']}-year experience with examples.")
    elif scores["experienceYears"] == 0:
        suggestions.append("Include specific years or project details to quantify your experience.")
    if unique_resume_words:
        suggestions.append(f"Emphasize how '{unique_resume_words[0]}' relates to the job.")
    elif len(resume_words) < 100:
        suggestions.append(f"Expand your resume (currently {len(resume_words)} words) with more details.")

    return {
        "strengths": strengths or [f"Your resume has some content ({len(resume_words)} words), but could emphasize skills more."],
        "weaknesses": weaknesses or [f"No major gaps, but it could highlight terms like '{list(job_words)[0] or 'relevance'}'."],
        "suggestions": suggestions or [f"Consider adding details to align with '{list(job_words)[0] or 'job needs'}'."]
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