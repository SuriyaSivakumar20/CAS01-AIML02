from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import re
from werkzeug.utils import secure_filename
import spacy
import os
from textblob import TextBlob
from sklearn.linear_model import LogisticRegression
import numpy as np

app = Flask(__name__)
CORS(app)

nlp = spacy.load("en_core_web_lg")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Refined COMMON_SKILLS to focus on technical, actionable skills
COMMON_SKILLS = {
    'javascript', 'python', 'java', 'sql', 'html', 'css', 'react', 'node', 'typescript',
    'aws', 'docker', 'git', 'agile', 'scrum', 'management', 'leadership', 'communication',
    'data', 'analysis'  # Removed 'engineer', 'software', 'experience', 'years'
}

SKILL_RESOURCES = {
    "python": "Learn Python on Codecademy (https://www.codecademy.com/learn/learn-python-3)",
    "aws": "AWS Certification on Coursera (https://www.coursera.org/professional-certificates/aws-cloud-technology-consultant)",
    "sql": "SQL Basics on Khan Academy (https://www.khanacademy.org/computing/computer-programming/sql)",
    "javascript": "JavaScript Tutorial on freeCodeCamp (https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/)",
    "java": "Java Programming on Udemy (https://www.udemy.com/course/java-the-complete-java-developer-course/)",
    "html": "HTML Crash Course on YouTube by Traversy Media (https://www.youtube.com/watch?v=UB1O30fR-EE)",
    "css": "CSS Flexbox Tutorial on Scrimba (https://scrimba.com/learn/flexbox)",
    "react": "React Official Tutorial (https://reactjs.org/tutorial/tutorial.html)",
    "node": "Node.js Basics on Pluralsight (https://www.pluralsight.com/courses/node-js-getting-started)",
    "typescript": "TypeScript for Beginners on Udemy (https://www.udemy.com/course/learn-typescript/)",
    "docker": "Docker Mastery on Udemy (https://www.udemy.com/course/docker-mastery/)",
    "git": "Git & GitHub Crash Course on YouTube by freeCodeCamp (https://www.youtube.com/watch?v=RGOj5yH7evk)",
    "agile": "Agile Fundamentals on LinkedIn Learning (https://www.linkedin.com/learning/agile-foundations)",
    "scrum": "Scrum Certification Prep on Coursera (https://www.coursera.org/learn/scrum-certification)",
    "management": "Project Management Basics on PMI (https://www.pmi.org/learning/training-development)",
    "leadership": "Leadership Skills on edX (https://www.edx.org/course/leadership-and-influence)",
    "communication": "Effective Communication on Coursera (https://www.coursera.org/learn/communication-skills)",
    "data": "Data Analysis with Python on Coursera (https://www.coursera.org/learn/data-analysis-python)",
    "analysis": "Intro to Data Analysis on Udacity (https://www.udacity.com/course/intro-to-data-analysis--nd002)"
}

X_train = np.array([
    [85, 5, 12], [60, 2, 5], [90, 7, 15], [45, 1, 3],
    [75, 4, 8], [30, 0, 2], [80, 3, 10], [55, 2, 4],
    [95, 6, 14], [70, 3, 7], [40, 1, 3], [65, 2, 6]
])
y_train = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0])
job_fit_model = LogisticRegression().fit(X_train, y_train)

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
            return text.strip()
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return ""

def extract_text_from_txt(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading TXT: {e}")
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

def summarize_resume(resume_text):
    doc = nlp(resume_text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    skill_sentences = []
    for sent in sentences:
        skills = extract_key_skills(sent)
        score = len(skills) + (len(sent.split()) / 50)
        skill_sentences.append((sent, score))
    top_sentences = sorted(skill_sentences, key=lambda x: x[1], reverse=True)[:2]
    return " ".join([sent for sent, score in top_sentences])

def analyze_sentiment(resume_text):
    blob = TextBlob(resume_text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "Confident/Positive"
    elif polarity < -0.1:
        return "Passive/Negative"
    else:
        return "Neutral"

def predict_job_fit(similarity_score, experience_years, matched_keywords_count):
    features = np.array([[similarity_score, experience_years, matched_keywords_count]])
    probability = job_fit_model.predict_proba(features)[0][1]
    return round(probability * 100)

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
    missing_keywords = [skill for skill in (job_skills - resume_skills) if skill in SKILL_RESOURCES][:3]  # Only skills with resources
    unique_resume_skills = list(resume_skills - job_skills)[:3]

    strengths, weaknesses, suggestions, skill_gaps = [], [], [], []

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

    for skill in missing_keywords:
        resource = SKILL_RESOURCES[skill]  # Guaranteed to exist due to filter
        skill_gaps.append(f"Learn '{skill}': {resource}")

    return {
        "strengths": strengths or ["Your resume has content but could highlight skills more clearly."],
        "weaknesses": weaknesses or [f"Minor gaps; consider adding specific technical skills."],
        "suggestions": suggestions or ["Add more specific details to align with the job."],
        "skillGaps": skill_gaps or ["No major skill gaps identified."]
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
        if not filename.endswith((".txt", ".pdf")):
            continue

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if filename.endswith(".txt"):
            text = extract_text_from_txt(filepath)
        elif filename.endswith(".pdf"):
            text = extract_text_from_pdf(filepath)

        if text and text.strip():
            scores = calculate_scores(job_desc, text)
            feedback = generate_feedback(job_desc, text, scores)
            summary = summarize_resume(text)
            tone = analyze_sentiment(text)
            job_fit = predict_job_fit(scores["similarityScore"], scores["experienceYears"], len(scores["matchedKeywords"]))
            candidates.append({
                "name": filename,
                "similarityScore": scores["similarityScore"],
                "atsScore": scores["atsScore"],
                "matchedKeywords": scores["matchedKeywords"],
                "experienceYears": scores["experienceYears"],
                "feedback": feedback,
                "summary": summary,
                "tone": tone,
                "jobFit": job_fit
            })

    if not candidates:
        return jsonify({"error": "No readable resumes found"}), 400

    candidates.sort(key=lambda x: (x["atsScore"], x["similarityScore"]), reverse=True)
    return jsonify({"candidates": candidates})

if __name__ == "__main__":
    app.run(debug=True, port=5000)