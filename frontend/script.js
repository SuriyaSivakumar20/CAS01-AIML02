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

    const formData = new FormData();
    formData.append("jobDescription", jobDescription.value);
    Array.from(resumeFiles.files).forEach(file => {
        formData.append("resumes", file);
    });

    try {
        const response = await fetch("http://localhost:5000/screen", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        if (result.error) {
            candidateList.innerHTML = `<li>${result.error}</li>`;
            loading.style.display = "none";
            return;
        }

        const candidates = result.candidates;
        candidates.forEach((candidate, index) => {
            const li = document.createElement("li");
            li.className = "candidate-item";
            li.innerHTML = `
                <span>#${index + 1} <strong>${candidate.name}</strong></span>
                <div>
                    <span class="score">Similarity: ${candidate.similarityScore}%</span>
                    <span class="ats-score">ATS: ${candidate.atsScore}%</span>
                    <span class="job-fit">Job Fit: ${candidate.jobFit}%</span>
                </div>
                <div class="candidate-details">
                    <p><strong>Matched Keywords:</strong> ${candidate.matchedKeywords.length ? candidate.matchedKeywords.join(', ') : 'None'}</p>
                    <p><strong>Experience:</strong> ${candidate.experienceYears} years</p>
                    <p><strong>Summary:</strong> ${candidate.summary}</p>
                    <p><strong>Tone:</strong> ${candidate.tone}</p>
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
                        <p class="skill-gaps"><strong>Skill Gaps:</strong></p>
                        <ul>${candidate.feedback.skillGaps.map(g => `<li>${g}</li>`).join('')}</ul>
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
        alert("❌ Error processing resumes. Ensure the backend is running.");
    } finally {
        loading.style.display = "none";
    }
}