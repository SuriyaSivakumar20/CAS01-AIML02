const jobDescription = document.getElementById("jobDescription");
const resumeFiles = document.getElementById("resumeFiles");
const fileList = document.getElementById("fileList");
const candidateList = document.getElementById("candidateList");
const loading = document.getElementById("loading");
const keySkillsDiv = document.getElementById("keySkills");
const feedbackBox = document.getElementById("feedbackBox");
const resumeCount = document.getElementById("resumeCount");
const fileUpload = document.querySelector(".file-upload");

jobDescription.addEventListener("input", function () {
    document.getElementById("charCount").textContent = `${this.value.length}/1000 characters`;
    updateKeySkills(this.value);
});

resumeFiles.addEventListener("change", function () {
    fileList.innerHTML = "";
    const files = Array.from(this.files);
    resumeCount.textContent = `${files.length} resumes uploaded`;
    fileUpload.classList.add("uploaded"); 

    
    for (let i = 0; i < files.length; i += 4) {
        const row = document.createElement("div");
        row.className = "file-row";
        const rowFiles = files.slice(i, i + 4);
        rowFiles.forEach(file => {
            const fileItem = document.createElement("div");
            fileItem.className = "file-item";
            fileItem.textContent = `📄 ${file.name}`;
            row.appendChild(fileItem);
        });
        fileList.appendChild(row);
    }
});

const stopWords = new Set([
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he', 'in', 'is', 'it',
    'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were', 'will', 'with'
]);

function cleanText(text) {
    return text.toLowerCase()
        .replace(/[^\w\s]/g, '')
        .replace(/\s+/g, ' ')
        .trim()
        .split(' ')
        .filter(word => !stopWords.has(word))
        .map(stemWord);
}

function stemWord(word) {
    if (word.endsWith('ing')) return word.slice(0, -3);
    if (word.endsWith('ed')) return word.slice(0, -2);
    if (word.endsWith('s') && !word.endsWith('ss')) return word.slice(0, -1);
    return word;
}

function extractKeySkills(text) {
    const commonSkills = [
        'javascript', 'python', 'java', 'sql', 'html', 'css', 'react', 'node', 'typescript',
        'aws', 'docker', 'git', 'agile', 'scrum', 'management', 'leadership', 'communication',
        'experience', 'years', 'software', 'engineer', 'developer', 'data', 'analysis'
    ].map(stemWord);
    const words = cleanText(text);
    return [...new Set(words.filter(word => commonSkills.includes(word)))];
}

function updateKeySkills(text) {
    const skills = extractKeySkills(text);
    keySkillsDiv.innerHTML = skills.length
        ? `Key Skills: ${skills.map(skill => `<span>${skill}</span>`).join('')}`
        : "";
}

async function readFileContent(file) {
    if (file.type === "text/plain") {
        return file.text();
    } else if (file.type === "application/pdf") {
        return extractTextFromPDF(file);
    } else {
        console.warn(`Unsupported file type: ${file.name}`);
        return null;
    }
}

async function extractTextFromPDF(file) {
    const reader = new FileReader();
    return new Promise((resolve, reject) => {
        reader.onload = async function () {
            try {
                const pdfData = new Uint8Array(reader.result);
                const pdf = await pdfjsLib.getDocument({ data: pdfData }).promise;
                let text = "";
                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const content = await page.getTextContent();
                    text += content.items.map(item => item.str).join(" ") + " ";
                }
                resolve(text);
            } catch (error) {
                reject(`Error parsing PDF: ${error.message}`);
            }
        };
        reader.onerror = () => reject("Error reading PDF file.");
        reader.readAsArrayBuffer(file);
    });
}

function generateFeedback(jobDesc, resumeText, scores) {
    const jobWords = new Set(cleanText(jobDesc));
    const resumeWords = cleanText(resumeText);
    const missingKeywords = [...jobWords].filter(word => !resumeWords.includes(word)).slice(0, 3);
    const uniqueResumeWords = resumeWords.filter(word => !jobWords.has(word)).slice(0, 3);

    const strengths = [];
    const weaknesses = [];
    const suggestions = [];

    if (scores.matchedKeywords.length > 0) {
        const topMatches = scores.matchedKeywords.slice(0, 2).join(" and ");
        strengths.push(`Your resume aligns well with the job through keywords like ${topMatches}.`);
    }
    if (scores.experienceYears > 0) {
        strengths.push(`You highlight ${scores.experienceYears} years of experience, adding credibility to your profile.`);
    }
    if (uniqueResumeWords.length > 0) {
        const uniqueWord = uniqueResumeWords[0];
        strengths.push(`The inclusion of "${uniqueWord}" sets your resume apart with a distinctive skill or term.`);
    }

    if (missingKeywords.length > 0) {
        const missing = missingKeywords.slice(0, 2).join(" and ");
        weaknesses.push(`Your resume misses critical job terms such as ${missing}, reducing its relevance.`);
    }
    const requiredYears = Math.max(...(jobDesc.match(/(\d+)\s*(years|yrs|year)/gi) || []).map(match => parseInt(match) || 0)) || 0;
    if (requiredYears > 0 && scores.experienceYears < requiredYears) {
        weaknesses.push(`With ${scores.experienceYears} years, you fall ${requiredYears - scores.experienceYears} year(s) short of the job's experience expectation.`);
    } else if (scores.experienceYears === 0 && requiredYears > 0) {
        weaknesses.push(`No experience years are specified, while the job expects ${requiredYears} years.`);
    }
    if (resumeWords.length < 75) {
        weaknesses.push(`The resume is brief (${resumeWords.length} words), potentially lacking detail to fully showcase your qualifications.`);
    }

    if (missingKeywords.length > 0) {
        suggestions.push(`Add "${missingKeywords[0]}" to your resume to better match the job description.`);
    }
    if (scores.experienceYears > 0) {
        suggestions.push(`Elaborate on your ${scores.experienceYears}-year experience with concrete examples or achievements.`);
    } else if (scores.experienceYears === 0) {
        suggestions.push(`Include specific years or project details to quantify your experience.`);
    }
    if (uniqueResumeWords.length > 0) {
        suggestions.push(`Emphasize how "${uniqueResumeWords[0]}" relates to the job to maximize its impact.`);
    } else if (resumeWords.length < 100) {
        suggestions.push(`Expand your resume (currently ${resumeWords.length} words) with more details about your skills or roles.`);
    }

    return {
        strengths: strengths.length ? strengths : [`Your resume has some content (${resumeWords.length} words), but could emphasize specific skills more.`],
        weaknesses: weaknesses.length ? weaknesses : [`No major gaps, but it could better highlight terms like "${[...jobWords][0] || 'relevance'}".`],
        suggestions: suggestions.length ? suggestions : [`Consider adding details to align with "${[...jobWords][0] || 'job needs'}".`]
    };
}

function calculateScores(jobDesc, resumeText) {
    const jobWords = new Set(cleanText(jobDesc));
    const resumeWords = cleanText(resumeText);
    const wordFreq = {};
    const matchedKeywords = [];

    resumeWords.forEach(word => {
        wordFreq[word] = (wordFreq[word] || 0) + 1;
    });

    let similarityScore = 0;
    jobWords.forEach(word => {
        if (wordFreq[word]) {
            similarityScore += wordFreq[word];
            matchedKeywords.push(word);
        }
    });
    const maxSimilarityScore = jobWords.size * 5;
    similarityScore = Math.min((similarityScore / maxSimilarityScore) * 100, 100);

    let atsScore = 0;
    const keywordMatchWeight = 0.6;
    const experienceWeight = 0.3;
    const extraWeight = 0.1;

    const keywordMatchScore = (matchedKeywords.length / jobWords.size) * 100;
    atsScore += keywordMatchScore * keywordMatchWeight;

    const experienceRegex = /(\d+)\s*(years|yrs|year)/gi;
    const jobExperience = (jobDesc.match(experienceRegex) || []).map(match => parseInt(match) || 0);
    const resumeExperience = (resumeText.match(experienceRegex) || []).map(match => parseInt(match) || 0);
    const requiredYears = jobExperience.length ? Math.max(...jobExperience) : 0;
    const candidateYears = resumeExperience.length ? Math.max(...resumeExperience) : 0;
    const experienceScore = requiredYears > 0 ? Math.min((candidateYears / requiredYears) * 100, 100) : 50;
    atsScore += experienceScore * experienceWeight;

    const resumeLengthScore = Math.min((resumeWords.length / 200) * 100, 100);
    atsScore += resumeLengthScore * extraWeight;

    return {
        similarityScore: Math.round(similarityScore),
        atsScore: Math.round(Math.min(atsScore, 100)),
        matchedKeywords,
        experienceYears: candidateYears
    };
}

async function screenResumes() {
    if (!jobDescription.value) {
        alert("⚠️ Please enter a job description.");
        return;
    }

    if (resumeFiles.files.length === 0) {
        alert("⚠️ Please upload at least one resume.");
        return;
    }

    loading.style.display = "block";
    candidateList.innerHTML = "";

    const jobDesc = jobDescription.value;
    const files = Array.from(resumeFiles.files);
    const candidates = [];

    try {
        for (const file of files) {
            const text = await readFileContent(file);
            if (text && text.trim()) {
                const scores = calculateScores(jobDesc, text);
                const feedback = generateFeedback(jobDesc, text, scores);
                candidates.push({ 
                    name: file.name, 
                    similarityScore: scores.similarityScore, 
                    atsScore: scores.atsScore, 
                    matchedKeywords: scores.matchedKeywords, 
                    experienceYears: scores.experienceYears,
                    feedback 
                });
            } else {
                console.warn(`No readable text in ${file.name}`);
            }
        }

        if (candidates.length === 0) {
            candidateList.innerHTML = "<li>No readable resumes found. Please upload .txt or .pdf files.</li>";
            loading.style.display = "none";
            return;
        }

        candidates.sort((a, b) => b.atsScore - a.atsScore || b.similarityScore - a.similarityScore);

        candidates.forEach((candidate, index) => {
            const li = document.createElement("li");
            li.className = "candidate-item";
            li.innerHTML = `
                <span>#${index + 1} <strong>${candidate.name}</strong></span>
                <div>
                    <span class="score">Similarity: ${candidate.similarityScore}%</span>
                    <span class="ats-score">ATS: ${candidate.atsScore}%</span>
                </div>
                <div class="candidate-details">
                    <p><strong>Matched Keywords:</strong> ${candidate.matchedKeywords.length ? candidate.matchedKeywords.join(', ') : 'None'}</p>
                    <p><strong>Experience:</strong> ${candidate.experienceYears} years</p>
                </div>
            `;
            li.addEventListener('click', () => {
                li.classList.toggle('active');
                if (li.classList.contains('active')) {
                    feedbackBox.innerHTML = `
                        <p class="strengths"><strong>Strengths:</strong></p>
                        <ul>${candidate.feedback.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
                        <p class="weaknesses"><strong>Weaknesses:</strong></p>
                        <ul>${candidate.feedback.weaknesses.map(w => `<li>${w}</li>`).join('')}</ul>
                        <p class="suggestions"><strong>Suggestions:</strong></p>
                        <ul>${candidate.feedback.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
                    `;
                    feedbackBox.classList.add('active');
                } else {
                    feedbackBox.classList.remove('active');
                }
            });
            candidateList.appendChild(li);
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.candidate-item') && !e.target.closest('.feedback-box')) {
                feedbackBox.classList.remove('active');
                document.querySelectorAll('.candidate-item').forEach(item => item.classList.remove('active'));
            }
        });
    } catch (error) {
        console.error("Error:", error);
        alert("❌ Error processing resumes. Ensure files are valid .txt or .pdf.");
    } finally {
        loading.style.display = "none";
    }
}