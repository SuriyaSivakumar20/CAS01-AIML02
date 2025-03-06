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
        alert("❌ Error processing resumes. Ensure the backend is running.");
    } finally {
        loading.style.display = "none";
    }
}